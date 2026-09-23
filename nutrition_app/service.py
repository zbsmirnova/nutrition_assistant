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

from nutrition_contracts.commands import (
    AddConsumedFood, CalculatedRecipeNutrition, CommandEnvelope, CorrectFoodEntry, DefineRecipe,
    DeleteFoodEntry, ProductComponent, RecipeDefinition, ReviseRecipe, RestoreFoodEntry,
    ResolvedIngredientSource, UnknownIngredientSource,
)
from nutrition_contracts.common import Contract, Count, NutritionSnapshot, PositiveCount, Text
from nutrition_contracts.results import Applied, DailySummary, FoodEntrySummary, MutationReceipt, OutcomeEnvelope, RecipeProfile

from .errors import ApplicationError, Conflict, NotFound, Unauthorized, Unsupported
from .nutrition import (CALCULATION_VERSION, RECIPE_CALCULATION_VERSION, day_nutrition, entry_nutrition,
                        from_columns, recipe_per_100_g, scale, to_columns)
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


def operation_id_for(update_id: UUID, position: int = 0) -> UUID:
    """Derive a stable command identity from an inbox update and action position."""
    if type(position) is not int or not 0 <= position < 32:
        raise ApplicationError("Operation position must be between 0 and 31")
    return uuid5(OPERATION_NAMESPACE, f"{update_id}:{position}")


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
    def _validate_supported(command: CommandEnvelope, position: int = 0) -> None:
        if not isinstance(command.command, (AddConsumedFood, CorrectFoodEntry, DeleteFoodEntry, RestoreFoodEntry,
                                            DefineRecipe, ReviseRecipe)):
            raise Unsupported("This slice supports resolved food and recipe definition commands only")
        evidence = command.source.evidence_update_ids
        if evidence[0] != command.source.origin_update_id or len(set(evidence)) != len(evidence):
            raise ApplicationError("Evidence must begin with the original source and contain no duplicates")
        if isinstance(command.command, AddConsumedFood):
            if any(not isinstance(c, ProductComponent) for c in command.command.food.components):
                raise Unsupported("This slice supports pinned product components only")
            if command.source.pending_action_id is None and evidence != [command.source.origin_update_id]:
                raise Unsupported("Additional evidence requires a pending clarification")
            if command.source.pending_action_id is not None and len(evidence) < 2:
                raise Unsupported("A clarification command requires answer evidence")
        elif isinstance(command.command, CorrectFoodEntry) and any(
                not isinstance(c, ProductComponent) for c in command.command.replacement.components):
            raise Unsupported("This slice supports pinned product components only")
        elif isinstance(command.command, (DefineRecipe, ReviseRecipe)):
            if command.source.pending_action_id is not None or evidence != [command.source.origin_update_id]:
                raise Unsupported("Recipe persistence does not depend on pending clarification in this slice")
        elif command.source.pending_action_id is None and evidence != [command.source.origin_update_id]:
            raise Unsupported("Additional correction evidence requires a pending clarification")
        elif command.source.pending_action_id is not None and len(evidence) < 2:
            raise Unsupported("A clarification command requires answer evidence")
        if command.operation_id != operation_id_for(command.source.origin_update_id, position):
            raise ApplicationError("Operation identity must match its original message and position")

    def prepare(self, actor: UUID, command: CommandEnvelope, *, position: int = 0) -> UUID:
        with self.engine.begin() as connection:
            self._user(connection, actor)
            return self._prepare(connection, actor, command, position=position)

    def _prepare(self, connection: Connection, actor: UUID, command: CommandEnvelope, *, position: int = 0) -> UUID:
        """Freeze under an existing short user-locked transaction (also used by W003)."""
        command = CommandEnvelope.model_validate_json(command.model_dump_json())
        if command.user_id != actor:
            raise Unauthorized("Command identity does not match the authenticated user")
        self._validate_supported(command, position)
        payload = command.model_dump(mode="json")
        request_hash = digest(payload)
        source = connection.execute(sa.select(db.inbox_updates.c.id).where(
            db.inbox_updates.c.user_id == actor, db.inbox_updates.c.id == command.source.origin_update_id,
        )).one_or_none()
        if source is None:
            raise NotFound("Source message not found")
        if command.source.pending_action_id is not None:
            pending = connection.execute(sa.select(db.conversation_jobs.c.id).where(
                db.conversation_jobs.c.user_id == actor,
                db.conversation_jobs.c.id == command.source.pending_action_id,
                db.conversation_jobs.c.origin_update_id == command.source.origin_update_id,
                db.conversation_jobs.c.status == "unresolved",
                db.conversation_jobs.c.pending_questions.is_not(None),
            )).scalar_one_or_none()
            if pending is None:
                raise Conflict("Pending clarification is missing or already resolved")
            evidence_rows = connection.execute(sa.select(sa.func.count()).select_from(db.inbox_updates).where(
                db.inbox_updates.c.user_id == actor,
                db.inbox_updates.c.id.in_(command.source.evidence_update_ids))).scalar_one()
            if evidence_rows != len(command.source.evidence_update_ids):
                raise NotFound("Clarification evidence source not found")
        existing = connection.execute(sa.select(db.prepared_operations).where(
            db.prepared_operations.c.user_id == actor, db.prepared_operations.c.id == command.operation_id,
        )).mappings().one_or_none()
        if existing:
            if existing["request_hash"] != request_hash:
                raise Conflict("A prepared operation cannot be replaced with different input")
            return existing["id"]
        connection.execute(db.prepared_operations.insert().values(
            id=command.operation_id, user_id=actor, origin_update_id=command.source.origin_update_id,
            position=position, request_hash=request_hash, command=payload,
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
            self._validate_supported(command, prepared["position"])
            # M1's explicit additive commands commute: revalidate pinned sources under
            # this user lock. Do not reinterpret date or switch to a newer product.
            result = self._mutate(connection, actor, command)
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
    def _current_entry(connection, actor, entry_id, *, lock=False):
        query = sa.select(
            db.food_entries.c.id.label("entry_id"),
            db.food_entries.c.current_revision_id,
            db.food_entry_revisions.c.id.label("revision_id"),
            db.food_entry_revisions.c.revision_no,
            db.food_entry_revisions.c.food_day_id,
            db.food_entry_revisions.c.description,
            db.food_entry_revisions.c.meal,
            db.food_entry_revisions.c.time_zone,
            db.food_entry_revisions.c.state,
            db.food_days.c.local_date.label("effective_date"),
        ).select_from(
            db.food_entries.join(db.food_entry_revisions, sa.and_(
                db.food_entries.c.user_id == db.food_entry_revisions.c.user_id,
                db.food_entries.c.id == db.food_entry_revisions.c.food_entry_id,
                db.food_entries.c.current_revision_id == db.food_entry_revisions.c.id))
            .join(db.food_days, sa.and_(
                db.food_entry_revisions.c.user_id == db.food_days.c.user_id,
                db.food_entry_revisions.c.food_day_id == db.food_days.c.id))
        ).where(db.food_entries.c.user_id == actor, db.food_entries.c.id == entry_id)
        if lock:
            query = query.with_for_update()
        return connection.execute(query).mappings().one_or_none()

    @staticmethod
    def _ensure_day(connection, actor, effective_date, time_zone):
        day = connection.execute(sa.select(db.food_days).where(
            db.food_days.c.user_id == actor, db.food_days.c.local_date == effective_date,
        )).mappings().one_or_none()
        if day is not None:
            return day["id"]
        day_id = uuid4()
        connection.execute(db.food_days.insert().values(
            id=day_id, user_id=actor, local_date=effective_date, time_zone=time_zone))
        return day_id

    @staticmethod
    def _touch_days(connection, actor, day_ids):
        for day_id in dict.fromkeys(day_ids):
            connection.execute(db.food_days.update().where(
                db.food_days.c.user_id == actor, db.food_days.c.id == day_id
            ).values(revision=db.food_days.c.revision + 1, explicit_zero_food=False))

    @staticmethod
    def _copy_components(connection, actor, source_revision_id, target_revision_id):
        rows = connection.execute(sa.select(db.food_components).where(
            db.food_components.c.user_id == actor,
            db.food_components.c.food_entry_revision_id == source_revision_id,
        ).order_by(db.food_components.c.position)).mappings().all()
        for row in rows:
            values = dict(row)
            values.pop("id", None)
            values.pop("created_at", None)
            values["food_entry_revision_id"] = target_revision_id
            connection.execute(db.food_components.insert().values(**values))
        return rows

    def _changed_entry_result(self, connection, actor, command, *, entry_id, revision_id,
                              effective_date, description, change, nutrition, day_dates):
        entry = FoodEntrySummary(entry_id=entry_id, revision_id=revision_id,
            effective_date=effective_date, description=description, nutrition=nutrition, change=change)
        return OutcomeEnvelope(result=Applied(schema_version="1.0", operation_id=command.operation_id,
            outcome="applied", mutations=[MutationReceipt(entity_kind="food_entry", entity_id=entry_id,
                revision_id=revision_id, effective_date=effective_date)], food_entries=[entry], observations=[],
            daily_summaries=[self._day(connection, actor, day) for day in sorted(set(day_dates))], recipe=None))

    def _check_current_revision(self, connection, actor, command, *, allow_deleted=False):
        current = self._current_entry(connection, actor, command.entry_id, lock=True)
        if current is None:
            raise NotFound("Food entry not found")
        if current["revision_id"] != command.expected_revision_id:
            raise Conflict("Food entry revision has changed")
        if not allow_deleted and current["state"] != "active":
            raise Conflict("Food entry is deleted")
        return current

    def _correct(self, connection, actor, envelope):
        command: CorrectFoodEntry = envelope.command
        current = self._check_current_revision(connection, actor, command)
        food = command.replacement
        components = [self._component(connection, actor, component) for component in food.components]
        day_id = self._ensure_day(connection, actor, food.effective_date, food.time_zone)
        revision_id = uuid4()
        connection.execute(db.food_entry_revisions.insert().values(
            id=revision_id, user_id=actor, food_entry_id=command.entry_id,
            revision_no=current["revision_no"] + 1, food_day_id=day_id,
            applied_operation_id=envelope.operation_id, description=food.description,
            meal=food.meal, time_zone=food.time_zone, state="active"))
        snapshots = []
        for position, (values, snapshot) in enumerate(components):
            connection.execute(db.food_components.insert().values(
                user_id=actor, food_entry_revision_id=revision_id, position=position, **values))
            snapshots.append(snapshot)
        connection.execute(db.food_entries.update().where(
            db.food_entries.c.user_id == actor, db.food_entries.c.id == command.entry_id
        ).values(current_revision_id=revision_id))
        self._touch_days(connection, actor, [current["food_day_id"], day_id])
        return self._changed_entry_result(connection, actor, envelope, entry_id=command.entry_id,
            revision_id=revision_id, effective_date=food.effective_date, description=food.description,
            change="corrected", nutrition=entry_nutrition(snapshots),
            day_dates=[current["effective_date"], food.effective_date])

    def _delete(self, connection, actor, envelope):
        command: DeleteFoodEntry = envelope.command
        current = self._check_current_revision(connection, actor, command)
        revision_id = uuid4()
        connection.execute(db.food_entry_revisions.insert().values(
            id=revision_id, user_id=actor, food_entry_id=command.entry_id,
            revision_no=current["revision_no"] + 1, food_day_id=current["food_day_id"],
            applied_operation_id=envelope.operation_id, description=current["description"],
            meal=current["meal"], time_zone=current["time_zone"], state="deleted"))
        connection.execute(db.food_entries.update().where(
            db.food_entries.c.user_id == actor, db.food_entries.c.id == command.entry_id
        ).values(current_revision_id=revision_id))
        self._touch_days(connection, actor, [current["food_day_id"]])
        return self._changed_entry_result(connection, actor, envelope, entry_id=command.entry_id,
            revision_id=revision_id, effective_date=current["effective_date"],
            description=current["description"], change="deleted", nutrition=None,
            day_dates=[current["effective_date"]])

    def _restore(self, connection, actor, envelope):
        command: RestoreFoodEntry = envelope.command
        current = self._check_current_revision(connection, actor, command, allow_deleted=True)
        if current["revision_id"] == command.restore_from_revision_id:
            raise Conflict("Restore source is already the current revision")
        source = connection.execute(sa.select(
            db.food_entry_revisions, db.food_days.c.local_date.label("effective_date")
        ).select_from(db.food_entry_revisions.join(db.food_days, sa.and_(
            db.food_entry_revisions.c.user_id == db.food_days.c.user_id,
            db.food_entry_revisions.c.food_day_id == db.food_days.c.id
        ))).where(
            db.food_entry_revisions.c.user_id == actor,
            db.food_entry_revisions.c.food_entry_id == command.entry_id,
            db.food_entry_revisions.c.id == command.restore_from_revision_id,
        )).mappings().one_or_none()
        if source is None:
            raise NotFound("Restore revision not found")
        if source["state"] != "active":
            raise Conflict("Only an active revision can be restored")
        revision_id = uuid4()
        connection.execute(db.food_entry_revisions.insert().values(
            id=revision_id, user_id=actor, food_entry_id=command.entry_id,
            revision_no=current["revision_no"] + 1, food_day_id=source["food_day_id"],
            applied_operation_id=envelope.operation_id, description=source["description"],
            meal=source["meal"], time_zone=source["time_zone"], state="active"))
        rows = self._copy_components(connection, actor, source["id"], revision_id)
        connection.execute(db.food_entries.update().where(
            db.food_entries.c.user_id == actor, db.food_entries.c.id == command.entry_id
        ).values(current_revision_id=revision_id))
        self._touch_days(connection, actor, [current["food_day_id"], source["food_day_id"]])
        nutrition = entry_nutrition([from_columns(row) for row in rows])
        return self._changed_entry_result(connection, actor, envelope, entry_id=command.entry_id,
            revision_id=revision_id, effective_date=source["effective_date"],
            description=source["description"], change="restored", nutrition=nutrition,
            day_dates=[current["effective_date"], source["effective_date"]])

    @staticmethod
    def _empty_nutrition():
        return NutritionSnapshot(kcal=None, protein_g=None, fat_g=None, carbs_g=None)

    def _recipe_inputs(self, connection, actor, recipe: RecipeDefinition):
        """Validate ingredient sources and calculate nutrition without trusting model arithmetic."""
        nutrition = recipe.nutrition
        if not isinstance(nutrition, CalculatedRecipeNutrition):
            source_exists = connection.execute(sa.select(db.data_sources.c.id).where(
                db.data_sources.c.user_id == actor, db.data_sources.c.id == nutrition.data_source_id
            )).scalar_one_or_none()
            if source_exists is None:
                raise NotFound("Recipe data source not found")
            return nutrition.per_100_g

        ingredients = []
        for ingredient in recipe.ingredients:
            if isinstance(ingredient.source, UnknownIngredientSource):
                ingredients.append((self._empty_nutrition(), Decimal("1")))
                continue
            source: ResolvedIngredientSource = ingredient.source
            quantity = source.quantity
            if quantity.kind != "mass":
                raise Unsupported("Recipe calculation requires a normalized mass source")
            version = connection.execute(sa.select(db.product_versions).where(
                db.product_versions.c.user_id == actor,
                db.product_versions.c.id == source.product_version_id,
            )).mappings().one_or_none()
            if version is None:
                raise NotFound("Recipe ingredient product version not found")
            if version["nutrition_basis"] != "per_100_g" or version["weight_basis"] != quantity.weight_basis:
                raise ApplicationError("Recipe ingredient source and product bases do not match")
            if ingredient.weight_basis is not None and ingredient.weight_basis != quantity.weight_basis:
                raise ApplicationError("Recipe ingredient weight basis is inconsistent")
            ingredients.append((from_columns(version), Decimal(quantity.edible_g)))
        return recipe_per_100_g(ingredients, Decimal(nutrition.finished_yield_g))

    def _recipe_profile(self, connection, actor, recipe_id, version_id):
        row = connection.execute(sa.select(db.recipe_versions).where(
            db.recipe_versions.c.user_id == actor,
            db.recipe_versions.c.recipe_id == recipe_id,
            db.recipe_versions.c.id == version_id,
        )).mappings().one_or_none()
        if row is None:
            raise NotFound("Recipe version not found")
        rows = connection.execute(sa.select(db.recipe_ingredients).where(
            db.recipe_ingredients.c.user_id == actor,
            db.recipe_ingredients.c.recipe_version_id == version_id,
        ).order_by(db.recipe_ingredients.c.position)).mappings().all()
        from nutrition_contracts.commands import RecipeIngredient
        ingredients = [RecipeIngredient.model_validate({
            "name_as_entered": item["name_as_entered"],
            "original_quantity": item["original_quantity"],
            "weight_basis": item["weight_basis"],
            "source": item["source"],
        }) for item in rows]
        return RecipeProfile(recipe_id=recipe_id, version_id=version_id, name=row["name"],
            ingredients=ingredients, cooking_instructions=row["cooking_instructions"],
            per_100_g=from_columns(row))

    @staticmethod
    def _recipe_profile_from_definition(recipe_id, version_id, definition, nutrition):
        return RecipeProfile(recipe_id=recipe_id, version_id=version_id, name=definition.name,
            ingredients=definition.ingredients, cooking_instructions=definition.cooking_instructions,
            per_100_g=nutrition)

    def _insert_recipe_version(self, connection, actor, recipe_id, version_id, version_no, definition, profile):
        nutrition = definition.nutrition
        values = {
            "id": version_id, "user_id": actor, "recipe_id": recipe_id, "version_no": version_no,
            "name": definition.name, "cooking_instructions": definition.cooking_instructions,
            "nutrition_kind": nutrition.kind, "data_source_id": None,
            "finished_yield_g": None, "yield_basis": None,
            "estimate_approval_update_id": None, "calculation_policy_version": None,
            **to_columns(profile),
        }
        if isinstance(nutrition, CalculatedRecipeNutrition):
            values.update(finished_yield_g=Decimal(nutrition.finished_yield_g), yield_basis=nutrition.yield_basis,
                          estimate_approval_update_id=nutrition.estimate_approval_update_id,
                          calculation_policy_version=nutrition.calculation_policy_version)
        else:
            values["data_source_id"] = nutrition.data_source_id
        connection.execute(db.recipe_versions.insert().values(**values))
        for position, ingredient in enumerate(definition.ingredients):
            connection.execute(db.recipe_ingredients.insert().values(
                id=uuid4(), user_id=actor, recipe_version_id=version_id, position=position,
                name_as_entered=ingredient.name_as_entered,
                original_quantity=ingredient.original_quantity.model_dump(mode="json"),
                weight_basis=ingredient.weight_basis,
                source=ingredient.source.model_dump(mode="json")))

    def _recipe_result(self, command, recipe_id, version_id, profile):
        return OutcomeEnvelope(result=Applied(schema_version="1.0", operation_id=command.operation_id,
            outcome="applied", mutations=[MutationReceipt(entity_kind="recipe", entity_id=recipe_id,
                revision_id=version_id, effective_date=None)], food_entries=[], observations=[],
            daily_summaries=[], recipe=profile))

    def _define_recipe(self, connection, actor, envelope):
        command: DefineRecipe = envelope.command
        recipe_id, version_id = uuid4(), uuid4()
        profile = self._recipe_inputs(connection, actor, command.recipe)
        connection.execute(db.recipes.insert().values(id=recipe_id, user_id=actor, current_version_id=version_id))
        self._insert_recipe_version(connection, actor, recipe_id, version_id, 1, command.recipe, profile)
        return self._recipe_result(envelope, recipe_id, version_id,
                                   self._recipe_profile_from_definition(recipe_id, version_id, command.recipe, profile))

    def _revise_recipe(self, connection, actor, envelope):
        command: ReviseRecipe = envelope.command
        recipe = connection.execute(sa.select(db.recipes).where(
            db.recipes.c.user_id == actor, db.recipes.c.id == command.recipe_id
        ).with_for_update()).mappings().one_or_none()
        if recipe is None:
            raise NotFound("Recipe not found")
        if recipe["current_version_id"] != command.expected_version_id:
            raise Conflict("Recipe version has changed")
        current = connection.execute(sa.select(db.recipe_versions.c.version_no).where(
            db.recipe_versions.c.user_id == actor,
            db.recipe_versions.c.id == recipe["current_version_id"],
        )).scalar_one()
        version_id = uuid4()
        profile = self._recipe_inputs(connection, actor, command.replacement)
        self._insert_recipe_version(connection, actor, command.recipe_id, version_id, current + 1,
                                    command.replacement, profile)
        connection.execute(db.recipes.update().where(
            db.recipes.c.user_id == actor, db.recipes.c.id == command.recipe_id
        ).values(current_version_id=version_id))
        return self._recipe_result(envelope, command.recipe_id, version_id,
                                   self._recipe_profile_from_definition(command.recipe_id, version_id,
                                                                        command.replacement, profile))

    def _mutate(self, connection, actor, command):
        if isinstance(command.command, AddConsumedFood):
            return self._add(connection, actor, command)
        if isinstance(command.command, CorrectFoodEntry):
            return self._correct(connection, actor, command)
        if isinstance(command.command, DeleteFoodEntry):
            return self._delete(connection, actor, command)
        if isinstance(command.command, RestoreFoodEntry):
            return self._restore(connection, actor, command)
        if isinstance(command.command, DefineRecipe):
            return self._define_recipe(connection, actor, command)
        if isinstance(command.command, ReviseRecipe):
            return self._revise_recipe(connection, actor, command)
        raise Unsupported("This slice supports resolved food and recipe definition commands only")

    def get_recipe(self, actor: UUID, recipe_id: UUID) -> RecipeProfile:
        with self.engine.begin() as connection:
            self._user(connection, actor, read=True)
            version_id = connection.execute(sa.select(db.recipes.c.current_version_id).where(
                db.recipes.c.user_id == actor, db.recipes.c.id == recipe_id)).scalar_one_or_none()
            if version_id is None:
                raise NotFound("Recipe not found")
            return self._recipe_profile(connection, actor, recipe_id, version_id)

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
        pending = connection.execute(sa.select(sa.func.count()).select_from(db.conversation_jobs).where(
            db.conversation_jobs.c.user_id == actor, db.conversation_jobs.c.status == "unresolved",
            db.conversation_jobs.c.pending_food_date == effective_date)).scalar_one()
        return DailySummary(effective_date=effective_date,
            completeness="unconfirmed" if day is None else day["completeness"],
            explicit_zero_food=False if day is None else day["explicit_zero_food"], pending_food_actions=pending,
            entry_count=len({row["entry_id"] for row in rows}), component_count=len(rows),
            nutrition=day_nutrition([from_columns(row) for row in rows]))

    def get_day(self, actor: UUID, effective_date: date) -> DailySummary:
        with self.engine.begin() as connection:
            self._user(connection, actor, read=True)
            return self._day(connection, actor, effective_date)

    def get_entry(self, actor: UUID, entry_id: UUID) -> FoodEntrySummary:
        with self.engine.begin() as connection:
            self._user(connection, actor, read=True)
            current = self._current_entry(connection, actor, entry_id)
            if current is None:
                raise NotFound("Food entry not found")
            if current["state"] == "deleted":
                return FoodEntrySummary(entry_id=entry_id, revision_id=current["revision_id"],
                    effective_date=current["effective_date"], description=current["description"],
                    nutrition=None, change="deleted")
            rows = connection.execute(self._current_components(actor).where(
                db.food_entries.c.id == entry_id)).mappings().all()
            return FoodEntrySummary(entry_id=entry_id, revision_id=rows[0]["revision_id"],
                effective_date=rows[0]["local_date"], description=rows[0]["entry_description"],
                nutrition=entry_nutrition([from_columns(row) for row in rows]), change="added")
