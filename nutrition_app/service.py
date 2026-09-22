"""M1 food services. Actor IDs come from a trusted adapter, never from model text."""

from datetime import date, timezone
from decimal import Decimal
import hashlib
import json
from typing import Callable
from uuid import UUID, uuid4, uuid5

from pydantic import AwareDatetime
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection, Engine

from nutrition_contracts.commands import AddConsumedFood, CommandEnvelope, ProductComponent
from nutrition_contracts.common import Contract, Count, PositiveCount, Text
from nutrition_contracts.results import Applied, DailySummary, FoodEntrySummary, MutationReceipt, OutcomeEnvelope

from .errors import ApplicationError, Conflict, NotFound, Unauthorized, Unsupported
from .nutrition import CALCULATION_VERSION, day_nutrition, entry_nutrition, from_columns, scale, to_columns
from . import schema as db


OPERATION_NAMESPACE = UUID("1d1e3636-b7c8-4e9b-9c13-4ac0b74d039a")


class IncomingMessage(Contract):
    bot_id: PositiveCount
    telegram_update_id: Count
    telegram_message_id: PositiveCount
    private_chat_id: PositiveCount
    telegram_user_id: PositiveCount
    sent_at: AwareDatetime
    text: Text
    reply_to_message_id: PositiveCount | None = None
    forwarded: bool = False


def operation_id_for(update_id: UUID) -> UUID:
    """M1 freezes exactly one command per accepted message (operation position 0)."""
    return uuid5(OPERATION_NAMESPACE, f"{update_id}:0")


