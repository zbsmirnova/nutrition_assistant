"""Durable single-message work. Network/model calls never hold a transaction."""

from dataclasses import dataclass
from datetime import date, timedelta
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
                             Parser, ParserRejected, ParserUnavailable, Resolution, parser_request,
                             resolve, resolve_actions)
from .service import FoodService, operation_id_for


MAX_ATTEMPTS = 3
TERMINAL = {"applied", "non_logging", "unresolved", "unsupported", "rejected", "failed"}


@dataclass(frozen=True)
class Claim:
    actor: UUID
    origin: UUID
    token: UUID
    operation_id: UUID
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
    def _clarification(context, reason, pending_questions):
        if reason == "recipe_target_ambiguous":
            records = {record["ref"]: record for record in context.get("recipe_records", ())}
            choices = []
            for number, recipe in enumerate((item for item in context.get("recipes", ())
                                              if item["ref"] in pending_questions), 1):
                record = records.get(recipe["ref"], {})
                kcal = record.get("kcal")
                suffix = "" if kcal is None else f" — {kcal} ккал/100 г"
                choices.append(f"{number}. {recipe['name']}{suffix}")
            if choices:
                return "Какой сохранённый рецепт записать?\n" + "\n".join(choices) + \
                    "\nОтветьте номером или напишите более точное название рецепта."
        if reason in {"quantity_unresolved", "quantity_not_exact", "weight_basis_unresolved"}:
            ref = next(iter(pending_questions), None)
            recipe = next((item for item in context.get("recipes", ()) if item["ref"] == ref), None)
            if recipe is not None:
                name = f"рецепта «{recipe['name']}»"
            else:
                candidate = next((item for item in context.get("candidates", ()) if item["ref"] == ref), None)
                name = "этого продукта" if candidate is None else f"«{candidate['name']}»"
            if reason == "weight_basis_unresolved":
                return (f"Уточните съедобный вес {name} без костей и кожи или напишите, какую оценку "
                        "использовать. Пока не включаю приблизительный вес в итог.")
            return (f"Укажите точный вес {name} в граммах или подтвердите оценку. "
                    "Приблизительный вес пока не включаю в итог.")
        return None

    @staticmethod
    def _where(actor, origin):
        return sa.and_(db.conversation_jobs.c.user_id == actor, db.conversation_jobs.c.origin_update_id == origin)

    @staticmethod
    def _prepared(connection, actor, operation_id):
        return connection.execute(sa.select(db.prepared_operations.c.id).where(
            db.prepared_operations.c.user_id == actor,
            db.prepared_operations.c.id == operation_id)).scalar_one_or_none() is not None

    @staticmethod
    def _applied(connection, actor, operation_id):
        return connection.execute(sa.select(db.applied_operations.c.id).where(
            db.applied_operations.c.user_id == actor,
            db.applied_operations.c.id == operation_id)).scalar_one_or_none() is not None

    @staticmethod
    def _context(connection, user, source, parser_version):
        versions, products = db.product_versions, db.products
        rows = connection.execute(sa.select(versions).select_from(products.join(versions, sa.and_(
            versions.c.user_id == products.c.user_id, versions.c.product_id == products.c.id,
            versions.c.id == products.c.current_version_id))).where(products.c.user_id == user["id"])
            .order_by(versions.c.name, versions.c.id).limit(MAX_CANDIDATES + 1)).mappings().all()
        recipe_rows = connection.execute(sa.select(
            db.recipe_versions.c.id.label("version_id"),
            db.recipe_versions.c.recipe_id,
            db.recipe_versions.c.name,
            db.recipe_versions.c.kcal,
        ).select_from(db.recipes.join(db.recipe_versions, sa.and_(
            db.recipes.c.user_id == db.recipe_versions.c.user_id,
            db.recipes.c.current_version_id == db.recipe_versions.c.id,
        ))).where(db.recipes.c.user_id == user["id"])
            .order_by(db.recipe_versions.c.name, db.recipe_versions.c.id).limit(MAX_CANDIDATES + 1)).mappings().all()
        catalog_overflow = len(rows) > MAX_CANDIDATES or len(rows) + len(recipe_rows) > MAX_CANDIDATES
        context = {"context_version": CONTEXT_VERSION, "resolver_version": RESOLVER_VERSION,
                   "parser_version": parser_version, "schema_version": "1.0", "context_revision": user["context_revision"],
                   "source_text": source["text"], "time_zone": source["source_time_zone"],
                   "local_date": source["source_sent_at"].astimezone(ZoneInfo(source["source_time_zone"])).date().isoformat(),
                   "has_reply": source["reply_to_message_id"] is not None, "forwarded": source["forwarded"],
                   "catalog_overflow": catalog_overflow, "candidates": [], "recipes": [],
                   "recipe_records": [],
                   "pending_candidates": [], "pending_recipes": [], "pending_entries": [],
                   "pending_questions": {}, "pending": None, "pending_reason": None,
                   "observations": [],
                   "entries": [], "reply_entry_ref": None}
        observation_rows = connection.execute(sa.select(
            db.observations.c.metric, db.observations.c.series_date,
            db.observations.c.current_revision_id.label("revision_id")
        ).where(db.observations.c.user_id == user["id"],
                db.observations.c.series_date == date.fromisoformat(context["local_date"]))).mappings().all()
        context["observations"] = [{"metric": row["metric"], "series_date": row["series_date"].isoformat(),
                                     "revision_id": str(row["revision_id"])} for row in observation_rows]
        if not context["catalog_overflow"]:
            context["candidates"] = [{"ref": f"c{i}", "version_id": str(row["id"]), "name": row["name"],
                "nutrition_basis": row["nutrition_basis"], "weight_basis": row["weight_basis"],
                "food_kind": row["food_kind"], "declared_fat_percent":
                    None if row["declared_fat_percent"] is None else str(row["declared_fat_percent"])}
                for i, row in enumerate(rows, 1)]
            recipe_start = len(context["candidates"]) + 1
            context["recipes"] = [{"ref": f"c{i}", "name": row["name"]}
                                   for i, row in enumerate(recipe_rows, recipe_start)]
            context["recipe_records"] = [{"ref": f"c{i}", "recipe_id": str(row["recipe_id"]),
                                           "version_id": str(row["version_id"]), "name": row["name"],
                                           "kcal": None if row["kcal"] is None else str(row["kcal"])}
                                          for i, row in enumerate(recipe_rows, recipe_start)]
        entry_rows = connection.execute(sa.select(
            db.food_entries.c.id.label("entry_id"),
            db.food_entry_revisions.c.id.label("revision_id"),
            db.food_entry_revisions.c.revision_no,
            db.food_entry_revisions.c.food_day_id,
            db.food_entry_revisions.c.description,
            db.food_entry_revisions.c.meal,
            db.food_entry_revisions.c.time_zone,
            db.food_entry_revisions.c.state,
            db.food_days.c.local_date.label("effective_date"),
            db.food_components.c.position.label("component_position"),
            db.food_components.c.description.label("component_description"),
            db.food_components.c.component_kind,
            db.food_components.c.product_version_id,
            db.food_components.c.recipe_version_id,
            db.food_components.c.quantity_kind,
            db.food_components.c.edible_g,
            db.food_components.c.gross_g,
            db.food_components.c.inedible_g,
            db.food_components.c.volume_ml,
            db.food_components.c.weight_basis,
        ).select_from(
            db.food_entries.join(db.food_entry_revisions, sa.and_(
                db.food_entries.c.user_id == db.food_entry_revisions.c.user_id,
                db.food_entries.c.id == db.food_entry_revisions.c.food_entry_id,
                db.food_entries.c.current_revision_id == db.food_entry_revisions.c.id))
            .join(db.food_days, sa.and_(
                db.food_entry_revisions.c.user_id == db.food_days.c.user_id,
                db.food_entry_revisions.c.food_day_id == db.food_days.c.id))
            .outerjoin(db.food_components, sa.and_(
                db.food_entry_revisions.c.user_id == db.food_components.c.user_id,
                db.food_entry_revisions.c.id == db.food_components.c.food_entry_revision_id))
        ).where(db.food_entries.c.user_id == user["id"])
         .order_by(db.food_days.c.local_date.desc(), db.food_entry_revisions.c.created_at.desc(),
                   db.food_entries.c.id, db.food_components.c.position)).mappings().all()
        entry_map = {}
        for row in entry_rows:
            key = row["entry_id"]
            record = entry_map.setdefault(key, {"entry_id": str(key), "revision_id": str(row["revision_id"]),
                "state": row["state"], "description": row["description"], "meal": row["meal"],
                "effective_date": row["effective_date"].isoformat(), "time_zone": row["time_zone"],
                "components": [], "food": None, "undo_revision_id": None})
            if row["component_position"] is not None:
                if row["quantity_kind"] == "mass":
                    quantity = {"kind": "mass", "edible_g": str(row["edible_g"]),
                                "gross_g": None if row["gross_g"] is None else str(row["gross_g"]),
                                "inedible_g": None if row["inedible_g"] is None else str(row["inedible_g"]),
                                "weight_basis": row["weight_basis"]}
                else:
                    quantity = {"kind": "volume", "ml": str(row["volume_ml"]),
                                "weight_basis": row["weight_basis"]}
                if row["component_kind"] == "recipe":
                    record["components"].append({"kind": "recipe", "description": row["component_description"],
                        "recipe_version_id": str(row["recipe_version_id"]), "eaten_grams": str(row["edible_g"])})
                else:
                    record["components"].append({"kind": "product", "description": row["component_description"],
                        "product_version_id": str(row["product_version_id"]), "quantity": quantity})
        for record in entry_map.values():
            previous = connection.execute(sa.select(db.food_entry_revisions.c.id).where(
                db.food_entry_revisions.c.user_id == user["id"],
                db.food_entry_revisions.c.food_entry_id == UUID(record["entry_id"]),
                db.food_entry_revisions.c.state == "active",
                db.food_entry_revisions.c.revision_no < sa.select(db.food_entry_revisions.c.revision_no).where(
                    db.food_entry_revisions.c.user_id == user["id"],
                    db.food_entry_revisions.c.id == UUID(record["revision_id"])).scalar_subquery(),
            ).order_by(db.food_entry_revisions.c.revision_no.desc()).limit(1)).scalar_one_or_none()
            record["undo_revision_id"] = None if previous is None else str(previous)
            record["food"] = {"effective_date": record["effective_date"], "time_zone": record["time_zone"],
                               "meal": record["meal"], "description": record["description"],
                               "components": record["components"]}
        entry_records = list(entry_map.values())
        for index, record in enumerate(entry_records, len(rows) + len(recipe_rows) + 1):
            record["ref"] = f"c{index}"
            context["entries"].append({"ref": record["ref"], "description": record["description"],
                                        "effective_date": record["effective_date"], "meal": record["meal"],
                                        "state": record["state"]})
        context["entry_records"] = entry_records
        if source["reply_to_message_id"] is not None:
            replied_entry = connection.execute(sa.select(db.food_entries.c.id).select_from(
                db.food_entries.join(db.food_entry_revisions, sa.and_(
                    db.food_entries.c.user_id == db.food_entry_revisions.c.user_id,
                    db.food_entries.c.id == db.food_entry_revisions.c.food_entry_id))
                .join(db.applied_operations, sa.and_(
                    db.food_entry_revisions.c.user_id == db.applied_operations.c.user_id,
                    db.food_entry_revisions.c.applied_operation_id == db.applied_operations.c.id))
                .join(db.prepared_operations, sa.and_(
                    db.applied_operations.c.user_id == db.prepared_operations.c.user_id,
                    db.applied_operations.c.id == db.prepared_operations.c.id))
                .join(db.inbox_updates, sa.and_(
                    db.prepared_operations.c.user_id == db.inbox_updates.c.user_id,
                    db.prepared_operations.c.origin_update_id == db.inbox_updates.c.id))
            ).where(db.food_entries.c.user_id == user["id"],
                    db.inbox_updates.c.telegram_account_id == source["telegram_account_id"],
                    db.inbox_updates.c.telegram_message_id == source["reply_to_message_id"])).scalar_one_or_none()
            for record in entry_records:
                if record["entry_id"] == (None if replied_entry is None else str(replied_entry)):
                    context["reply_entry_ref"] = record["ref"]
                    break
        if source["reply_to_message_id"] is not None:
            original = db.inbox_updates.alias("original_inbox")
            pending = connection.execute(sa.select(db.conversation_jobs).select_from(
                db.conversation_jobs.join(original, sa.and_(
                    original.c.user_id == db.conversation_jobs.c.user_id,
                    original.c.id == db.conversation_jobs.c.origin_update_id))).where(
                db.conversation_jobs.c.user_id == user["id"],
                db.conversation_jobs.c.status == "unresolved",
                db.conversation_jobs.c.pending_questions.is_not(None),
                original.c.telegram_account_id == source["telegram_account_id"],
                original.c.telegram_message_id == source["reply_to_message_id"]
            ).order_by(original.c.created_at, original.c.id).limit(1)).mappings().first()
            if pending is not None:
                original_context = pending["context"]
                pending_questions = pending["pending_questions"]
                refs = set(pending_questions)
                context["pending_questions"] = pending_questions
                context["pending_reason"] = pending["reason"]
                context["pending_candidates"] = [candidate for candidate in original_context["candidates"]
                                                   if candidate["ref"] in refs]
                context["pending_recipes"] = [recipe for recipe in original_context.get("recipes", ())
                                               if recipe["ref"] in refs]
                context["pending_entries"] = [entry for entry in original_context.get("entries", ())
                                               if entry["ref"] in refs]
                context["pending"] = {
                    "job_id": str(pending["id"]),
                    "origin_update_id": str(pending["origin_update_id"]),
                    "proposal": pending["proposal"],
                    "context": original_context,
                    "position": original_context.get("pending_position", 0),
                }
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
            if job["status"] in TERMINAL:
                return {"status": job["status"], "reason": job["reason"], "origin_update_id": str(origin)}
            if job["status"] == "processing" and job["lease_until"] > now:
                return {"status": "busy", "origin_update_id": str(origin)}
            if job["status"] == "retry" and job["next_attempt_at"] > now:
                return {"status": "waiting", "origin_update_id": str(origin)}
            context = job["context"]
            if context is None:
                context = self._context(connection, user, source, parser_version)
            execution_origin = UUID(context["pending"]["origin_update_id"]) if context.get("pending") else origin
            execution_position = context["pending"].get("position", 0) if context.get("pending") else 0
            execution_operation_id = operation_id_for(execution_origin, execution_position)
            if self._applied(connection, actor, execution_operation_id):
                self._set(connection, actor, origin, "applied", "stored_result_recovered")
                if context.get("pending"):
                    self._clear_pending(connection, Claim(actor, origin, uuid4(), execution_operation_id, context, True))
                return {"status": "applied", "origin_update_id": str(origin)}
            prepared = self._prepared(connection, actor, execution_operation_id)
            # A frozen command is recoverable without another interpretation, even
            # after the final lease expired following a successful preparation.
            if job["attempts"] >= MAX_ATTEMPTS and not prepared:
                self._set(connection, actor, origin, "failed", "attempt_limit")
                return {"status": "failed", "reason": "attempt_limit", "origin_update_id": str(origin)}
            if not prepared and (context["parser_version"] != parser_version or
                    context["resolver_version"] != RESOLVER_VERSION or context["context_version"] != CONTEXT_VERSION):
                self._set(connection, actor, origin, "failed", "interpretation_version_changed")
                return {"status": "failed", "reason": "interpretation_version_changed", "origin_update_id": str(origin)}
            token = uuid4()
            connection.execute(jobs.update().where(self._where(actor, origin)).values(status="processing",
                reason="resuming_command" if prepared else "interpreting", attempts=job["attempts"] + 1,
                context=context, claim_token=token, lease_until=now + timedelta(seconds=self.lease_seconds),
                next_attempt_at=None))
            return Claim(actor, origin, token, execution_operation_id, context, prepared)

    def _live_claim(self, connection, claim):
        now = connection.execute(sa.select(sa.func.clock_timestamp())).scalar_one()
        return connection.execute(sa.select(db.conversation_jobs).where(self._where(claim.actor, claim.origin),
            db.conversation_jobs.c.status == "processing", db.conversation_jobs.c.claim_token == claim.token,
            db.conversation_jobs.c.lease_until > now)).mappings().one_or_none()

    @staticmethod
    def _clear_pending(connection, claim):
        pending = claim.context.get("pending")
        if pending is None:
            return
        connection.execute(db.conversation_jobs.update().where(
            db.conversation_jobs.c.user_id == claim.actor,
            db.conversation_jobs.c.origin_update_id == UUID(pending["origin_update_id"]),
            db.conversation_jobs.c.status == "unresolved",
        ).values(status="applied", reason="clarification_resolved", pending_food_date=None,
                 pending_questions=None, claim_token=None, lease_until=None, next_attempt_at=None))

    def _freeze(self, claim, proposal, resolution):
        with self.engine.begin() as connection:
            self.service._user(connection, claim.actor)
            if self._live_claim(connection, claim) is None:
                return False
            if resolution.command is not None:
                position = resolution.command_position
                if position is None:
                    position = claim.context.get("operation_position", 0)
                    if claim.context.get("pending"):
                        position = claim.context["pending"].get("position", 0)
                self.service._prepare(connection, claim.actor, resolution.command, position=position)
            if resolution.pending_questions:
                claim.context["pending_questions"] = resolution.pending_questions
                claim.context["pending_reason"] = resolution.reason
                claim.context["pending_position"] = resolution.pending_position or 0
                claim.context["pending_food_date"] = (None if resolution.pending_food_date is None
                                                        else resolution.pending_food_date.isoformat())
            values = {"proposal": proposal,
                      "pending_questions": resolution.pending_questions,
                      "context": claim.context}
            # _set normally clears the date; use a separate value assignment below.
            self._set(connection, claim.actor, claim.origin, resolution.status, resolution.reason, **values)
            if resolution.pending_food_date is not None:
                connection.execute(db.conversation_jobs.update().where(self._where(claim.actor, claim.origin))
                                   .values(pending_food_date=resolution.pending_food_date))
        return True

    def _failure(self, claim, reason, *, retryable, require_claim=True, retry_after=None):
        with self.engine.begin() as connection:
            self.service._user(connection, claim.actor)
            if self._applied(connection, claim.actor, claim.operation_id):
                self._set(connection, claim.actor, claim.origin, "applied", "stored_result_recovered")
                self._clear_pending(connection, claim)
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
            if (context["forwarded"] or
                    (context["has_reply"] and context.get("reply_entry_ref") is None)) and context.get("pending") is None:
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
                    if len(output.actions) == 1:
                        resolution = resolve(actor, claim.origin, context, output)
                    else:
                        resolved = resolve_actions(actor, claim.origin, context, output)
                        ready = [(index, item) for index, item in enumerate(resolved)
                                 if item.command is not None and item.status == "ready"]
                        waiting = [(index, item) for index, item in enumerate(resolved)
                                   if item.status == "unresolved" and item.pending_questions]
                        if len(ready) == 1 and len(waiting) == 1 and len(resolved) == 2:
                            ready_index, ready_resolution = ready[0]
                            pending_index, pending_resolution = waiting[0]
                            resolution = Resolution(
                                "ready", "partial_command_prepared", command=ready_resolution.command,
                                pending_food_date=pending_resolution.pending_food_date,
                                pending_questions=pending_resolution.pending_questions,
                                pending_position=pending_index, command_position=ready_index)
                        else:
                            resolution = Resolution("unsupported", "multiple_actions")
                    proposal = output.model_dump(mode="json")
                except (ValidationError, ValueError, TypeError, OverflowError):
                    resolution = Resolution("rejected", "invalid_parser_proposal")
            if not self._freeze(claim, proposal, resolution):
                return {"status": "lost_claim", "origin_update_id": str(claim.origin)}
            point("after_prepare")
            if resolution.command is None:
                result = {"status": resolution.status, "reason": resolution.reason,
                          "origin_update_id": str(claim.origin)}
                if resolution.pending_questions:
                    clarification = self._clarification(claim.context, resolution.reason,
                                                         resolution.pending_questions)
                    if clarification is not None:
                        result["clarification"] = clarification
                return result
        try:
            outcome = self.service.execute(actor, claim.operation_id,
                fault=lambda name: point(name.replace("commit", "domain_commit")))
        except ApplicationError:
            status = self._failure(claim, "command_rejected", retryable=False, require_claim=False)
            return {"status": status, "origin_update_id": str(claim.origin)}
        except DBAPIError:
            status = self._failure(claim, "database_unavailable", retryable=True, require_claim=False)
            return {"status": status, "origin_update_id": str(claim.origin)}
        with self.engine.begin() as connection:
            self.service._user(connection, actor)
            if claim.context.get("pending_questions") and claim.context.get("pending") is None:
                pending_date = claim.context.get("pending_food_date")
                self._set(connection, actor, claim.origin, "unresolved", "partial_applied",
                          pending_questions=claim.context["pending_questions"])
                if pending_date is not None:
                    connection.execute(db.conversation_jobs.update().where(self._where(actor, claim.origin))
                                       .values(pending_food_date=date.fromisoformat(pending_date)))
            else:
                self._set(connection, actor, claim.origin, "applied", "command_applied")
                self._clear_pending(connection, claim)
        result = {"status": "applied", "origin_update_id": str(claim.origin),
                  "outcome": outcome.model_dump(mode="json")}
        if claim.context.get("pending_questions") and claim.context.get("pending") is None:
            clarification = self._clarification(claim.context, claim.context.get("pending_reason"),
                                                 claim.context["pending_questions"])
            if clarification is not None:
                result["clarification"] = clarification
        return result

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
