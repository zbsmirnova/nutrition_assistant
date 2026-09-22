"""Real PostgreSQL, simulated Nebius responses: no live provider requests."""
from datetime import datetime, timezone
import json
import unittest

import sqlalchemy as sa
import test_food_service as food_tests
from nutrition_app import schema as db
from nutrition_app.conversation import ConversationWorker
from nutrition_app.conversation_demo import PRODUCT_NAME, TEXT, dairy_nutrition, fixture
from nutrition_app.demo import message, seed_user
from nutrition_app.nebius import NebiusConfig, NebiusParser


class NebiusWorkerTests(unittest.TestCase):
    cleanup_database = food_tests.FoodPersistenceTests.cleanup_database
    count = food_tests.FoodPersistenceTests.count
    row = food_tests.FoodPersistenceTests.row

    def setUp(self):
        food_tests.FoodPersistenceTests.setUp(self)
        self.seed = seed_user(self.engine, name=PRODUCT_NAME, food_kind="dairy",
                              declared_fat_percent="5", nutrition=dairy_nutrition())
        self.actor = self.seed.user_id
        self.worker = ConversationWorker(self.engine)
        self.calls = []

    def source(self, number=1, text=TEXT):
        return self.service.accept_message(self.actor, message(self.seed, number, text=text))

    def parser(self, *, status=200, output=None, headers=None, key="test-secret", model="example/model"):
        def send(body, timeout):
            self.calls.append(json.loads(body))
            raw = {"choices": [{"index": 0, "finish_reason": "stop", "message": {
                "role": "assistant", "content": json.dumps(fixture()["output"] if output is None else output)}}]}
            return status, headers or {}, json.dumps(raw).encode()
        return NebiusParser(NebiusConfig(key, model), request=send)

    def due(self):
        with self.engine.begin() as connection:
            connection.execute(db.conversation_jobs.update().where(db.conversation_jobs.c.user_id == self.actor)
                               .values(next_attempt_at=sa.func.now()))

    def test_provider_result_saves_expected_food_and_replay_does_not_call_model(self):
        source = self.source();parser = self.parser()
        result = self.worker.run_one(self.actor, parser, origin=source)
        day = result["outcome"]["result"]["daily_summaries"][0]
        self.assertEqual(day["nutrition"]["kcal"]["amount"]["value"], "120")
        self.assertEqual(self.worker.run_one(self.actor, parser, origin=source)["status"], "applied")
        self.assertEqual(len(self.calls), 1)
        self.assertEqual((self.count(db.food_entries), self.count(db.outbox)), (1, 1))

    def test_missing_dairy_percentage_stays_pending_even_with_provider_candidate(self):
        text = "Съела 100 г творога";source = self.source(text=text)
        result = self.worker.run_one(self.actor, self.parser(output=fixture(text)["output"]), origin=source)
        self.assertEqual((result["status"], result["reason"]), ("unresolved", "dairy_fat_missing"))
        self.assertEqual((self.count(db.food_entries), self.count(db.outbox)), (0, 0))

    def test_auth_and_invalid_response_fail_once_without_food_or_payload_in_job(self):
        for number, parser in enumerate((self.parser(status=401), self.parser(output={"secret": TEXT})), 1):
            source = self.source(number)
            result = self.worker.run_one(self.actor, parser, origin=source)
            self.assertEqual(result["status"], "failed")
            before = len(self.calls);self.worker.run_one(self.actor, parser, origin=source)
            self.assertEqual(len(self.calls), before)
        self.assertEqual((self.count(db.food_entries), self.count(db.outbox)), (0, 0))
        self.assertNotIn(TEXT, json.dumps(self.worker.status(self.actor)))
        self.assertNotIn("test-secret", json.dumps(self.worker.status(self.actor)))
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(sa.select(db.conversation_jobs.c.proposal)).scalars().all(), [None, None])

    def test_rate_limit_persists_delay_and_exhausts_three_attempts_without_sleeping(self):
        source = self.source();parser = self.parser(status=429, headers={"Retry-After": "120"})
        self.assertEqual(self.worker.run_one(self.actor, parser, origin=source)["status"], "retry")
        row = self.row(db.conversation_jobs)
        self.assertGreater((row["next_attempt_at"] - datetime.now(timezone.utc)).total_seconds(), 115)
        self.assertEqual(self.worker.run_one(self.actor, parser, origin=source)["status"], "waiting")
        self.assertEqual(len(self.calls), 1)
        self.due();self.assertEqual(self.worker.run_one(self.actor, parser, origin=source)["status"], "retry")
        self.due();self.assertEqual(self.worker.run_one(self.actor, parser, origin=source)["status"], "failed")
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(self.count(db.food_entries), 0)

    def test_rotated_key_can_retry_but_model_change_fences_unfinished_work(self):
        source = self.source()
        self.worker.run_one(self.actor, self.parser(status=503), origin=source)
        self.due()
        self.assertEqual(self.worker.run_one(self.actor, self.parser(key="rotated-key"), origin=source)["status"], "applied")
        source = self.source(2)
        self.worker.run_one(self.actor, self.parser(status=503), origin=source)
        self.due();before = len(self.calls)
        result = self.worker.run_one(self.actor, self.parser(model="changed/model"), origin=source)
        self.assertEqual(result["reason"], "interpretation_version_changed")
        self.assertEqual(len(self.calls), before)

    def test_prepared_command_resumes_after_provider_change_without_request(self):
        source = self.source()
        def crash(point):
            if point == "after_prepare":raise RuntimeError("synthetic crash")
        with self.assertRaises(RuntimeError):
            self.worker.run_one(self.actor, self.parser(), origin=source, fault=crash)
        result = self.worker.run_one(self.actor, self.parser(status=401, model="changed/model"), origin=source)
        self.assertEqual(result["status"], "applied")
        self.assertEqual((len(self.calls), self.count(db.food_entries), self.count(db.outbox)), (1, 1, 1))


if __name__ == "__main__":
    unittest.main()
