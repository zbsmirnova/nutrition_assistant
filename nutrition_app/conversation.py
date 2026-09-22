"""Durable single-message work. Network/model calls never hold a transaction."""

from dataclasses import dataclass
from datetime import timedelta
import json
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from pydantic import ValidationError
import sqlalchemy as sa
from sqlalchemy.exc import DBAPIError

from nutrition_contracts.parser import ParserOutput

from . import schema as db
from .errors import ApplicationError, NotFound
from .interpretation import (CONTEXT_VERSION, MAX_CANDIDATES, RESOLVER_VERSION,
                             Parser, ParserRejected, ParserUnavailable, Resolution, parser_request, resolve)
from .service import FoodService, operation_id_for


MAX_ATTEMPTS = 3
TERMINAL = {"applied", "non_logging", "unresolved", "unsupported", "rejected", "failed"}


@dataclass(frozen=True)
class Claim:
    actor: UUID
    origin: UUID
    token: UUID
    context: dict
    prepared: bool


class ConversationWorker:
    def __init__(self, engine, *, lease_seconds=60):
        if type(lease_seconds) is not int or not 1 <= lease_seconds <= 300:
            raise ApplicationError("Worker lease must be between 1 and 300 seconds")
        self.engine = engine
        self.service = FoodService(engine)
        self.lease_seconds = lease_seconds

    @staticmethod
    def _where(actor, origin):
        return sa.and_(db.conversation_jobs.c.user_id == actor, db.conversation_jobs.c.origin_update_id == origin)

    @staticmethod
    def _prepared(connection, actor, origin):
        return connection.execute(sa.select(db.prepared_operations.c.id).where(
            db.prepared_operations.c.user_id == actor,
            db.prepared_operations.c.id == operation_id_for(origin))).scalar_one_or_none() is not None

    @staticmethod
    def _applied(connection, actor, origin):
        return connection.execute(sa.select(db.applied_operations.c.id).where(
            db.applied_operations.c.user_id == actor,
            db.applied_operations.c.id == operation_id_for(origin))).scalar_one_or_none() is not None

    @staticmethod
    def _context(connection, user, source, parser_version):
        versions, products = db.product_versions, db.products
        rows = connection.execute(sa.select(versions).select_from(products.join(versions, sa.and_(
            versions.c.user_id == products.c.user_id, versions.c.product_id == products.c.id,
            versions.c.id == products.c.current_version_id))).where(products.c.user_id == user["id"])
            .order_by(versions.c.name, versions.c.id).limit(MAX_CANDIDATES + 1)).mappings().all()
        context = {"context_version": CONTEXT_VERSION, "resolver_version": RESOLVER_VERSION,
                   "parser_version": parser_version, "schema_version": "1.0", "context_revision": user["context_revision"],
                   "source_text": source["text"], "time_zone": source["source_time_zone"],
                   "local_date": source["source_sent_at"].astimezone(ZoneInfo(source["source_time_zone"])).date().isoformat(),
                   "has_reply": source["reply_to_message_id"] is not None, "forwarded": source["forwarded"],
                   "catalog_overflow": len(rows) > MAX_CANDIDATES, "candidates": []}
        if not context["catalog_overflow"]:
            context["candidates"] = [{"ref": f"c{i}", "version_id": str(row["id"]), "name": row["name"],
                "nutrition_basis": row["nutrition_basis"], "weight_basis": row["weight_basis"],
                "food_kind": row["food_kind"], "declared_fat_percent":
                    None if row["declared_fat_percent"] is None else str(row["declared_fat_percent"])}
                for i, row in enumerate(rows, 1)]
        return context

    def _set(self, connection, actor, origin, status, reason, **values):
        connection.execute(db.conversation_jobs.update().where(self._where(actor, origin)).values(
            status=status, reason=reason, claim_token=None, lease_until=None, next_attempt_at=None,
            pending_food_date=None, **values))

    def _claim(self, actor, parser_version, origin=None):
        if not isinstance(parser_version, str) or not 1 <= len(parser_version) <= 128:
            raise ApplicationError("Parser must supply a bounded version identifier")
        with self.engine.begin() as connection:
            user = self.service._user(connection, actor)
            now = connection.execute(sa.select(sa.func.clock_timestamp())).scalar_one()
            inbox, jobs = db.inbox_updates, db.conversation_jobs
            if origin is None:
                query = sa.select(inbox).select_from(inbox.outerjoin(jobs, sa.and_(
                    jobs.c.user_id == inbox.c.user_id, jobs.c.origin_update_id == inbox.c.id))).where(
                        inbox.c.user_id == actor, sa.or_(jobs.c.id.is_(None), jobs.c.status == "ready",
                        sa.and_(jobs.c.status == "retry", jobs.c.next_attempt_at <= now),
                        sa.and_(jobs.c.status == "processing", jobs.c.lease_until <= now)))
                source = connection.execute(query.order_by(inbox.c.created_at, inbox.c.id).limit(1)).mappings().first()
                if source is None:
                    return {"status": "idle"}
                origin = source["id"]
            else:
                source = connection.execute(sa.select(inbox).where(inbox.c.user_id == actor,
                    inbox.c.id == origin)).mappings().one_or_none()
                if source is None:
                    raise NotFound("Inbox source not found")
            job = connection.execute(sa.select(jobs).where(self._where(actor, origin))).mappings().one_or_none()
            if job is None:
                connection.execute(jobs.insert().values(user_id=actor, origin_update_id=origin,
                                                       status="ready", reason="accepted"))
                job = connection.execute(sa.select(jobs).where(self._where(actor, origin))).mappings().one()
            if self._applied(connection, actor, origin):
                self._set(connection, actor, origin, "applied", "stored_result_recovered")
                return {"status": "applied", "origin_update_id": str(origin)}
            if job["status"] in TERMINAL:
                return {"status": job["status"], "reason": job["reason"], "origin_update_id": str(origin)}
            if job["status"] == "processing" and job["lease_until"] > now:
                return {"status": "busy", "origin_update_id": str(origin)}
            if job["status"] == "retry" and job["next_attempt_at"] > now:
                return {"status": "waiting", "origin_update_id": str(origin)}
            prepared = self._prepared(connection, actor, origin)
            # A frozen command is recoverable without another interpretation, even
            # after the final lease expired following a successful preparation.
            if job["attempts"] >= MAX_ATTEMPTS and not prepared:
                self._set(connection, actor, origin, "failed", "attempt_limit")
                return {"status": "failed", "reason": "attempt_limit", "origin_update_id": str(origin)}
            context = job["context"]
            if context is None and not prepared:
                context = self._context(connection, user, source, parser_version)
            if not prepared and (context["parser_version"] != parser_version or
                    context["resolver_version"] != RESOLVER_VERSION or context["context_version"] != CONTEXT_VERSION):
                self._set(connection, actor, origin, "failed", "interpretation_version_changed")
                return {"status": "failed", "reason": "interpretation_version_changed", "origin_update_id": str(origin)}
            token = uuid4()
            connection.execute(jobs.update().where(self._where(actor, origin)).values(status="processing",
                reason="resuming_command" if prepared else "interpreting", attempts=job["attempts"] + 1,
                context=context, claim_token=token, lease_until=now + timedelta(seconds=self.lease_seconds),
                next_attempt_at=None))
            return Claim(actor, origin, token, context, prepared)

    def _live_claim(self, connection, claim):
        now = connection.execute(sa.select(sa.func.clock_timestamp())).scalar_one()
        return connection.execute(sa.select(db.conversation_jobs).where(self._where(claim.actor, claim.origin),
            db.conversation_jobs.c.status == "processing", db.conversation_jobs.c.claim_token == claim.token,
            db.conversation_jobs.c.lease_until > now)).mappings().one_or_none()

    def _freeze(self, claim, proposal, resolution):
        with self.engine.begin() as connection:
            self.service._user(connection, claim.actor)
            if self._live_claim(connection, claim) is None:
                return False
            if resolution.command is not None:
                self.service._prepare(connection, claim.actor, resolution.command)
            values = {"proposal": proposal}
            # _set normally clears the date; use a separate value assignment below.
            self._set(connection, claim.actor, claim.origin, resolution.status, resolution.reason, **values)
            if resolution.pending_food_date is not None:
                connection.execute(db.conversation_jobs.update().where(self._where(claim.actor, claim.origin))
                                   .values(pending_food_date=resolution.pending_food_date))
        return True

    def _failure(self, claim, reason, *, retryable, require_claim=True, retry_after=None):
        with self.engine.begin() as connection:
            self.service._user(connection, claim.actor)
            if self._applied(connection, claim.actor, claim.origin):
                self._set(connection, claim.actor, claim.origin, "applied", "stored_result_recovered")
                return "applied"
            row = (self._live_claim(connection, claim) if require_claim else connection.execute(
                sa.select(db.conversation_jobs).where(self._where(claim.actor, claim.origin))).mappings().one())
            if row is None:
                return "lost_claim"
            if not require_claim and (row["status"] not in {"ready", "processing"} or
                    (row["status"] == "processing" and row["claim_token"] != claim.token)):
                return "lost_claim"
            status = "retry" if retryable and row["attempts"] < MAX_ATTEMPTS else "failed"
            self._set(connection, claim.actor, claim.origin, status, reason)
            if status == "retry":
                delay = max(2 ** row["attempts"], retry_after or 0)
                connection.execute(db.conversation_jobs.update().where(self._where(claim.actor, claim.origin))
                    .values(next_attempt_at=sa.func.clock_timestamp() + timedelta(seconds=delay)))
            return status

    def run_one(self, actor: UUID, parser: Parser, *, origin: UUID | None = None, fault=None):
        claim = self._claim(actor, parser.version, origin)
        if isinstance(claim, dict):
            return claim

        def point(name):
            if fault:
                fault(name)

        point("after_claim")
        if not claim.prepared:
            context = claim.context
            proposal = None
            if context["has_reply"] or context["forwarded"]:
                resolution = Resolution("unresolved", "conversation_context_required")
            elif context["catalog_overflow"]:
                resolution = Resolution("unsupported", "catalog_context_limit")
            else:
                try:
                    raw = parser.parse(parser_request(context))
                except ParserRejected:
                    status = self._failure(claim, "parser_rejected", retryable=False)
                    return {"status": status, "origin_update_id": str(claim.origin)}
                except ParserUnavailable as exc:
                    status = self._failure(claim, "parser_unavailable", retryable=True, retry_after=exc.retry_after)
                    return {"status": status, "origin_update_id": str(claim.origin)}
                except Exception:
                    # Provider exceptions can contain message text, endpoints, or keys.
                    status = self._failure(claim, "parser_unavailable", retryable=True)
                    return {"status": status, "origin_update_id": str(claim.origin)}
                point("after_parse")
                try:
                    if not isinstance(raw, str) or len(raw.encode("utf-8")) > 256 * 1024:
                        raise ValueError("Invalid proposal size or type")
                    output = ParserOutput.model_validate_json(raw)
                    resolution = resolve(actor, claim.origin, context, output)
                    proposal = output.model_dump(mode="json")
                except (ValidationError, ValueError, TypeError, OverflowError):
                    resolution = Resolution("rejected", "invalid_parser_proposal")
            if not self._freeze(claim, proposal, resolution):
                return {"status": "lost_claim", "origin_update_id": str(claim.origin)}
            point("after_prepare")
            if resolution.command is None:
                return {"status": resolution.status, "reason": resolution.reason,
                        "origin_update_id": str(claim.origin)}
        try:
            outcome = self.service.execute(actor, operation_id_for(claim.origin),
                fault=lambda name: point(name.replace("commit", "domain_commit")))
        except ApplicationError:
            status = self._failure(claim, "command_rejected", retryable=False, require_claim=False)
            return {"status": status, "origin_update_id": str(claim.origin)}
        except DBAPIError:
            status = self._failure(claim, "database_unavailable", retryable=True, require_claim=False)
            return {"status": status, "origin_update_id": str(claim.origin)}
        with self.engine.begin() as connection:
            self.service._user(connection, actor)
            self._set(connection, actor, claim.origin, "applied", "command_applied")
        return {"status": "applied", "origin_update_id": str(claim.origin), "outcome": outcome.model_dump(mode="json")}

    def status(self, actor: UUID, origin: UUID | None = None):
        """Operator diagnostics exclude input, catalog, provider payloads and credentials."""
        with self.engine.begin() as connection:
            self.service._user(connection, actor, read=True)
            inbox, jobs = db.inbox_updates, db.conversation_jobs
            query = sa.select(inbox.c.id, jobs.c.status, jobs.c.reason, jobs.c.attempts, jobs.c.next_attempt_at).select_from(
                inbox.outerjoin(jobs, sa.and_(jobs.c.user_id == inbox.c.user_id, jobs.c.origin_update_id == inbox.c.id))
            ).where(inbox.c.user_id == actor)
            if origin is not None:
                query = query.where(inbox.c.id == origin)
            rows = connection.execute(query.order_by(inbox.c.created_at, inbox.c.id).limit(100)).mappings().all()
            if origin is not None and not rows:
                raise NotFound("Inbox source not found")
            return [{"origin_update_id": str(row["id"]), "status": row["status"] or "received",
                     "reason": row["reason"], "attempts": row["attempts"] or 0,
                     "next_attempt_at": row["next_attempt_at"].isoformat() if row["next_attempt_at"] else None} for row in rows]
