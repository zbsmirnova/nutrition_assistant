"""Real PostgreSQL acceptance checks. Each test owns a fresh disposable schema.

Run explicitly: python -m unittest discover -s tests/integration -v
No mocking or SQLite fallback; an unavailable database fails the run.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import json
import os
import subprocess
import sys
from threading import Barrier
import unittest
from uuid import uuid4

from alembic import command as alembic_command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
import sqlalchemy as sa
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError, IntegrityError

from nutrition_contracts.commands import (
    CommandEnvelope, CommandSource, CorrectFoodEntry, DeleteFoodEntry,
    FoodState, ProductComponent, RestoreFoodEntry,
)
from nutrition_contracts.common import Mass, NutrientValue
from nutrition_app.db import database_url, engine_for, migrate, ROOT
from nutrition_app.demo import DEMO_DATE, food_command, message, seed_product, seed_user, synthetic_nutrition
from nutrition_app.errors import ApplicationError, Conflict, NotFound, NumericOverflow, Unauthorized
from nutrition_app.outbox import DefinitelyNotSent, FakeSender, OutboxWorker
from nutrition_app.service import FoodService, operation_id_for
from nutrition_app import schema as db


class FoodPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.url = database_url()
        if make_url(self.url).host not in {"127.0.0.1", "localhost", "::1"}:
            self.fail("Integration tests require a local disposable development database")
        self.schema = "ntest_" + uuid4().hex
        self.admin = engine_for(self.url)
        self.engine = None
        self.addCleanup(self.cleanup_database)
        with self.admin.begin() as connection:
            connection.execute(sa.schema.CreateSchema(self.schema))
        self.engine = engine_for(self.url, schema=self.schema)
        migrate(self.engine)
        self.seed = seed_user(self.engine)
        self.service = FoodService(self.engine)

    def cleanup_database(self):
        if self.engine:
            self.engine.dispose()
        with self.admin.begin() as connection:
            connection.execute(sa.schema.DropSchema(self.schema, cascade=True, if_exists=True))
        self.admin.dispose()

    def command(self, update_id=1, **kwargs):
        source = self.service.accept_message(self.seed.user_id, message(self.seed, update_id))
        return food_command(self.seed, source, **kwargs)

    def count(self, table, *, actor=None):
        with self.engine.connect() as connection:
            return connection.execute(sa.select(sa.func.count()).select_from(table)
                .where(table.c.user_id == (actor or self.seed.user_id))).scalar_one()

    def row(self, table):
        with self.engine.connect() as connection:
            return connection.execute(sa.select(table).where(table.c.user_id == self.seed.user_id)).mappings().one()

    def worker(self, *args):
        environment = dict(os.environ, NUTRITION_DATABASE_URL=self.url, NUTRITION_DB_SCHEMA=self.schema)
        return subprocess.run([sys.executable, "-m", "nutrition_app", *args], cwd=ROOT,
                              env=environment, text=True, capture_output=True, timeout=20)

    def test_fresh_migrations_are_repeatable_and_match_current_model(self):
        migrate(self.engine)
        with self.engine.connect() as connection:
            self.assertEqual(connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one(), "0010")
            self.assertEqual(connection.exec_driver_sql("SELECT current_schema()").scalar_one(), self.schema)
            inspector = sa.inspect(connection)
            self.assertEqual(set(inspector.get_table_names()) - {"alembic_version"}, set(db.metadata.tables))
            self.assertEqual(compare_metadata(MigrationContext.configure(connection), db.metadata), [])
            foreign_keys = inspector.get_foreign_keys("food_entries")
            current = next(f for f in foreign_keys if f["name"] == "fk_food_current_revision")
            self.assertEqual(current["referred_columns"], ["user_id", "food_entry_id", "id"])
            self.assertEqual(current["options"], {"initially": "DEFERRED", "deferrable": True})

    def test_migration_round_trip_on_its_own_disposable_schema(self):
        config = Config(str(ROOT / "alembic.ini"))
        with self.engine.begin() as connection:
            config.attributes["connection"] = connection
            alembic_command.downgrade(config, "base")
        migrate(self.engine)
        with self.engine.connect() as connection:
            self.assertEqual(set(sa.inspect(connection).get_table_names()) - {"alembic_version"}, set(db.metadata.tables))

    def test_add_returns_committed_entry_and_day_values(self):
        result = self.service.apply(self.seed.user_id, self.command()).result
        entry, day = result.food_entries[0], result.daily_summaries[0]
        self.assertEqual(entry.nutrition.kcal.value, "250")
        self.assertEqual(entry.nutrition.protein_g.value, "10")
        self.assertEqual(entry.nutrition.fat_g.value, "10")
        self.assertEqual(entry.nutrition.carbs_g.value, "30")
        self.assertEqual(day.nutrition.kcal.amount.value, "250")
        self.assertEqual(day, self.service.get_day(self.seed.user_id, DEMO_DATE))
        self.assertEqual(entry, self.service.get_entry(self.seed.user_id, entry.entry_id))
        for table in (db.food_entries, db.food_entry_revisions, db.food_components, db.applied_operations, db.outbox):
            self.assertEqual(self.count(table), 1)
        self.assertEqual(self.row(db.outbox)["payload"], {"result": result.model_dump(mode="json")})

    def test_correction_keeps_entry_identity_and_revises_snapshot(self):
        added = self.service.apply(self.seed.user_id, self.command(1)).result.food_entries[0]
        source = self.service.accept_message(self.seed.user_id, message(self.seed, 2, text="Было 80 г"))
        correction = CommandEnvelope(
            schema_version="1.0", user_id=self.seed.user_id, operation_id=operation_id_for(source),
            context_revision=1, source=CommandSource(origin_update_id=source, evidence_update_ids=[source], pending_action_id=None),
            command=CorrectFoodEntry(kind="correct_food_entry", entry_id=added.entry_id,
                expected_revision_id=added.revision_id, reason="Было 80 г",
                replacement=FoodState(effective_date=DEMO_DATE, time_zone="Europe/Berlin", meal="lunch",
                    description="Synthetic product A", components=[ProductComponent(
                        kind="product", description="Synthetic product A", product_version_id=self.seed.version_id,
                        quantity=Mass(kind="mass", edible_g="80", gross_g=None, inedible_g=None, weight_basis="as_sold"))])),
        )
        result = self.service.apply(self.seed.user_id, correction).result
        changed = result.food_entries[0]
        self.assertEqual(changed.entry_id, added.entry_id)
        self.assertNotEqual(changed.revision_id, added.revision_id)
        self.assertEqual(changed.change, "corrected")
        self.assertEqual(changed.nutrition.kcal.value, "80")
        self.assertEqual(result.daily_summaries[0].nutrition.kcal.amount.value, "80")
        self.assertEqual(self.service.apply(self.seed.user_id, correction).result, result)
        self.assertEqual(self.count(db.food_entries), 1)
        self.assertEqual(self.count(db.food_entry_revisions), 2)
        self.assertEqual(self.count(db.food_components), 2)
        with self.engine.connect() as connection:
            old = connection.execute(sa.select(db.food_entry_revisions).where(
                db.food_entry_revisions.c.id == added.revision_id)).mappings().one()
            old_component = connection.execute(sa.select(db.food_components).where(
                db.food_components.c.food_entry_revision_id == added.revision_id)).mappings().one()
        self.assertEqual((old["state"], old["revision_no"], old_component["edible_g"]), ("active", 1, Decimal("250")))

    def test_delete_and_restore_preserve_history_and_recalculate_day(self):
        added = self.service.apply(self.seed.user_id, self.command(1)).result.food_entries[0]
        delete_source = self.service.accept_message(self.seed.user_id, message(self.seed, 2, text="Удали запись"))
        delete = CommandEnvelope(
            schema_version="1.0", user_id=self.seed.user_id, operation_id=operation_id_for(delete_source),
            context_revision=1, source=CommandSource(origin_update_id=delete_source, evidence_update_ids=[delete_source], pending_action_id=None),
            command=DeleteFoodEntry(kind="delete_food_entry", entry_id=added.entry_id,
                expected_revision_id=added.revision_id, reason="Удали запись"),
        )
        deleted = self.service.apply(self.seed.user_id, delete).result
        self.assertEqual(deleted.food_entries[0].change, "deleted")
        self.assertIsNone(deleted.food_entries[0].nutrition)
        self.assertEqual(deleted.daily_summaries[0].entry_count, 0)
        self.assertEqual(self.service.get_entry(self.seed.user_id, added.entry_id).change, "deleted")

        restore_source = self.service.accept_message(self.seed.user_id, message(self.seed, 3, text="Верни последнюю запись"))
        restore = CommandEnvelope(
            schema_version="1.0", user_id=self.seed.user_id, operation_id=operation_id_for(restore_source),
            context_revision=2, source=CommandSource(origin_update_id=restore_source, evidence_update_ids=[restore_source], pending_action_id=None),
            command=RestoreFoodEntry(kind="restore_food_entry", entry_id=added.entry_id,
                expected_revision_id=deleted.food_entries[0].revision_id,
                restore_from_revision_id=added.revision_id),
        )
        restored = self.service.apply(self.seed.user_id, restore).result
        self.assertEqual(restored.food_entries[0].change, "restored")
        self.assertEqual(restored.food_entries[0].nutrition.kcal.value, "250")
        self.assertEqual(restored.daily_summaries[0].nutrition.kcal.amount.value, "250")
        self.assertEqual(self.service.apply(self.seed.user_id, restore).result, restored)
        self.assertEqual(self.count(db.food_entries), 1)
        self.assertEqual(self.count(db.food_entry_revisions), 3)
        self.assertEqual(self.count(db.food_components), 2)
        self.assertEqual(self.count(db.outbox), 3)

    def test_stale_food_revision_is_rejected_without_domain_mutation(self):
        added = self.service.apply(self.seed.user_id, self.command(1)).result.food_entries[0]
        source = self.service.accept_message(self.seed.user_id, message(self.seed, 2, text="Удали старую версию"))
        stale = CommandEnvelope(
            schema_version="1.0", user_id=self.seed.user_id, operation_id=operation_id_for(source),
            context_revision=1, source=CommandSource(origin_update_id=source, evidence_update_ids=[source], pending_action_id=None),
            command=DeleteFoodEntry(kind="delete_food_entry", entry_id=added.entry_id,
                expected_revision_id=uuid4(), reason="Удали старую версию"),
        )
        with self.assertRaises(Conflict):
            self.service.apply(self.seed.user_id, stale)
        self.assertEqual(self.service.get_entry(self.seed.user_id, added.entry_id).revision_id, added.revision_id)
        self.assertEqual(self.service.get_day(self.seed.user_id, DEMO_DATE).nutrition.kcal.amount.value, "250")
        self.assertEqual(self.count(db.food_entry_revisions), 1)
        self.assertEqual(self.count(db.outbox), 1)

    def test_correction_move_returns_source_and_destination_day_summaries(self):
        added = self.service.apply(self.seed.user_id, self.command(1)).result.food_entries[0]
        destination = DEMO_DATE.replace(day=DEMO_DATE.day + 1)
        source = self.service.accept_message(self.seed.user_id, message(self.seed, 2, text="Перенеси на завтра"))
        correction = CommandEnvelope(
            schema_version="1.0", user_id=self.seed.user_id, operation_id=operation_id_for(source),
            context_revision=1, source=CommandSource(origin_update_id=source, evidence_update_ids=[source], pending_action_id=None),
            command=CorrectFoodEntry(kind="correct_food_entry", entry_id=added.entry_id,
                expected_revision_id=added.revision_id, reason="Перенеси на завтра",
                replacement=FoodState(effective_date=destination, time_zone="Europe/Berlin",
                    meal="lunch", description="Synthetic product A", components=[ProductComponent(
                        kind="product", description="Synthetic product A", product_version_id=self.seed.version_id,
                        quantity=Mass(kind="mass", edible_g="250", gross_g=None, inedible_g=None, weight_basis="as_sold"))])),
        )
        result = self.service.apply(self.seed.user_id, correction).result
        self.assertEqual([day.effective_date for day in result.daily_summaries], [DEMO_DATE, destination])
        self.assertEqual(result.daily_summaries[0].entry_count, 0)
        self.assertEqual(result.daily_summaries[1].nutrition.kcal.amount.value, "250")
        self.assertEqual(self.service.get_day(self.seed.user_id, DEMO_DATE).entry_count, 0)
        self.assertEqual(self.service.get_day(self.seed.user_id, destination).entry_count, 1)

    def test_duplicate_delivery_and_operation_do_not_add_a_portion(self):
        original = self.command()
        self.assertEqual(self.command(), original)
        first = self.service.apply(self.seed.user_id, original)
        self.assertEqual(self.service.apply(self.seed.user_id, original), first)
        self.assertEqual(self.count(db.inbox_updates), 1)
        self.assertEqual(self.count(db.prepared_operations), 1)
        self.assertEqual(self.count(db.food_entries), 1)
        self.assertEqual(self.count(db.outbox), 1)

    def test_new_identical_text_is_a_new_consumption(self):
        self.service.apply(self.seed.user_id, self.command(1))
        self.service.apply(self.seed.user_id, self.command(2))
        day = self.service.get_day(self.seed.user_id, DEMO_DATE)
        self.assertEqual(day.entry_count, 2)
        self.assertEqual(day.nutrition.kcal.amount.value, "500")

    def test_changed_delivery_or_prepared_payload_is_rejected(self):
        original = self.command()
        self.service.apply(self.seed.user_id, original)
        with self.assertRaises(Conflict):
            self.service.accept_message(self.seed.user_id, message(self.seed, text="changed input"))
        changed = food_command(self.seed, original.source.origin_update_id, grams="80")
        with self.assertRaises(Conflict):
            self.service.apply(self.seed.user_id, changed)
        self.assertEqual(self.service.get_day(self.seed.user_id, DEMO_DATE).nutrition.kcal.amount.value, "250")
        self.assertEqual(self.count(db.outbox), 1)

    def test_delivery_identity_is_unique_across_accounts_of_a_bot(self):
        self.command(1)
        other = seed_user(self.engine)
        with self.assertRaises(Conflict):
            self.service.accept_message(other.user_id, message(other, 1))
        self.assertEqual(self.count(db.inbox_updates, actor=other.user_id), 0)

    def test_concurrent_duplicate_commands_apply_once(self):
        command = self.command()
        barrier = Barrier(4)
        def apply():
            barrier.wait(timeout=10)
            return self.service.apply(self.seed.user_id, command)
        with ThreadPoolExecutor(max_workers=4) as workers:
            results = list(workers.map(lambda _: apply(), range(4)))
        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(self.count(db.food_entries), 1)
        self.assertEqual(self.count(db.outbox), 1)

    def test_concurrent_distinct_resolved_additions_are_all_retained(self):
        commands = [self.command(n) for n in range(1, 5)]
        barrier = Barrier(4)
        def apply(command):
            barrier.wait(timeout=10)
            return self.service.apply(self.seed.user_id, command)
        with ThreadPoolExecutor(max_workers=4) as workers:
            results = list(workers.map(apply, commands))
        self.assertEqual(sorted(r.result.daily_summaries[0].entry_count for r in results), [1, 2, 3, 4])
        day = self.service.get_day(self.seed.user_id, DEMO_DATE)
        self.assertEqual(day.entry_count, 4)
        self.assertEqual(day.nutrition.kcal.amount.value, "1000")

    def test_real_process_crash_before_commit_rolls_back_then_recovers(self):
        command = self.command()
        self.service.prepare(self.seed.user_id, command)
        crash = self.worker("execute", "--user", str(self.seed.user_id), "--operation", str(command.operation_id), "--crash", "before_commit")
        self.assertEqual(crash.returncode, 77, crash.stderr)
        self.assertEqual(self.service.get_day(self.seed.user_id, DEMO_DATE).entry_count, 0)
        for table in (db.food_entries, db.food_components, db.applied_operations, db.outbox):
            self.assertEqual(self.count(table), 0)
        self.assertEqual(self.count(db.inbox_updates), 1)
        self.assertEqual(self.count(db.prepared_operations), 1)
        recovered = self.worker("execute", "--user", str(self.seed.user_id), "--operation", str(command.operation_id))
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        self.assertEqual(json.loads(recovered.stdout)["result"]["daily_summaries"][0]["entry_count"], 1)

    def test_real_process_crash_after_commit_keeps_result_and_response(self):
        command = self.command()
        self.service.prepare(self.seed.user_id, command)
        crash = self.worker("execute", "--user", str(self.seed.user_id), "--operation", str(command.operation_id), "--crash", "after_commit")
        self.assertEqual(crash.returncode, 77, crash.stderr)
        saved_result = self.row(db.applied_operations)["outcome"]
        self.assertEqual(self.row(db.outbox)["status"], "pending")
        recovered = self.worker("execute", "--user", str(self.seed.user_id), "--operation", str(command.operation_id))
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        self.assertEqual(json.loads(recovered.stdout), saved_result)
        sent = self.worker("dispatch")
        self.assertEqual(sent.returncode, 0, sent.stderr)
        self.assertEqual(json.loads(sent.stdout)["status"], "sent")
        self.assertEqual(json.loads(sent.stdout)["deliveries"][0]["payload"], saved_result)
        self.assertEqual(self.count(db.food_entries), 1)
        self.assertEqual(self.count(db.outbox), 1)
        self.assertEqual(json.loads(self.worker("dispatch").stdout)["status"], "idle")

    def test_foreign_actor_cannot_access_messages_entries_products_or_operations(self):
        command = self.command()
        result = self.service.apply(self.seed.user_id, command)
        other = seed_user(self.engine)
        with self.assertRaises(Unauthorized):
            self.service.apply(other.user_id, command)
        with self.assertRaises(Unauthorized):
            self.service.accept_message(other.user_id, message(self.seed))
        with self.assertRaises(NotFound):
            self.service.execute(other.user_id, command.operation_id)
        with self.assertRaises(NotFound):
            self.service.get_entry(other.user_id, result.result.food_entries[0].entry_id)
        self.assertEqual(self.service.get_day(other.user_id, DEMO_DATE).entry_count, 0)
        other_source = self.service.accept_message(other.user_id, message(other, 1001))
        foreign_product = food_command(other, other_source, version_id=self.seed.version_id)
        with self.assertRaises(NotFound):
            self.service.apply(other.user_id, foreign_product)
        foreign_message = food_command(other, command.source.origin_update_id)
        with self.assertRaises(NotFound):
            self.service.prepare(other.user_id, foreign_message)
        self.assertEqual(self.count(db.food_entries, actor=other.user_id), 0)
        self.assertEqual(self.count(db.outbox, actor=other.user_id), 0)

    def test_database_rejects_foreign_source_and_wrong_current_parent(self):
        other = seed_user(self.engine)
        with self.engine.connect() as connection:
            version = dict(connection.execute(sa.select(db.product_versions).where(db.product_versions.c.id == self.seed.version_id)).mappings().one())
        version.update(id=uuid4(), version_no=2, data_source_id=other.source_id)
        with self.assertRaises(IntegrityError), self.engine.begin() as connection:
            connection.execute(db.product_versions.insert().values(**version))
        first = self.service.apply(self.seed.user_id, self.command(1)).result.food_entries[0]
        second = self.service.apply(self.seed.user_id, self.command(2)).result.food_entries[0]
        with self.assertRaises(IntegrityError), self.engine.begin() as connection:
            connection.execute(db.food_entries.update().where(db.food_entries.c.id == first.entry_id)
                               .values(current_revision_id=second.revision_id))
        self.assertEqual(self.service.get_entry(self.seed.user_id, first.entry_id).revision_id, first.revision_id)

    def test_unknown_partial_empty_and_zero_intake_are_not_conflated(self):
        empty = self.service.get_day(self.seed.user_id, DEMO_DATE)
        self.assertEqual(empty.nutrition.fat_g.kind, "empty")
        self.assertFalse(empty.explicit_zero_food)
        with self.engine.begin() as connection:
            _, unknown_version, _ = seed_product(connection, self.seed.user_id, nutrition=synthetic_nutrition(unknown_fat=True))
        self.service.apply(self.seed.user_id, self.command(1, version_id=unknown_version))
        unknown = self.service.get_day(self.seed.user_id, DEMO_DATE)
        self.assertEqual(unknown.nutrition.fat_g.kind, "unknown")
        result = self.service.apply(self.seed.user_id, self.command(2))
        fat = result.result.daily_summaries[0].nutrition.fat_g
        self.assertEqual(fat.kind, "partial")
        self.assertEqual(fat.known_subtotal, "10")
        self.assertEqual((fat.known_components, fat.unknown_components), (1, 1))

    def test_multiple_components_keep_entry_unknown_and_day_partial(self):
        command = self.command()
        with self.engine.begin() as connection:
            _, unknown_version, _ = seed_product(connection, self.seed.user_id, nutrition=synthetic_nutrition(unknown_fat=True))
        extra = command.command.food.components[0].model_copy(update={"product_version_id": unknown_version})
        command.command.food.components.append(extra)
        result = self.service.apply(self.seed.user_id, command).result
        self.assertIsNone(result.food_entries[0].nutrition.fat_g)
        self.assertEqual(result.daily_summaries[0].nutrition.fat_g.known_subtotal, "10")
        self.assertEqual(result.daily_summaries[0].entry_count, 1)
        self.assertEqual(result.daily_summaries[0].component_count, 2)

    def test_new_product_version_preserves_old_meals_and_source_evidence(self):
        first = self.service.apply(self.seed.user_id, self.command(1)).result.food_entries[0]
        nutrition = synthetic_nutrition()
        nutrition.kcal = NutrientValue(value="200", lower=None, upper=None)
        with self.engine.begin() as connection:
            _, new_version, _ = seed_product(connection, self.seed.user_id, nutrition=nutrition,
                                             product_id=self.seed.product_id, version_no=2)
        self.assertEqual(self.service.get_entry(self.seed.user_id, first.entry_id).nutrition.kcal.value, "250")
        self.service.apply(self.seed.user_id, self.command(2, version_id=new_version))
        self.assertEqual(self.service.get_day(self.seed.user_id, DEMO_DATE).nutrition.kcal.amount.value, "750")
        with self.engine.connect() as connection:
            old = connection.execute(sa.select(db.food_components).where(db.food_components.c.food_entry_revision_id == first.revision_id)).mappings().one()
        self.assertEqual(old["product_version_id"], self.seed.version_id)
        self.assertEqual(old["data_source_id"], self.seed.source_id)
        self.assertEqual(old["calculation_version"], "decimal-components-v1")

    def test_snapshot_rows_and_response_payload_cannot_be_overwritten(self):
        self.service.apply(self.seed.user_id, self.command())
        for table, column in ((db.data_sources, "kind"), (db.product_versions, "name"), (db.inbox_updates, "text"),
                              (db.prepared_operations, "command"), (db.applied_operations, "outcome"),
                              (db.food_entry_revisions, "description"), (db.food_components, "description")):
            with self.subTest(table=table.name), self.assertRaises(DBAPIError), self.engine.begin() as connection:
                connection.execute(table.update().where(table.c.user_id == self.seed.user_id).values({column: table.c[column]}))
        with self.assertRaises(DBAPIError), self.engine.begin() as connection:
            connection.execute(db.outbox.update().where(db.outbox.c.user_id == self.seed.user_id).values(payload={"tampered": True}))

    def test_quantity_and_source_basis_must_match(self):
        command = self.command()
        command.command.food.components[0].quantity.weight_basis = "raw"
        with self.assertRaises(ApplicationError):
            self.service.apply(self.seed.user_id, command)
        self.assertEqual(self.count(db.food_entries), 0)
        self.assertEqual(self.count(db.outbox), 0)

    def test_volume_requires_a_volume_source_and_bones_use_edible_mass(self):
        command = self.command(1, grams="100")
        quantity = command.command.food.components[0].quantity
        quantity.gross_g, quantity.inedible_g = "125", "25"
        result = self.service.apply(self.seed.user_id, command)
        self.assertEqual(result.result.food_entries[0].nutrition.kcal.value, "100")
        component = self.row(db.food_components)
        self.assertEqual((component["gross_g"], component["inedible_g"], component["edible_g"]),
                         (Decimal(125), Decimal(25), Decimal(100)))
        volume = self.command(2).model_dump(mode="json")
        volume["command"]["food"]["components"][0]["quantity"] = {"kind": "volume", "ml": "250", "weight_basis": "as_sold"}
        with self.assertRaises(ApplicationError):
            self.service.apply(self.seed.user_id, CommandEnvelope.model_validate_json(json.dumps(volume)))

    def test_day_overflow_rolls_back_the_second_mutation_and_its_response(self):
        nutrition = synthetic_nutrition()
        nutrition.kcal = NutrientValue(value="999999999999.999999", lower=None, upper=None)
        with self.engine.begin() as connection:
            _, maximum_version, _ = seed_product(connection, self.seed.user_id, nutrition=nutrition)
        self.service.apply(self.seed.user_id, self.command(1, grams="100", version_id=maximum_version))
        with self.assertRaises(NumericOverflow):
            self.service.apply(self.seed.user_id, self.command(2, grams="1"))
        self.assertEqual(self.count(db.food_entries), 1)
        self.assertEqual(self.count(db.applied_operations), 1)
        self.assertEqual(self.count(db.outbox), 1)

    def test_source_instant_and_effective_date_survive_a_later_process(self):
        msg = message(self.seed)
        msg.sent_at = datetime(2026, 9, 22, 21, 59, tzinfo=timezone.utc)  # 23:59 Berlin.
        source = self.service.accept_message(self.seed.user_id, msg)
        command = food_command(self.seed, source, effective_date=date(2026, 9, 21))  # Explicit backdate.
        self.service.prepare(self.seed.user_id, command)
        result = self.worker("execute", "--user", str(self.seed.user_id), "--operation", str(command.operation_id))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["result"]["daily_summaries"][0]["effective_date"], "2026-09-21")
        self.assertEqual(self.row(db.inbox_updates)["source_sent_at"], msg.sent_at)
        self.assertEqual(self.row(db.food_entry_revisions)["time_zone"], "Europe/Berlin")
        self.assertEqual(self.service.get_day(self.seed.user_id, date(2026, 9, 22)).entry_count, 0)

    def test_existing_complete_day_remains_complete_after_an_addition(self):
        with self.engine.begin() as connection:
            connection.execute(db.food_days.insert().values(user_id=self.seed.user_id, local_date=DEMO_DATE,
                time_zone="Europe/Berlin", completeness="complete", explicit_zero_food=True))
        result = self.service.apply(self.seed.user_id, self.command()).result.daily_summaries[0]
        self.assertEqual(result.completeness, "complete")
        self.assertFalse(result.explicit_zero_food)

    def test_concurrent_delivery_workers_claim_one_response_once(self):
        self.service.apply(self.seed.user_id, self.command())
        barrier = Barrier(2)
        def claim():
            barrier.wait(timeout=10)
            return OutboxWorker(self.engine).claim()
        with ThreadPoolExecutor(max_workers=2) as workers:
            claims = list(workers.map(lambda _: claim(), range(2)))
        self.assertEqual(sum(item is not None for item in claims), 1)
        self.assertEqual(self.row(db.outbox)["attempts"], 1)

    def test_uncertain_send_is_visible_and_not_blindly_repeated(self):
        self.service.apply(self.seed.user_id, self.command())
        class TimeoutSender:
            def send(self, delivery):
                raise TimeoutError("Unknown external result")
        worker = OutboxWorker(self.engine)
        self.assertEqual(worker.dispatch_one(TimeoutSender()), "uncertain")
        self.assertEqual(self.row(db.outbox)["status"], "uncertain")
        sender = FakeSender()
        self.assertEqual(worker.dispatch_one(sender), "idle")
        self.assertEqual(sender.deliveries, [])
        self.assertEqual(self.count(db.food_entries), 1)

    def test_proven_unsent_retries_are_bounded(self):
        self.service.apply(self.seed.user_id, self.command())
        class OfflineSender:
            def send(self, delivery):
                raise DefinitelyNotSent()
        worker = OutboxWorker(self.engine)
        for _ in range(3):
            self.assertEqual(worker.dispatch_one(OfflineSender()), "retry_or_failed")
        self.assertEqual(self.row(db.outbox)["status"], "failed")
        self.assertEqual(self.row(db.outbox)["attempts"], 3)
        self.assertEqual(worker.dispatch_one(OfflineSender()), "idle")

    def test_expired_sender_cannot_acknowledge_a_lost_claim(self):
        self.service.apply(self.seed.user_id, self.command())
        worker = OutboxWorker(self.engine)
        delivery = worker.claim()
        with self.engine.begin() as connection:
            connection.execute(db.outbox.update().where(db.outbox.c.id == delivery.id)
                               .values(lease_until=sa.func.now() - timedelta(seconds=1)))
        self.assertIsNone(worker.claim())
        self.assertEqual(self.row(db.outbox)["status"], "uncertain")
        self.assertFalse(worker._finish(delivery, "sent"))
