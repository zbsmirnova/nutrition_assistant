"""W002: synthetic Telegram boundary, real PostgreSQL, no external messages."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
import os
import subprocess
import sys
from threading import Event
import unittest

from alembic import command as alembic_command
from alembic.config import Config
import sqlalchemy as sa

import test_food_service as food_tests
from nutrition_app import schema as db
from nutrition_app.db import ROOT, engine_for, migrate
from nutrition_app.demo import food_command, message, seed_user
from nutrition_app.errors import Conflict
from nutrition_app.outbox import OutboxWorker
from nutrition_app.service import FoodService, digest
from nutrition_app.telegram import TelegramClient, TelegramError, TelegramIngress, TelegramPoller, TelegramSender, link_account


def telegram_update(seed, number=1):
    msg = message(seed, number)
    return {"update_id": number, "message": {"message_id": number,
        "from": {"id": seed.telegram_user_id, "is_bot": False},
        "chat": {"id": seed.telegram_user_id, "type": "private"},
        "date": int(msg.sent_at.timestamp()), "text": msg.text}}


class FixtureAPI:
    bot_id = 101

    def __init__(self, updates=()):
        self.updates = list(updates)
        self.calls = []

    def call(self, method, payload, *, timeout=15):
        self.calls.append((method, payload))
        if method == "getUpdates":
            return self.updates
        if method == "sendMessage":
            return {"message_id": 9001, "chat": {"id": payload["chat_id"]}}
        raise AssertionError(method)


class TelegramTransportTests(unittest.TestCase):
    setUp = food_tests.FoodPersistenceTests.setUp
    cleanup_database = food_tests.FoodPersistenceTests.cleanup_database
    count = food_tests.FoodPersistenceTests.count
    row = food_tests.FoodPersistenceTests.row
    command = food_tests.FoodPersistenceTests.command

    def test_ingress_resolves_account_and_preserves_context_without_food(self):
        update = telegram_update(self.seed)
        update["message"].update(reply_to_message={"message_id": 77}, forward_origin={"type": "hidden_user"},
                                  text="user_id=another-user; вчера 125 г супа")
        ingress = TelegramIngress(self.engine, 101)
        source = ingress.accept(update)
        self.assertEqual(ingress.accept(update), source)
        row = self.row(db.inbox_updates)
        self.assertEqual(row["user_id"], self.seed.user_id)
        self.assertEqual(row["reply_to_message_id"], 77)
        self.assertTrue(row["forwarded"])
        self.assertEqual(row["source_time_zone"], "Europe/Berlin")
        self.assertEqual(row["source_sent_at"], message(self.seed).sent_at)
        self.assertEqual(self.count(db.food_entries), 0)
        self.assertEqual(self.count(db.outbox), 0)

    def test_foreign_accounts_groups_bots_media_and_edits_create_no_records(self):
        updates = []
        for changed in ["foreign", "group", "bot", "media", "edited"]:
            item = telegram_update(self.seed)
            if changed == "foreign": item["message"]["from"]["id"] += 1
            if changed == "group": item["message"]["chat"]["type"] = "group"
            if changed == "bot": item["message"]["from"]["is_bot"] = True
            if changed == "media": item["message"].pop("text")
            if changed == "edited": item["edited_message"] = item.pop("message")
            item["update_id"] = len(updates) + 1
            updates.append(item)
        result = TelegramPoller(self.engine, FixtureAPI(updates)).poll_once(timeout=0)
        self.assertEqual(result, {"received": 5, "accepted": 0, "ignored": 5, "next_update_id": 6})
        self.assertEqual(self.count(db.inbox_updates), 0)
        self.assertEqual(self.count(db.food_entries), 0)

    def test_supported_malformed_update_does_not_advance_cursor(self):
        update = telegram_update(self.seed)
        update["message"]["date"] = True
        with self.assertRaises(TelegramError):
            TelegramPoller(self.engine, FixtureAPI([update])).poll_once(timeout=0)
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(sa.select(db.telegram_poll_cursors.c.next_update_id)).scalar_one(), 0)
        self.assertEqual(self.count(db.inbox_updates), 0)

    def test_new_identical_text_and_batch_order_are_preserved(self):
        api = FixtureAPI([telegram_update(self.seed, 2), telegram_update(self.seed, 1)])
        poller = TelegramPoller(self.engine, api)
        self.assertEqual(poller.poll_once(timeout=0)["next_update_id"], 3)
        self.assertEqual(self.count(db.inbox_updates), 2)
        api.updates = []
        poller.poll_once(timeout=0)
        self.assertEqual(api.calls[-1][1]["offset"], 3)

    def test_real_process_loss_before_checkpoint_replays_one_durable_source(self):
        script = '''
import json, os, sys
from nutrition_app.db import engine_for
from nutrition_app.telegram import TelegramPoller
class API:
    bot_id = 101
    def call(self, *args, **kwargs): return [update]
update = json.load(sys.stdin)
TelegramPoller(engine_for(), API()).poll_once(timeout=0, fault=lambda point: os._exit(77))
'''
        update = telegram_update(self.seed, 41)
        process = subprocess.run([sys.executable, "-c", script], input=json.dumps(update), text=True,
            capture_output=True, cwd=ROOT, timeout=20,
            env=dict(os.environ, NUTRITION_DATABASE_URL=self.url, NUTRITION_DB_SCHEMA=self.schema))
        self.assertEqual(process.returncode, 77, process.stderr)
        original = self.row(db.inbox_updates)["id"]
        api = FixtureAPI([update])
        self.assertEqual(TelegramPoller(self.engine, api).poll_once(timeout=0)["next_update_id"], 42)
        self.assertEqual(api.calls[0][1]["offset"], 0)
        self.assertEqual(self.row(db.inbox_updates)["id"], original)
        self.assertEqual(self.count(db.inbox_updates), 1)

    def test_concurrent_poller_cannot_acknowledge_an_inflight_batch(self):
        started, release = Event(), Event()
        class BlockingAPI(FixtureAPI):
            def call(inner, *args, **kwargs):
                started.set()
                if not release.wait(timeout=10): raise TimeoutError("test coordination failed")
                return []
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(TelegramPoller(self.engine, BlockingAPI()).poll_once, timeout=0)
            self.assertTrue(started.wait(timeout=10))
            try:
                competing = FixtureAPI()
                with self.assertRaises(Conflict):
                    TelegramPoller(self.engine, competing).poll_once(timeout=0)
                self.assertEqual(competing.calls, [])
            finally:
                release.set()
            future.result(timeout=10)

    def test_link_is_idempotent_and_never_reassigns_another_owner(self):
        self.assertEqual(link_account(self.engine, self.seed.user_id, 101,
                         self.seed.telegram_user_id, self.seed.telegram_user_id), self.seed.account_id)
        other = seed_user(self.engine)
        with self.assertRaises(Conflict):
            link_account(self.engine, other.user_id, 101, self.seed.telegram_user_id, self.seed.telegram_user_id)
        self.assertEqual(self.row(db.telegram_accounts)["id"], self.seed.account_id)

    def test_populated_upgrade_keeps_legacy_delivery_hash_and_food_outcome(self):
        original = self.service.apply(self.seed.user_id, self.command())
        source = self.row(db.inbox_updates)
        legacy_payload = message(self.seed).model_dump(mode="json", exclude={"reply_to_message_id", "forwarded"})
        legacy_payload["sent_at"] = message(self.seed).sent_at.isoformat()
        self.assertEqual(source["payload_hash"], digest(legacy_payload))
        config = Config(str(ROOT / "alembic.ini"))
        with self.engine.begin() as connection:
            config.attributes["connection"] = connection
            alembic_command.downgrade(config, "0002")
        migrate(self.engine)
        self.assertEqual(self.service.apply(self.seed.user_id, self.command()), original)
        self.assertEqual(self.row(db.inbox_updates)["id"], source["id"])
        self.assertEqual(self.row(db.outbox)["payload"], original.model_dump(mode="json"))

    def test_ingress_resolved_command_and_sender_use_committed_result(self):
        api = FixtureAPI([telegram_update(self.seed)])
        TelegramPoller(self.engine, api).poll_once(timeout=0)
        source = self.row(db.inbox_updates)["id"]
        # Explicit fixture command stands in for a future validated resolver.
        self.service.apply(self.seed.user_id, food_command(self.seed, source))
        worker = OutboxWorker(self.engine, bot_id=101)
        self.assertEqual(worker.dispatch_one(TelegramSender(api)), "sent")
        self.assertEqual(worker.dispatch_one(TelegramSender(api)), "idle")
        sends = [payload for method, payload in api.calls if method == "sendMessage"]
        self.assertEqual(len(sends), 1)
        self.assertIn("Ккал: 250", sends[0]["text"])
        self.assertEqual(self.row(db.outbox)["telegram_message_id"], 9001)
        self.assertEqual(self.count(db.food_entries), 1)

    def test_claiming_and_expiry_are_scoped_to_the_configured_bot(self):
        self.service.apply(self.seed.user_id, self.command())
        other = seed_user(self.engine)
        with self.engine.begin() as connection:
            connection.execute(db.telegram_accounts.update().where(db.telegram_accounts.c.user_id == other.user_id)
                               .values(bot_id=202))
        msg = message(other)
        msg.bot_id = 202
        source = self.service.accept_message(other.user_id, msg)
        self.service.apply(other.user_id, food_command(other, source))
        foreign_worker = OutboxWorker(self.engine, bot_id=202)
        foreign = foreign_worker.claim()
        with self.engine.begin() as connection:
            connection.execute(db.outbox.update().where(db.outbox.c.id == foreign.id)
                               .values(lease_until=sa.func.now() - timedelta(seconds=1)))
        worker = OutboxWorker(self.engine, bot_id=101)
        self.assertEqual(worker.dispatch_one(TelegramSender(FixtureAPI())), "sent")
        self.assertIsNone(worker.claim())
        with self.engine.connect() as connection:
            self.assertEqual(connection.execute(sa.select(db.outbox.c.status)
                .where(db.outbox.c.id == foreign.id)).scalar_one(), "sending")

    def test_rate_limit_waits_and_then_stops_after_bounded_attempts(self):
        self.service.apply(self.seed.user_id, self.command())
        client = TelegramClient("101:synthetic", 101, request=lambda *args: (
            429, {"ok": False, "error_code": 429, "parameters": {"retry_after": 120}}))
        worker = OutboxWorker(self.engine, bot_id=101)
        for attempt in range(1, 4):
            self.assertEqual(worker.dispatch_one(TelegramSender(client)), "retry_or_failed")
            row = self.row(db.outbox)
            self.assertEqual(row["attempts"], attempt)
            self.assertEqual(worker.dispatch_one(TelegramSender(client)), "idle")
            if attempt < 3:
                with self.engine.begin() as connection:
                    remaining = connection.execute(sa.select(db.outbox.c.next_attempt_at - sa.func.now())).scalar_one()
                    self.assertGreater(remaining.total_seconds(), 110)
                    connection.execute(db.outbox.update().values(next_attempt_at=sa.func.now() - timedelta(seconds=1)))
        self.assertEqual(self.row(db.outbox)["status"], "failed")

    def test_permanent_rejection_and_ambiguous_transport_have_different_states(self):
        for index, status in enumerate((403, 500), start=1):
            self.service.apply(self.seed.user_id, self.command(index))
            client = TelegramClient("101:synthetic", 101, request=lambda *args: (
                status, {"ok": False, "error_code": status, "description": "not logged"}))
            worker = OutboxWorker(self.engine, bot_id=101)
            self.assertEqual(worker.dispatch_one(TelegramSender(client)), "failed" if status == 403 else "uncertain")
            self.assertEqual(worker.dispatch_one(TelegramSender(client)), "idle")
        self.assertEqual(self.count(db.food_entries), 2)