def digest(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def decode_outcome(payload: dict) -> OutcomeEnvelope:
    return OutcomeEnvelope.model_validate_json(json.dumps(payload))


class FoodService:
    def __init__(self, engine: Engine):
        self.engine = engine

    @staticmethod
    def _user(connection: Connection, actor: UUID, *, read: bool = False):
        row = connection.execute(sa.select(db.users).where(db.users.c.id == actor)
                                 .with_for_update(read=read)).mappings().one_or_none()
        if row is None:
            raise Unauthorized("Unknown application user")
        return row

    def accept_message(self, actor: UUID, message: IncomingMessage) -> UUID:
        # Revalidate mutable model instances supplied by trusted calling code too.
        message = IncomingMessage.model_validate_json(message.model_dump_json())
        payload = message.model_dump(mode="json")
        payload["sent_at"] = message.sent_at.astimezone(timezone.utc).isoformat()
        # Preserve the hashes of M1 messages that predate transport metadata.
        if message.reply_to_message_id is None:
            payload.pop("reply_to_message_id")
        if not message.forwarded:
            payload.pop("forwarded")
        request_hash = digest(payload)
        with self.engine.begin() as connection:
            user = self._user(connection, actor)
            account = connection.execute(sa.select(db.telegram_accounts).where(
                db.telegram_accounts.c.user_id == actor,
                db.telegram_accounts.c.bot_id == message.bot_id,
                db.telegram_accounts.c.private_chat_id == message.private_chat_id,
                db.telegram_accounts.c.telegram_user_id == message.telegram_user_id,
            )).mappings().one_or_none()
            if account is None:
                raise Unauthorized("Transport account does not belong to the authenticated user")
            existing = connection.execute(sa.select(db.inbox_updates).where(
                db.inbox_updates.c.user_id == actor,
                db.inbox_updates.c.telegram_account_id == account["id"],
                db.inbox_updates.c.telegram_update_id == message.telegram_update_id,
            )).mappings().one_or_none()
            if existing:
                if existing["payload_hash"] != request_hash:
                    raise Conflict("A delivery identity cannot be reused with different message data")
                return existing["id"]
            update_id = uuid4()
            inserted = connection.execute(insert(db.inbox_updates).values(
                id=update_id, user_id=actor, telegram_account_id=account["id"],
                bot_id=message.bot_id,
                telegram_update_id=message.telegram_update_id, telegram_message_id=message.telegram_message_id,
                source_sent_at=message.sent_at, source_time_zone=user["time_zone"], text=message.text,
                payload_hash=request_hash,
                reply_to_message_id=message.reply_to_message_id, forwarded=message.forwarded,
            ).on_conflict_do_nothing(index_elements=["bot_id", "telegram_update_id"]).returning(db.inbox_updates.c.id)).scalar_one_or_none()
            if inserted is None:
                raise Conflict("Delivery identity is unavailable")
        return update_id

    @staticmethod
    def _validate_supported(command: CommandEnvelope) -> None:
        if not isinstance(command.command, AddConsumedFood):
            raise Unsupported("This slice supports resolved add-food commands only")
        if any(not isinstance(c, ProductComponent) for c in command.command.food.components):
            raise Unsupported("This slice supports pinned product components only")
        if command.source.pending_action_id is not None or command.source.evidence_update_ids != [command.source.origin_update_id]:
            raise Unsupported("Clarification workflows are not implemented in this slice")
        if command.operation_id != operation_id_for(command.source.origin_update_id):
            raise ApplicationError("Operation identity must match its original message and position")

    def prepare(self, actor: UUID, command: CommandEnvelope) -> UUID:
        command = CommandEnvelope.model_validate_json(command.model_dump_json())
        if command.user_id != actor:
            raise Unauthorized("Command identity does not match the authenticated user")
        self._validate_supported(command)
        payload = command.model_dump(mode="json")
        request_hash = digest(payload)
        with self.engine.begin() as connection:
            self._user(connection, actor)
            source = connection.execute(sa.select(db.inbox_updates.c.id).where(
                db.inbox_updates.c.user_id == actor, db.inbox_updates.c.id == command.source.origin_update_id,
            )).one_or_none()
            if source is None:
                raise NotFound("Source message not found")
            existing = connection.execute(sa.select(db.prepared_operations).where(
                db.prepared_operations.c.user_id == actor, db.prepared_operations.c.id == command.operation_id,
            )).mappings().one_or_none()
            if existing:
                if existing["request_hash"] != request_hash:
                    raise Conflict("A prepared operation cannot be replaced with different input")
                return existing["id"]
            connection.execute(db.prepared_operations.insert().values(
                id=command.operation_id, user_id=actor, origin_update_id=command.source.origin_update_id,
                position=0, request_hash=request_hash, command=payload,
            ))
        return command.operation_id

    def apply(self, actor: UUID, command: CommandEnvelope, *, fault: Callable[[str], None] | None = None) -> OutcomeEnvelope:
        operation_id = self.prepare(actor, command)
        return self.execute(actor, operation_id, fault=fault)

    def execute(self, actor: UUID, operation_id: UUID, *, fault: Callable[[str], None] | None = None) -> OutcomeEnvelope:
        """Recover a frozen command. The optional fault hook is for local failure tests."""
        with self.engine.begin() as connection:
            self._user(connection, actor)
            prepared = connection.execute(sa.select(db.prepared_operations).where(
                db.prepared_operations.c.user_id == actor, db.prepared_operations.c.id == operation_id,
            )).mappings().one_or_none()
            if prepared is None:
                raise NotFound("Operation not found")
            previous = connection.execute(sa.select(db.applied_operations.c.outcome).where(
                db.applied_operations.c.user_id == actor, db.applied_operations.c.id == operation_id,
            )).scalar_one_or_none()
            if previous is not None:
                return decode_outcome(previous)
            command = CommandEnvelope.model_validate_json(json.dumps(prepared["command"]))
            if command.user_id != actor or command.operation_id != operation_id or digest(prepared["command"]) != prepared["request_hash"]:
                raise Conflict("Prepared operation is inconsistent")
            self._validate_supported(command)
            # M1's explicit additive commands commute: revalidate pinned sources under
            # this user lock. Do not reinterpret date or switch to a newer product.
            result = self._add(connection, actor, command)
            connection.execute(db.applied_operations.insert().values(
                id=operation_id, user_id=actor, outcome=result.model_dump(mode="json")))
            account_id = connection.execute(sa.select(db.inbox_updates.c.telegram_account_id).where(
                db.inbox_updates.c.user_id == actor, db.inbox_updates.c.id == command.source.origin_update_id,
            )).scalar_one()
            connection.execute(db.outbox.insert().values(
                user_id=actor, operation_id=operation_id, telegram_account_id=account_id,
                payload=result.model_dump(mode="json")))
            connection.execute(db.users.update().where(db.users.c.id == actor)
                               .values(context_revision=db.users.c.context_revision + 1))
            if fault:
                fault("before_commit")
        # A failure here intentionally leaves a committed result and pending response.
        if fault:
            fault("after_commit")
        return result

    @staticmethod
    def _component(connection, actor, component):
        version = connection.execute(sa.select(db.product_versions).where(
            db.product_versions.c.user_id == actor, db.product_versions.c.id == component.product_version_id,
        )).mappings().one_or_none()
        if version is None:
            raise NotFound("Product version not found")
        quantity = component.quantity
        compatible = ((quantity.kind == "mass" and version["nutrition_basis"] == "per_100_g") or
                      (quantity.kind == "volume" and version["nutrition_basis"] == "per_100_ml"))
        if not compatible or version["weight_basis"] != quantity.weight_basis:
            raise ApplicationError("Product and quantity bases do not match; an explicit conversion is required")
        amount = Decimal(quantity.edible_g if quantity.kind == "mass" else quantity.ml)
        snapshot = scale(from_columns(version), amount)
        values = dict(description=component.description, product_version_id=version["id"],
            data_source_id=version["data_source_id"], quantity_kind=quantity.kind,
            weight_basis=quantity.weight_basis, calculation_version=CALCULATION_VERSION,
            edible_g=None, gross_g=None, inedible_g=None, volume_ml=None, **to_columns(snapshot))
        if quantity.kind == "mass":
            values.update(edible_g=amount,
                gross_g=None if quantity.gross_g is None else Decimal(quantity.gross_g),
                inedible_g=None if quantity.inedible_g is None else Decimal(quantity.inedible_g))
        else:
            values["volume_ml"] = amount
        return values, snapshot

    def _add(self, connection, actor, command):
        food = command.command.food
        components = [self._component(connection, actor, c) for c in food.components]
        day = connection.execute(sa.select(db.food_days).where(
            db.food_days.c.user_id == actor, db.food_days.c.local_date == food.effective_date,
        )).mappings().one_or_none()
        if day is None:
            day_id = uuid4()
            connection.execute(db.food_days.insert().values(
                id=day_id, user_id=actor, local_date=food.effective_date, time_zone=food.time_zone))
        else:
            day_id = day["id"]
        entry_id, revision_id = uuid4(), uuid4()
        connection.execute(db.food_entries.insert().values(id=entry_id, user_id=actor, current_revision_id=revision_id))
        connection.execute(db.food_entry_revisions.insert().values(
            id=revision_id, user_id=actor, food_entry_id=entry_id, revision_no=1, food_day_id=day_id,
            applied_operation_id=command.operation_id, description=food.description, meal=food.meal,
            time_zone=food.time_zone))
        for position, (values, _) in enumerate(components):
            connection.execute(db.food_components.insert().values(
                user_id=actor, food_entry_revision_id=revision_id, position=position, **values))
        connection.execute(db.food_days.update().where(db.food_days.c.id == day_id, db.food_days.c.user_id == actor)
                           .values(revision=db.food_days.c.revision + 1, explicit_zero_food=False))
        entry = FoodEntrySummary(entry_id=entry_id, revision_id=revision_id, effective_date=food.effective_date,
            description=food.description, nutrition=entry_nutrition([s for _, s in components]), change="added")
        return OutcomeEnvelope(result=Applied(schema_version="1.0", operation_id=command.operation_id,
            outcome="applied", mutations=[MutationReceipt(entity_kind="food_entry", entity_id=entry_id,
                revision_id=revision_id, effective_date=food.effective_date)], food_entries=[entry], observations=[],
            daily_summaries=[self._day(connection, actor, food.effective_date)], recipe=None))

    @staticmethod
    def _current_components(actor):
        return sa.select(db.food_components, db.food_entries.c.id.label("entry_id"),
            db.food_entry_revisions.c.id.label("revision_id"), db.food_days.c.local_date,
            db.food_entry_revisions.c.description.label("entry_description")).select_from(
                db.food_entries.join(db.food_entry_revisions, sa.and_(
                    db.food_entries.c.user_id == db.food_entry_revisions.c.user_id,
                    db.food_entries.c.id == db.food_entry_revisions.c.food_entry_id,
                    db.food_entries.c.current_revision_id == db.food_entry_revisions.c.id))
                .join(db.food_components, sa.and_(db.food_components.c.user_id == db.food_entry_revisions.c.user_id,
                    db.food_components.c.food_entry_revision_id == db.food_entry_revisions.c.id))
                .join(db.food_days, sa.and_(db.food_days.c.user_id == db.food_entry_revisions.c.user_id,
                    db.food_days.c.id == db.food_entry_revisions.c.food_day_id))
            ).where(db.food_entries.c.user_id == actor, db.food_entry_revisions.c.state == "active")

    def _day(self, connection, actor, effective_date):
        day = connection.execute(sa.select(db.food_days).where(
            db.food_days.c.user_id == actor, db.food_days.c.local_date == effective_date,
        )).mappings().one_or_none()
        rows = connection.execute(self._current_components(actor).where(db.food_days.c.local_date == effective_date)).mappings().all()
        return DailySummary(effective_date=effective_date,
            completeness="unconfirmed" if day is None else day["completeness"],
            explicit_zero_food=False if day is None else day["explicit_zero_food"], pending_food_actions=0,
            entry_count=len({row["entry_id"] for row in rows}), component_count=len(rows),
            nutrition=day_nutrition([from_columns(row) for row in rows]))

    def get_day(self, actor: UUID, effective_date: date) -> DailySummary:
        with self.engine.begin() as connection:
            self._user(connection, actor, read=True)
            return self._day(connection, actor, effective_date)

    def get_entry(self, actor: UUID, entry_id: UUID) -> FoodEntrySummary:
        with self.engine.begin() as connection:
            self._user(connection, actor, read=True)
            rows = connection.execute(self._current_components(actor).where(db.food_entries.c.id == entry_id)).mappings().all()
            if not rows:
                raise NotFound("Food entry not found")
            return FoodEntrySummary(entry_id=entry_id, revision_id=rows[0]["revision_id"],
                effective_date=rows[0]["local_date"], description=rows[0]["entry_description"],
                nutrition=entry_nutrition([from_columns(row) for row in rows]), change="added")
