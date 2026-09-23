"""W003: real PostgreSQL recovery and controlled interpretation, no cloud calls."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Event
import unittest

from alembic import command as alembic_command
from alembic.config import Config
import sqlalchemy as sa
from sqlalchemy.exc import DBAPIError, IntegrityError

import test_food_service as food_tests
from nutrition_app import schema as db
from nutrition_app.conversation import ConversationWorker
from nutrition_app.conversation_demo import PRODUCT_NAME, TEXT, dairy_nutrition, fixture, run_conversation_demo
from nutrition_app.db import ROOT, migrate
from nutrition_app.demo import food_command, message, seed_product, seed_user
from nutrition_app.errors import NotFound
from nutrition_app.interpretation import SyntheticParser
from nutrition_app.service import FoodService


class ControlledParser:
    version = "w003-test-parser-v1"

    def __init__(self, output=None, callback=None):
        self.output = output if output is not None else fixture()["output"]
        self.callback = callback
        self.calls = 0
        self.requests = []

    def parse(self, request):
        self.calls += 1
        self.requests.append(request)
        if self.callback:
            self.callback(request)
        return self.output if isinstance(self.output, str) else json.dumps(self.output)


class ConversationWorkerTests(unittest.TestCase):
    cleanup_database = food_tests.FoodPersistenceTests.cleanup_database
    count = food_tests.FoodPersistenceTests.count
    row = food_tests.FoodPersistenceTests.row

    def setUp(self):
        food_tests.FoodPersistenceTests.setUp(self)
        self.other = self.seed
        self.seed = seed_user(self.engine, name=PRODUCT_NAME, food_kind="dairy",
                              declared_fat_percent="5", nutrition=dairy_nutrition())
        self.worker = ConversationWorker(self.engine)
        self.actor = self.seed.user_id

    def source(self, number=1, text=TEXT, **changes):
        msg = message(self.seed, number, text=text).model_copy(update=changes)
        return self.service.accept_message(self.actor, msg)

    def expire(self):
        with self.engine.begin() as connection:
            connection.execute(db.conversation_jobs.update().where(db.conversation_jobs.c.user_id == self.actor,
                db.conversation_jobs.c.status == "processing").values(lease_until=sa.func.now() - timedelta(seconds=1)))
            connection.execute(db.conversation_jobs.update().where(db.conversation_jobs.c.user_id == self.actor,
                db.conversation_jobs.c.status == "retry").values(next_attempt_at=sa.func.now() - timedelta(seconds=1)))

    def test_clear_message_saves_expected_nutrition_and_replays_once(self):
        origin = self.source()
        parser = ControlledParser()
        result = self.worker.run_one(self.actor, parser, origin=origin)
        self.assertEqual(result["status"], "applied")
        day = result["outcome"]["result"]["daily_summaries"][0]
        self.assertEqual({k: v["amount"]["value"] for k, v in day["nutrition"].items()},
                         {"kcal": "120", "protein_g": "16", "fat_g": "5", "carbs_g": "3"})
        self.assertEqual(self.source(), origin)
        self.assertEqual(self.worker.run_one(self.actor, parser, origin=origin)["status"], "applied")
        self.assertEqual(parser.calls, 1)
        self.assertEqual(self.count(db.food_entries), 1)
        self.assertEqual(self.count(db.outbox), 1)
        self.assertEqual(self.row(db.conversation_jobs)["proposal"], fixture()["output"])
        self.source(2)
        self.assertEqual(self.worker.run_one(self.actor, parser)["status"], "applied")
        self.assertEqual(self.count(db.food_entries), 2)
        self.assertEqual(self.worker.run_one(self.actor, parser), {"status": "idle"})

    def test_unknown_fat_is_pending_and_visible_in_later_day_totals(self):
        text = "Съела 100 г творога"
        origin = self.source(text=text)
        result = self.worker.run_one(self.actor, ControlledParser(fixture(text)["output"]), origin=origin)
        self.assertEqual((result["status"], result["reason"]), ("unresolved", "dairy_fat_missing"))
        self.assertEqual(self.count(db.food_entries), 0)
        self.assertEqual(self.count(db.outbox), 0)
        self.source(2)
        saved = self.worker.run_one(self.actor, ControlledParser())
        self.assertEqual(saved["outcome"]["result"]["daily_summaries"][0]["pending_food_actions"], 1)
        self.assertEqual(self.service.get_day(self.actor, date(2026, 9, 22)).entry_count, 1)

    def test_dairy_fat_reply_resumes_original_operation_once(self):
        original = self.source(text="Съела 100 г творога")
        initial = self.worker.run_one(self.actor, ControlledParser(fixture("Съела 100 г творога")["output"]),
                                      origin=original)
        self.assertEqual((initial["status"], initial["reason"]), ("unresolved", "dairy_fat_missing"))
        with self.engine.begin() as connection:
            pending = connection.execute(sa.select(db.conversation_jobs).where(
                db.conversation_jobs.c.user_id == self.actor,
                db.conversation_jobs.c.origin_update_id == original)).mappings().one()
            self.assertEqual(pending["pending_questions"], {"c1": {"q1": "nutrition"}})
            original_message_id = connection.execute(sa.select(db.inbox_updates.c.telegram_message_id).where(
                db.inbox_updates.c.id == original)).scalar_one()
        reply = self.source(2, text="5%", reply_to_message_id=original_message_id)
        answer = {"schema_version": "1.0", "actions": [{
            "kind": "answer_clarification", "action_id": "a1", "evidence": "5%",
            "depends_on": [], "unresolved": [],
            "pending": {"kind": "candidate", "candidate_ref": "c1", "candidate_kind": "pending"},
            "answers": [{"question_ref": "q1", "value": {"kind": "nutrition",
                "supplied_nutrition": {"kcal": None, "protein_g": None, "fat_g": "5", "carbs_g": None}}}],
        }]}
        parser = ControlledParser(answer)
        result = self.worker.run_one(self.actor, parser, origin=reply)
        self.assertEqual(result["status"], "applied")
        self.assertEqual(parser.requests[0].pending_questions, {"c1": {"q1": "nutrition"}})
        self.assertEqual(parser.requests[0].pending_candidates[0]["ref"], "c1")
        self.assertEqual(self.count(db.food_entries), 1)
        self.assertEqual(self.worker.run_one(self.actor, parser, origin=reply)["status"], "applied")
        with self.engine.begin() as connection:
            states = connection.execute(sa.select(db.conversation_jobs.c.status, db.conversation_jobs.c.reason).where(
                db.conversation_jobs.c.user_id == self.actor).order_by(db.conversation_jobs.c.created_at)).all()
        self.assertEqual(states, [("applied", "clarification_resolved"), ("applied", "command_applied")])
        self.assertEqual(self.count(db.food_entries), 1)

    def test_forward_and_reply_inputs_wait_without_calling_parser(self):
        parser = ControlledParser()
        for number, change in enumerate([{"forwarded": True}, {"reply_to_message_id": 88}], 1):
            origin = self.source(number, **change)
            self.assertEqual(self.worker.run_one(self.actor, parser, origin=origin)["reason"], "conversation_context_required")
        self.assertEqual(parser.calls, 0)
        self.assertEqual(self.count(db.food_entries), 0)

    def test_invalid_proposals_and_foreign_references_have_no_mutations(self):
        cases = ["not JSON", json.dumps({"schema_version": "1.0", "user_id": str(self.other.user_id), "actions": []})]
        bad = fixture()["output"]
        bad["actions"][0]["food"]["candidate_ref"] = "c99"
        cases.append(bad)
        for number, output in enumerate(cases, 1):
            origin = self.source(number)
            result = self.worker.run_one(self.actor, ControlledParser(output), origin=origin)
            self.assertEqual(result["status"], "rejected")
        with self.assertRaises(NotFound):
            self.worker.run_one(self.other.user_id, ControlledParser(), origin=origin)
        with self.assertRaises(NotFound):
            self.worker.status(self.other.user_id, origin)
        self.assertEqual(self.count(db.food_entries), 0)
        self.assertEqual(self.count(db.prepared_operations), 0)

    def test_nonlogging_and_unsupported_messages_do_not_block_new_food(self):
        plan = {"schema_version": "1.0", "actions": [{"kind": "non_logging", "action_id": "a1", "evidence": TEXT,
                "depends_on": [], "unresolved": [], "reason": "planned_food"}]}
        origin = self.source()
        self.assertEqual(self.worker.run_one(self.actor, ControlledParser(plan), origin=origin)["status"], "non_logging")
        multi = fixture()["output"]
        multi["actions"].append(dict(deepcopy(multi["actions"][0]), action_id="a2"))
        origin = self.source(2)
        self.assertEqual(self.worker.run_one(self.actor, ControlledParser(multi), origin=origin)["status"], "unsupported")
        self.source(3)
        self.assertEqual(self.worker.run_one(self.actor, ControlledParser())["status"], "applied")
        self.assertEqual(self.count(db.food_entries), 1)

    def test_provider_failures_are_bounded_redacted_and_do_not_block_other_inputs(self):
        origin = self.source()
        def failure(_):
            raise RuntimeError("secret-token and personal message payload must not escape")
        parser = ControlledParser(callback=failure)
        result = self.worker.run_one(self.actor, parser, origin=origin)
        self.assertEqual(result["status"], "retry")
        self.assertEqual(self.worker.run_one(self.actor, parser, origin=origin)["status"], "waiting")
        self.source(2)
        self.assertEqual(self.worker.run_one(self.actor, ControlledParser())["status"], "applied")
        for expected in ("retry", "failed"):
            self.expire()
            self.assertEqual(self.worker.run_one(self.actor, parser, origin=origin)["status"], expected)
        self.assertEqual(self.worker.run_one(self.actor, parser, origin=origin)["status"], "failed")
        self.assertEqual(parser.calls, 3)
        diagnostic = json.dumps(self.worker.status(self.actor))
        self.assertNotIn("secret-token", diagnostic)
        self.assertNotIn(TEXT, diagnostic)

    def test_parser_holds_no_user_lock_and_pins_pre_call_catalog_version(self):
        origin = self.source()
        def update_catalog(request):
            self.assertEqual([c["name"] for c in request.candidates], [PRODUCT_NAME])
            self.assertNotIn(str(self.other.version_id), repr(request))
            with self.engine.begin() as connection:
                connection.exec_driver_sql("SET LOCAL lock_timeout = '500ms'")
                FoodService._user(connection, self.actor)
                seed_product(connection, self.actor, product_id=self.seed.product_id, version_no=2,
                             name=PRODUCT_NAME, food_kind="dairy", declared_fat_percent="5")
        result = self.worker.run_one(self.actor, ControlledParser(callback=update_catalog), origin=origin)
        self.assertEqual(result["status"], "applied")
        self.assertEqual(self.row(db.food_components)["product_version_id"], self.seed.version_id)
        self.assertEqual(self.service.get_day(self.actor, date(2026, 9, 22)).nutrition.kcal.amount.value, "120")

    def test_competing_workers_and_expired_claim_cannot_replace_winning_interpretation(self):
        origin = self.source()
        entered, release = Event(), Event()
        first_output = fixture()["output"]
        first_output["actions"][0]["meal"] = "lunch"
        def pause(_):
            entered.set()
            if not release.wait(10):
                raise RuntimeError("test coordination timeout")
        with ThreadPoolExecutor(max_workers=2) as pool:
            future = pool.submit(self.worker.run_one, self.actor, ControlledParser(first_output, pause), origin=origin)
            try:
                self.assertTrue(entered.wait(5))
                self.assertEqual(self.worker.run_one(self.actor, ControlledParser(), origin=origin)["status"], "busy")
                self.expire()
                winner = fixture()["output"]
                winner["actions"][0]["meal"] = "dinner"
                self.assertEqual(self.worker.run_one(self.actor, ControlledParser(winner), origin=origin)["status"], "applied")
            finally:
                release.set()
            self.assertEqual(future.result(timeout=10)["status"], "lost_claim")
        self.assertEqual(self.row(db.food_entry_revisions)["meal"], "dinner")
        self.assertEqual(self.count(db.food_entries), 1)
        self.assertEqual(self.count(db.outbox), 1)

    def test_real_process_crashes_resume_before_and_after_frozen_command_and_domain_commit(self):
        points = ["after_claim", "after_parse", "after_prepare", "before_domain_commit", "after_domain_commit"]
        with tempfile.TemporaryDirectory(prefix="nutrition-w003-") as directory:
            path = Path(directory) / "fixture.json"
            path.write_text(json.dumps(fixture()))
            for number, point in enumerate(points, 1):
                with self.subTest(point=point):
                    origin = self.source(number)
                    result = subprocess.run([sys.executable, "-m", "nutrition_app", "conversation-run", "--user",
                        str(self.actor), "--source", str(origin), "--fixture", str(path), "--crash", point],
                        cwd=ROOT, capture_output=True, text=True, timeout=20,
                        env=dict(os.environ, NUTRITION_DATABASE_URL=self.url, NUTRITION_DB_SCHEMA=self.schema))
                    self.assertEqual(result.returncode, 77, result.stderr)
                    self.expire()
                    parser = SyntheticParser(fixture())
                    if point in {"after_prepare", "before_domain_commit", "after_domain_commit"}:
                        parser.parse = lambda _: self.fail("Frozen work must not be parsed again")
                    self.assertEqual(self.worker.run_one(self.actor, parser, origin=origin)["status"], "applied")
                    self.assertEqual(self.count(db.food_entries), number)
                    self.assertEqual(self.count(db.outbox), number)

    def test_freeze_failure_rolls_back_proposal_and_preparation_together(self):
        origin = self.source()
        with self.engine.begin() as connection:
            connection.exec_driver_sql("CREATE FUNCTION fail_prepare() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'fixture'; END $$")
            connection.exec_driver_sql("CREATE TRIGGER fail_prepare BEFORE INSERT ON prepared_operations FOR EACH ROW EXECUTE FUNCTION fail_prepare()")
        with self.assertRaises(DBAPIError):
            self.worker.run_one(self.actor, ControlledParser(), origin=origin)
        self.assertIsNone(self.row(db.conversation_jobs)["proposal"])
        self.assertEqual(self.count(db.prepared_operations), 0)
        self.assertEqual(self.count(db.food_entries), 0)
        with self.engine.begin() as connection:
            connection.exec_driver_sql("DROP TRIGGER fail_prepare ON prepared_operations")
        self.expire()
        self.assertEqual(self.worker.run_one(self.actor, ControlledParser(), origin=origin)["status"], "applied")

    def test_context_version_and_catalog_snapshot_survive_retry(self):
        origin = self.source()
        parser = ControlledParser(callback=lambda _: (_ for _ in ()).throw(RuntimeError("temporary")))
        self.worker.run_one(self.actor, parser, origin=origin)
        before = self.row(db.conversation_jobs)["context"]
        with self.engine.begin() as connection:
            seed_product(connection, self.actor, name="Additional product", food_kind="general")
        self.expire()
        replacement = ControlledParser()
        replacement.version = "different-parser"
        self.assertEqual(self.worker.run_one(self.actor, replacement, origin=origin)["reason"], "interpretation_version_changed")
        self.assertEqual(self.row(db.conversation_jobs)["context"], before)
        self.assertEqual(replacement.calls, 0)

    def test_source_timezone_midnight_and_dst_dates_survive_processing_delay(self):
        for number, (instant, hint, expected) in enumerate([
            ("2026-09-22T22:30:00+00:00", "вчера", "2026-09-22"),
            ("2026-10-25T00:30:00+00:00", None, "2026-10-25"),
            ("2026-10-25T01:30:00+00:00", None, "2026-10-25")], 1):
            text = ("Вчера " if hint else "") + TEXT
            origin = self.source(number, text, sent_at=datetime.fromisoformat(instant))
            parser = ControlledParser(fixture(text, date_hint=hint)["output"])
            result = self.worker.run_one(self.actor, parser, origin=origin)
            self.assertEqual(result["outcome"]["result"]["food_entries"][0]["effective_date"], expected)

    def test_upgrade_preserves_applied_and_prepared_work_and_marks_legacy_identity_unknown(self):
        sources = [self.source(n) for n in (1, 2, 3)]
        original = self.service.apply(self.actor, food_command(self.seed, sources[0], grams="100"))
        self.service.prepare(self.actor, food_command(self.seed, sources[1], grams="100"))
        config = Config(str(ROOT / "alembic.ini"))
        with self.engine.begin() as connection:
            config.attributes["connection"] = connection
            alembic_command.downgrade(config, "0003")
        migrate(self.engine)
        no_parse = ControlledParser(callback=lambda _: self.fail("Prepared/applied messages must not be parsed"))
        for origin in sources[:2]:
            self.assertEqual(self.worker.run_one(self.actor, no_parse, origin=origin)["status"], "applied")
        self.assertEqual(no_parse.calls, 0)
        self.assertEqual(self.service.execute(self.actor, food_command(self.seed, sources[0]).operation_id), original)
        self.assertEqual(self.worker.run_one(self.actor, ControlledParser(), origin=sources[2])["reason"], "catalog_identity_unclassified")
        self.assertEqual(self.count(db.food_entries), 2)
        self.assertEqual(self.count(db.outbox), 2)

    def test_database_constraints_reject_cross_owner_jobs_and_invalid_fat_metadata(self):
        origin = self.source()
        with self.assertRaises(IntegrityError), self.engine.begin() as connection:
            connection.execute(db.conversation_jobs.insert().values(user_id=self.other.user_id,
                origin_update_id=origin, status="ready"))
        with self.assertRaises(IntegrityError), self.engine.begin() as connection:
            seed_product(connection, self.actor, food_kind="dairy", declared_fat_percent="101")

    def test_synthetic_demo_delivers_russian_reply_and_is_repeatable(self):
        result = run_conversation_demo(self.engine)
        self.assertEqual(result["current_day"]["entry_count"], 1)
        self.assertIn("Ккал: 120", result["rendered_replies"][0])
        self.assertIn("Итого за 22.09.2026", result["rendered_replies"][0])
        replay = run_conversation_demo(self.engine)
        self.assertEqual(replay["current_day"]["entry_count"], 1)
        self.assertEqual(replay["delivery"], "idle")
        self.assertEqual(replay["rendered_replies"], [])


if __name__ == "__main__":
    unittest.main()
