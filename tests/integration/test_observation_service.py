"""Real PostgreSQL acceptance checks for W017 daily observations.

Run explicitly: python -m unittest discover -s tests/integration -v
No mocking or SQLite fallback; an unavailable database fails the run.
"""

from datetime import date
import unittest
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.engine import make_url

from nutrition_app.db import database_url, engine_for, migrate
from nutrition_app.demo import (DEMO_DATE, increment_steps_command, message, seed_user,
                                steps_command, weight_command)
from nutrition_app.errors import Conflict, Unauthorized
from nutrition_app.rendering import render_result
from nutrition_app.service import FoodService
from nutrition_app import schema as db


class ObservationTests(unittest.TestCase):
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

    def source(self, update_id):
        return self.service.accept_message(self.seed.user_id, message(self.seed, update_id))

    def count(self, table, *, actor=None):
        with self.engine.connect() as connection:
            return connection.execute(sa.select(sa.func.count()).select_from(table)
                .where(table.c.user_id == (actor or self.seed.user_id))).scalar_one()

    # --- Weight -----------------------------------------------------------------

    def test_set_weight_creates_one_slot_and_revision(self):
        command = weight_command(self.seed, self.source(1), value_kg="76.3")
        result = self.service.apply(self.seed.user_id, command).result
        self.assertEqual(result.outcome, "applied")
        snapshot = result.observations[0]
        self.assertEqual(snapshot.kind, "daily_weight")
        self.assertEqual(snapshot.value_kg, "76.3")
        self.assertEqual(snapshot.effective_date, DEMO_DATE)
        self.assertEqual(self.count(db.observations), 1)
        self.assertEqual(self.count(db.observation_revisions), 1)
        self.assertEqual(self.service.get_observation(self.seed.user_id, "weight", DEMO_DATE), snapshot)

    def test_later_weight_replaces_current_and_keeps_history(self):
        first = self.service.apply(self.seed.user_id, weight_command(self.seed, self.source(1),
            value_kg="76.3")).result
        second = self.service.apply(self.seed.user_id, weight_command(self.seed, self.source(2),
            value_kg="76.1", expected_revision_id=first.observations[0].revision_id)).result
        self.assertEqual(second.observations[0].value_kg, "76.1")
        self.assertEqual(self.count(db.observations), 1)
        self.assertEqual(self.count(db.observation_revisions), 2)
        current = self.service.get_observation(self.seed.user_id, "weight", DEMO_DATE)
        self.assertEqual(current.value_kg, "76.1")
        self.assertEqual(current.revision_id, second.observations[0].revision_id)

    def test_repeated_identical_weight_is_a_no_op(self):
        first = self.service.apply(self.seed.user_id, weight_command(self.seed, self.source(1),
            value_kg="76.3")).result
        repeat = self.service.apply(self.seed.user_id, weight_command(self.seed, self.source(2),
            value_kg="76.3", expected_revision_id=first.observations[0].revision_id)).result
        self.assertEqual(repeat.outcome, "no_change")
        self.assertEqual(repeat.reason, "same_value")
        self.assertEqual(self.count(db.observation_revisions), 1)

    def test_replacing_weight_requires_the_current_revision(self):
        self.service.apply(self.seed.user_id, weight_command(self.seed, self.source(1), value_kg="76.3"))
        with self.assertRaises(Conflict):
            self.service.apply(self.seed.user_id, weight_command(self.seed, self.source(2),
                value_kg="76.1", expected_revision_id=uuid4()))
        with self.assertRaises(Conflict):
            self.service.apply(self.seed.user_id, weight_command(self.seed, self.source(3),
                value_kg="76.1", expected_revision_id=None))

    def test_set_with_expected_revision_but_no_value_conflicts(self):
        with self.assertRaises(Conflict):
            self.service.apply(self.seed.user_id, weight_command(self.seed, self.source(1),
                value_kg="76.3", expected_revision_id=uuid4()))

    # --- Steps ------------------------------------------------------------------

    def test_set_steps_then_replace_keeps_one_slot(self):
        first = self.service.apply(self.seed.user_id, steps_command(self.seed, self.source(1), steps=8200)).result
        self.assertEqual(first.observations[0].steps, 8200)
        second = self.service.apply(self.seed.user_id, steps_command(self.seed, self.source(2),
            steps=9000, expected_revision_id=first.observations[0].revision_id)).result
        self.assertEqual(second.observations[0].steps, 9000)
        self.assertEqual(self.count(db.observations), 1)
        self.assertEqual(self.count(db.observation_revisions), 2)
        self.assertEqual(self.service.get_observation(self.seed.user_id, "daily_steps", DEMO_DATE).steps, 9000)

    def test_explicit_zero_steps_differs_from_missing(self):
        self.assertIsNone(self.service.get_observation(self.seed.user_id, "daily_steps", DEMO_DATE))
        result = self.service.apply(self.seed.user_id, steps_command(self.seed, self.source(1), steps=0)).result
        self.assertEqual(result.observations[0].steps, 0)
        self.assertEqual(self.service.get_observation(self.seed.user_id, "daily_steps", DEMO_DATE).steps, 0)

    def test_increment_requires_a_known_starting_total(self):
        with self.assertRaises(Conflict):
            self.service.apply(self.seed.user_id, increment_steps_command(self.seed, self.source(1),
                steps=500, expected_revision_id=uuid4()))
        base = self.service.apply(self.seed.user_id, steps_command(self.seed, self.source(2), steps=8200)).result
        added = self.service.apply(self.seed.user_id, increment_steps_command(self.seed, self.source(3),
            steps=500, expected_revision_id=base.observations[0].revision_id)).result
        self.assertEqual(added.observations[0].steps, 8700)
        self.assertEqual(self.count(db.observation_revisions), 2)

    def test_increment_records_origin_kind(self):
        base = self.service.apply(self.seed.user_id, steps_command(self.seed, self.source(1), steps=100)).result
        self.service.apply(self.seed.user_id, increment_steps_command(self.seed, self.source(2),
            steps=50, expected_revision_id=base.observations[0].revision_id))
        with self.engine.connect() as connection:
            kinds = connection.execute(sa.select(db.observation_revisions.c.origin_kind)
                .order_by(db.observation_revisions.c.revision_no)).scalars().all()
        self.assertEqual(kinds, ["manual", "increment"])

    # --- Dates, ownership, idempotency -----------------------------------------

    def test_backdating_uses_a_separate_daily_slot(self):
        earlier = date(2026, 9, 20)
        self.service.apply(self.seed.user_id, weight_command(self.seed, self.source(1), value_kg="76.3"))
        self.service.apply(self.seed.user_id, weight_command(self.seed, self.source(2),
            value_kg="75.0", effective_date=earlier))
        self.assertEqual(self.count(db.observations), 2)
        self.assertEqual(self.service.get_observation(self.seed.user_id, "weight", earlier).value_kg, "75")
        self.assertEqual(self.service.get_observation(self.seed.user_id, "weight", DEMO_DATE).value_kg, "76.3")

    def test_weight_and_steps_share_a_date_without_collision(self):
        self.service.apply(self.seed.user_id, weight_command(self.seed, self.source(1), value_kg="76.3"))
        self.service.apply(self.seed.user_id, steps_command(self.seed, self.source(2), steps=8200))
        self.assertEqual(self.count(db.observations), 2)
        self.assertEqual(self.service.get_observation(self.seed.user_id, "weight", DEMO_DATE).value_kg, "76.3")
        self.assertEqual(self.service.get_observation(self.seed.user_id, "daily_steps", DEMO_DATE).steps, 8200)

    def test_duplicate_operation_does_not_add_a_revision(self):
        command = weight_command(self.seed, self.source(1), value_kg="76.3")
        first = self.service.apply(self.seed.user_id, command)
        replay = self.service.apply(self.seed.user_id, command)
        self.assertEqual(first, replay)
        self.assertEqual(self.count(db.observation_revisions), 1)

    def test_foreign_user_cannot_see_or_replace_observations(self):
        first = self.service.apply(self.seed.user_id, weight_command(self.seed, self.source(1),
            value_kg="76.3")).result
        other = seed_user(self.engine)
        self.assertIsNone(self.service.get_observation(other.user_id, "weight", DEMO_DATE))
        with self.assertRaises(Unauthorized):
            self.service.get_observation(uuid4(), "weight", DEMO_DATE)
        # A foreign user's own new value is an independent slot, not a replacement.
        other_source = self.service.accept_message(other.user_id, message(other, 900))
        other_result = self.service.apply(other.user_id, weight_command(other, other_source,
            value_kg="60.0")).result
        self.assertNotEqual(other_result.observations[0].observation_id, first.observations[0].observation_id)
        self.assertEqual(self.service.get_observation(self.seed.user_id, "weight", DEMO_DATE).value_kg, "76.3")

    # --- Rendering --------------------------------------------------------------

    def test_confirmations_are_russian(self):
        weight = self.service.apply(self.seed.user_id, weight_command(self.seed, self.source(1),
            value_kg="76.3"))
        self.assertEqual(render_result(weight.model_dump(mode="json")), "Вес за сегодня записан: 76,3 кг.")
        steps = self.service.apply(self.seed.user_id, steps_command(self.seed, self.source(2), steps=8200))
        self.assertEqual(render_result(steps.model_dump(mode="json")),
                         "Записано шагов за 22.09.2026: 8,2 тыс. шагов.")
        repeat = self.service.apply(self.seed.user_id, weight_command(self.seed, self.source(3),
            value_kg="76.3", expected_revision_id=weight.result.observations[0].revision_id))
        self.assertIn("уже записано", render_result(repeat.model_dump(mode="json")))


if __name__ == "__main__":
    unittest.main()
