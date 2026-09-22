"""Independent W001 probes; synthetic records, private random schema per test."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from decimal import Decimal
from threading import Barrier
from uuid import uuid4
import json
import unittest
import sqlalchemy as sa
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from alembic import command as alembic_command
from alembic.config import Config
from nutrition_app import schema as db
from nutrition_app.db import ROOT, database_url, engine_for, migrate
from nutrition_app.demo import food_command, message, seed_product, seed_user
from nutrition_app.errors import Conflict, NotFound
from nutrition_app.service import FoodService
from nutrition_contracts.commands import CommandEnvelope
from nutrition_contracts.common import NutrientValue, NutritionSnapshot


class IndependentQA(unittest.TestCase):
    def setUp(self):
        self.url = database_url()
        self.assertIn(make_url(self.url).host, {'127.0.0.1', 'localhost', '::1'})
        self.schema = 'nqa_' + uuid4().hex
        self.admin = engine_for(self.url)
        self.engine = None
        self.addCleanup(self.cleanup)
        with self.admin.begin() as connection:
            connection.execute(sa.schema.CreateSchema(self.schema))
        self.engine = engine_for(self.url, schema=self.schema)
        migrate(self.engine)
        self.seed = seed_user(self.engine)
        self.service = FoodService(self.engine)

    def cleanup(self):
        if self.engine:
            self.engine.dispose()
        with self.admin.begin() as connection:
            connection.execute(sa.schema.DropSchema(self.schema, cascade=True, if_exists=True))
        self.admin.dispose()

    def command(self, number=1, **kwargs):
        source = self.service.accept_message(self.seed.user_id, message(self.seed, number))
        return food_command(self.seed, source, **kwargs)

    def rows(self, table):
        with self.engine.connect() as connection:
            return list(connection.execute(sa.select(table)).mappings())

    def assert_no_mutation(self):
        for table in (db.food_days, db.food_entries, db.food_entry_revisions,
                      db.food_components, db.applied_operations, db.outbox):
            self.assertEqual(len(self.rows(table)), 0, table.name)
        self.assertEqual(self.rows(db.users)[0]['context_revision'], 0)

    def migrate_to(self, revision, downgrade=False):
        config = Config(str(ROOT / 'alembic.ini'))
        config.set_main_option('script_location', str(ROOT / 'migrations'))
        with self.engine.begin() as connection:
            config.attributes['connection'] = connection
            (alembic_command.downgrade if downgrade else alembic_command.upgrade)(config, revision)

    def test_qa01_fractional_volume_bounds_and_known_zero(self):
        # Independently calculated 37.5/100 = 0.375, including explicitly zero fat.
        def n(value, lower=None, upper=None):
            return NutrientValue(value=value, lower=lower, upper=upper)
        profile = NutritionSnapshot(kcal=n('83.2', '80', '88'), protein_g=n('7.2'),
                                    fat_g=n('0'), carbs_g=None)
        with self.engine.begin() as connection:
            _, version, _ = seed_product(connection, self.seed.user_id, nutrition=profile,
                                         nutrition_basis='per_100_ml')
        command = self.command(version_id=version).model_dump(mode='json')
        command['command']['food']['components'][0]['quantity'] = {
            'kind': 'volume', 'ml': '37.5', 'weight_basis': 'as_sold'}
        result = self.service.apply(self.seed.user_id,
            CommandEnvelope.model_validate_json(json.dumps(command))).result
        entry = result.food_entries[0]
        self.assertEqual(entry.nutrition.kcal.model_dump(), {'value': '31.2', 'lower': '30', 'upper': '33'})
        self.assertEqual(entry.nutrition.protein_g.value, '2.7')
        day = result.daily_summaries[0]
        self.assertEqual(day.nutrition.fat_g.kind, 'complete')
        self.assertEqual(day.nutrition.fat_g.amount.value, '0')
        self.assertEqual(day.nutrition.carbs_g.kind, 'unknown')
        self.assertEqual(self.rows(db.food_components)[0]['volume_ml'], Decimal('37.5'))
        self.assertEqual(self.service.get_day(self.seed.user_id, day.effective_date), day)

    def test_qa02_frozen_version_survives_catalog_change_before_execution(self):
        command = self.command(grams='125')
        self.service.prepare(self.seed.user_id, command)
        profile = NutritionSnapshot(**{k: NutrientValue(value='999', lower=None, upper=None)
            for k in ('kcal', 'protein_g', 'fat_g', 'carbs_g')})
        with self.engine.begin() as connection:
            seed_product(connection, self.seed.user_id, product_id=self.seed.product_id,
                         version_no=2, nutrition=profile)
        first = FoodService(self.engine).execute(self.seed.user_id, command.operation_id)
        self.assertEqual(first.result.food_entries[0].nutrition.kcal.value, '125')
        self.assertEqual(self.rows(db.food_components)[0]['product_version_id'], self.seed.version_id)
        second = self.service.apply(self.seed.user_id, self.command(2, grams='25'))
        self.assertEqual(second.result.daily_summaries[0].nutrition.kcal.amount.value, '150')
        self.assertEqual(self.service.execute(self.seed.user_id, command.operation_id), first)
        self.assertEqual(first.result.daily_summaries[0].nutrition.kcal.amount.value, '125')
        self.assertEqual(self.service.get_day(self.seed.user_id, command.command.food.effective_date)
                         .nutrition.kcal.amount.value, '150')

    def test_qa03_database_outbox_insert_failure_rolls_back_entire_mutation(self):
        command = self.command()
        with self.engine.begin() as connection:
            connection.exec_driver_sql("""CREATE FUNCTION qa_reject() RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN RAISE EXCEPTION 'QA deliberate insertion failure'; END; $$""")
            connection.exec_driver_sql('CREATE TRIGGER qa_failure BEFORE INSERT ON outbox '
                                       'FOR EACH ROW EXECUTE FUNCTION qa_reject()')
        with self.assertRaises(DBAPIError):
            self.service.apply(self.seed.user_id, command)
        self.assert_no_mutation()
        self.assertEqual(len(self.rows(db.prepared_operations)), 1)
        with self.engine.begin() as connection:
            connection.exec_driver_sql('DROP TRIGGER qa_failure ON outbox')
        self.service.execute(self.seed.user_id, command.operation_id)
        self.assertEqual(len(self.rows(db.outbox)), 1)

    def test_qa04_deferred_failure_at_commit_never_returns_success(self):
        command = self.command()
        with self.engine.begin() as connection:
            connection.exec_driver_sql("""CREATE FUNCTION qa_commit_reject() RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN RAISE EXCEPTION 'QA deliberate deferred failure'; END; $$""")
            connection.exec_driver_sql('CREATE CONSTRAINT TRIGGER qa_failure AFTER INSERT ON food_entries '
                'DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION qa_commit_reject()')
        observed = []
        with self.assertRaises(DBAPIError):
            self.service.apply(self.seed.user_id, command, fault=observed.append)
        self.assertEqual(observed, ['before_commit'])
        self.assert_no_mutation()
        with self.engine.begin() as connection:
            connection.exec_driver_sql('DROP TRIGGER qa_failure ON food_entries')
        self.service.execute(self.seed.user_id, command.operation_id)
        self.assertEqual(len(self.rows(db.food_entries)), 1)

    def test_qa05_mixed_foreign_component_is_atomic(self):
        other = seed_user(self.engine)
        command = self.command()
        command.command.food.components.append(command.command.food.components[0].model_copy(
            update={'product_version_id': other.version_id}))
        with self.assertRaises(NotFound):
            self.service.apply(self.seed.user_id, command)
        for table in (db.food_days, db.food_entries, db.applied_operations, db.outbox):
            self.assertEqual(len(self.rows(table)), 0)

    def test_qa06_populated_upgrade_preserves_frozen_result_and_trigger(self):
        command = self.command()
        original = self.service.apply(self.seed.user_id, command)
        self.migrate_to('0001', downgrade=True)
        self.migrate_to('head')
        self.assertEqual(self.service.apply(self.seed.user_id, command), original)
        self.assertEqual(self.rows(db.inbox_updates)[0]['bot_id'], 101)
        self.assertEqual(self.rows(db.inbox_updates)[0]['id'], command.source.origin_update_id)
        self.assertEqual(self.rows(db.outbox)[0]['payload'], original.model_dump(mode='json'))
        with self.assertRaises(DBAPIError), self.engine.begin() as connection:
            connection.execute(db.inbox_updates.update().values(text='should remain immutable'))

    def test_qa07_failed_upgrade_is_transactional_and_preserves_trigger(self):
        self.command()
        other = seed_user(self.engine)
        self.migrate_to('0001', downgrade=True)
        legacy_inbox = sa.Table('inbox_updates', sa.MetaData(), autoload_with=self.engine)
        duplicate = dict(self.rows(legacy_inbox)[0])
        duplicate.update(id=uuid4(), user_id=other.user_id, telegram_account_id=other.account_id)
        # This duplicate was allowed by 0001, but cannot migrate to bot scope.
        with self.engine.begin() as connection:
            connection.execute(legacy_inbox.insert().values(**duplicate))
        with self.assertRaises(DBAPIError):
            self.migrate_to('head')
        with self.engine.connect() as connection:
            self.assertEqual(connection.exec_driver_sql('SELECT version_num FROM alembic_version').scalar_one(), '0001')
            self.assertEqual(connection.exec_driver_sql('SELECT count(*) FROM inbox_updates').scalar_one(), 2)
            self.assertNotIn('bot_id', {c['name'] for c in sa.inspect(connection).get_columns('inbox_updates')})
        with self.assertRaises(DBAPIError), self.engine.begin() as connection:
            connection.exec_driver_sql("UPDATE inbox_updates SET text = 'should remain immutable'")

    def test_qa08_simultaneous_identical_delivery_freezes_one_source(self):
        barrier = Barrier(6)
        def accept(_):
            barrier.wait(timeout=10)
            return self.service.accept_message(self.seed.user_id, message(self.seed))
        with ThreadPoolExecutor(max_workers=6) as pool:
            sources = list(pool.map(accept, range(6)))
        self.assertEqual(len(set(sources)), 1)
        self.assertEqual(len(self.rows(db.inbox_updates)), 1)

    def test_qa09_changed_payload_under_concurrent_operation_has_single_winner(self):
        original = self.command(grams='125')
        changed = food_command(self.seed, original.source.origin_update_id, grams='75')
        barrier = Barrier(2)
        def apply(command):
            barrier.wait(timeout=10)
            try:
                return self.service.apply(self.seed.user_id, command)
            except Conflict:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(apply, [original, changed]))
        self.assertEqual(sum(r is not None for r in results), 1)
        winner = next(r for r in results if r is not None)
        self.assertEqual(len(self.rows(db.food_entries)), 1)
        self.assertEqual(len(self.rows(db.outbox)), 1)
        self.assertEqual(self.rows(db.outbox)[0]['payload'], winner.model_dump(mode='json'))

    def test_qa10_frozen_timezone_survives_profile_change_and_dst_source(self):
        msg = message(self.seed)
        msg.sent_at = datetime(2026, 10, 25, 0, 59, tzinfo=timezone.utc)
        source = self.service.accept_message(self.seed.user_id, msg)
        command = food_command(self.seed, source, effective_date=date(2026, 10, 24))
        self.service.prepare(self.seed.user_id, command)
        with self.engine.begin() as connection:
            connection.execute(db.users.update().where(db.users.c.id == self.seed.user_id)
                               .values(time_zone='Pacific/Auckland'))
        result = FoodService(self.engine).execute(self.seed.user_id, command.operation_id)
        self.assertEqual(result.result.daily_summaries[0].effective_date, date(2026, 10, 24))
        self.assertEqual(self.rows(db.inbox_updates)[0]['source_time_zone'], 'Europe/Berlin')
        self.assertEqual(self.rows(db.food_entry_revisions)[0]['time_zone'], 'Europe/Berlin')
        self.assertEqual(self.rows(db.food_days)[0]['time_zone'], 'Europe/Berlin')
        self.assertEqual(self.rows(db.inbox_updates)[0]['source_sent_at'], msg.sent_at)


if __name__ == '__main__':
    unittest.main(verbosity=2)
