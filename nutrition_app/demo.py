"""Synthetic seed/harness helpers, not public user-management or catalog APIs."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from nutrition_contracts.commands import (AddConsumedFood, CommandEnvelope, CommandSource, FoodState,
                                          IncrementDailySteps, ProductComponent, SetDailySteps, SetDailyWeight)
from nutrition_contracts.common import Mass, NutrientValue, NutritionSnapshot

from . import schema as db
from .nutrition import to_columns
from .service import FoodService, IncomingMessage, operation_id_for


DEMO_USER_ID = UUID("492873ab-af25-4892-b68e-7088973fc015")
DEMO_DATE = date(2026, 9, 22)


@dataclass(frozen=True)
class Seed:
    user_id: UUID
    account_id: UUID
    telegram_user_id: int
    product_id: UUID
    version_id: UUID
    source_id: UUID


def synthetic_nutrition(*, unknown_fat=False) -> NutritionSnapshot:
    def value(amount):
        return NutrientValue(value=amount, lower=None, upper=None)
    return NutritionSnapshot(kcal=value("100"), protein_g=value("4"),
        fat_g=None if unknown_fat else value("4"), carbs_g=value("12"))


def seed_product(connection, actor: UUID, *, nutrition=None, product_id=None, version_no=1,
                 nutrition_basis="per_100_g", weight_basis="as_sold", name="Synthetic product A",
                 food_kind=None, declared_fat_percent=None):
    source_id, version_id = uuid4(), uuid4()
    connection.execute(db.data_sources.insert().values(id=source_id, user_id=actor,
        kind="synthetic_fixture", evidence={"synthetic": True, "fixture": "M1 product A"}))
    if product_id is None:
        product_id = uuid4()
        connection.execute(db.products.insert().values(id=product_id, user_id=actor, current_version_id=version_id))
    connection.execute(db.product_versions.insert().values(id=version_id, user_id=actor, product_id=product_id,
        version_no=version_no, name=name, data_source_id=source_id,
        food_kind=food_kind, declared_fat_percent=declared_fat_percent,
        nutrition_basis=nutrition_basis, weight_basis=weight_basis,
        **to_columns(nutrition or synthetic_nutrition())))
    connection.execute(db.products.update().where(db.products.c.id == product_id, db.products.c.user_id == actor)
                       .values(current_version_id=version_id))
    return product_id, version_id, source_id


def seed_user(engine: Engine, *, user_id: UUID | None = None, nutrition=None, **product_identity) -> Seed:
    actor, account_id = user_id or uuid4(), uuid4()
    external_user = actor.int % (2 ** 52) + 1
    with engine.begin() as connection:
        connection.execute(db.users.insert().values(id=actor, time_zone="Europe/Berlin"))
        connection.execute(db.telegram_accounts.insert().values(id=account_id, user_id=actor, bot_id=101,
            telegram_user_id=external_user, private_chat_id=external_user))
        product_id, version_id, source_id = seed_product(connection, actor, nutrition=nutrition, **product_identity)
    return Seed(actor, account_id, external_user, product_id, version_id, source_id)


def message(seed: Seed, update_id: int = 1, *, text="250 g synthetic product A") -> IncomingMessage:
    return IncomingMessage(bot_id=101, telegram_update_id=update_id, telegram_message_id=update_id,
        private_chat_id=seed.telegram_user_id, telegram_user_id=seed.telegram_user_id,
        sent_at=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc), text=text)


def food_command(seed: Seed, source_id: UUID, *, grams="250", effective_date=DEMO_DATE,
                 version_id=None, context_revision=0) -> CommandEnvelope:
    return CommandEnvelope(schema_version="1.0", user_id=seed.user_id, operation_id=operation_id_for(source_id),
        context_revision=context_revision, source=CommandSource(origin_update_id=source_id,
            evidence_update_ids=[source_id], pending_action_id=None),
        command=AddConsumedFood(kind="add_consumed_food", food=FoodState(effective_date=effective_date,
            time_zone="Europe/Berlin", meal="lunch", description="Synthetic product A",
            components=[ProductComponent(kind="product", description="Synthetic product A",
                product_version_id=version_id or seed.version_id,
                quantity=Mass(kind="mass", edible_g=grams, gross_g=None, inedible_g=None, weight_basis="as_sold"))])))


def _envelope(seed: Seed, source_id: UUID, command, *, context_revision=0) -> CommandEnvelope:
    return CommandEnvelope(schema_version="1.0", user_id=seed.user_id, operation_id=operation_id_for(source_id),
        context_revision=context_revision, source=CommandSource(origin_update_id=source_id,
            evidence_update_ids=[source_id], pending_action_id=None), command=command)


def weight_command(seed: Seed, source_id: UUID, *, value_kg="76.3", effective_date=DEMO_DATE,
                   expected_revision_id=None, context_revision=0, time_zone="Europe/Berlin") -> CommandEnvelope:
    return _envelope(seed, source_id, SetDailyWeight(kind="set_daily_weight", effective_date=effective_date,
        time_zone=time_zone, value_kg=value_kg, expected_revision_id=expected_revision_id),
        context_revision=context_revision)


def steps_command(seed: Seed, source_id: UUID, *, steps=8200, effective_date=DEMO_DATE,
                  expected_revision_id=None, context_revision=0, time_zone="Europe/Berlin") -> CommandEnvelope:
    return _envelope(seed, source_id, SetDailySteps(kind="set_daily_steps", effective_date=effective_date,
        time_zone=time_zone, steps=steps, expected_revision_id=expected_revision_id),
        context_revision=context_revision)


def increment_steps_command(seed: Seed, source_id: UUID, *, steps, expected_revision_id,
                            effective_date=DEMO_DATE, context_revision=0,
                            time_zone="Europe/Berlin") -> CommandEnvelope:
    return _envelope(seed, source_id, IncrementDailySteps(kind="increment_daily_steps", effective_date=effective_date,
        time_zone=time_zone, steps=steps, expected_revision_id=expected_revision_id),
        context_revision=context_revision)


def run_demo(engine: Engine):
    with engine.connect() as connection:
        exists = connection.execute(sa.select(db.users.c.id).where(db.users.c.id == DEMO_USER_ID)).scalar_one_or_none()
    if exists is None:
        seed = seed_user(engine, user_id=DEMO_USER_ID)
    else:
        with engine.connect() as connection:
            account = connection.execute(sa.select(db.telegram_accounts).where(db.telegram_accounts.c.user_id == DEMO_USER_ID)).mappings().one()
            product = connection.execute(sa.select(db.product_versions).where(db.product_versions.c.user_id == DEMO_USER_ID)
                                         .order_by(db.product_versions.c.created_at, db.product_versions.c.id)).mappings().first()
            seed = Seed(DEMO_USER_ID, account["id"], account["telegram_user_id"], product["product_id"], product["id"], product["data_source_id"])
    service = FoodService(engine)
    source_id = service.accept_message(seed.user_id, message(seed))
    command = food_command(seed, source_id)
    result = service.apply(seed.user_id, command)
    replay = service.apply(seed.user_id, command)
    return {"synthetic_demo": True, "outcome": result.model_dump(mode="json"),
            "replay_preserved_result": replay == result,
            "current_day": service.get_day(seed.user_id, DEMO_DATE).model_dump(mode="json")}
