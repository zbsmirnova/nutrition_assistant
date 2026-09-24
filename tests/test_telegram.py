"""Transport protocol and Russian-rendering checks; no network calls."""

import json
from pathlib import Path
import unittest
from uuid import uuid4

from nutrition_app.outbox import Delivery, DeliveryRejected, RetryLater
from nutrition_app.rendering import render_clarification_result, render_food_result
from nutrition_app.telegram import TelegramClient, TelegramError, TelegramRejected, TelegramSender, TelegramUnavailable


def outcome():
    return json.loads((Path(__file__).resolve().parents[1] /
        "contracts/v1/examples/01_add_food.json").read_text())["results"][0]


def delivery(*, bot_id=101, chat_id=789):
    return Delivery(id=uuid4(), claim_token=uuid4(), user_id=uuid4(), private_chat_id=chat_id,
                    payload=outcome(), bot_id=bot_id)


class TelegramProtocolTests(unittest.TestCase):
    def test_bot_identity_and_webhook_are_verified_without_mutation(self):
        calls = []
        def request(method, payload, timeout):
            calls.append(method)
            result = {"id": 101, "is_bot": True} if method == "getMe" else {"url": "https://example.invalid/hook"}
            return 200, {"ok": True, "result": result}
        client = TelegramClient("101:synthetic", 101, request=request)
        with self.assertRaises(TelegramError):
            client.verify(polling=True)
        self.assertEqual(calls, ["getMe", "getWebhookInfo"])
        wrong = TelegramClient("101:synthetic", 202, request=request)
        with self.assertRaises(TelegramError):
            wrong.verify()

    def test_token_is_not_in_repr_or_errors(self):
        token = "101:synthetic_private_value"
        def request(*args):
            raise OSError(token + " sensitive message")
        client = TelegramClient(token, 101, request=request)
        with self.assertRaises(TelegramUnavailable) as raised:
            client.call("sendMessage", {"text": "sensitive message"})
        self.assertNotIn(token, repr(client) + str(raised.exception))
        self.assertNotIn("sensitive message", str(raised.exception))
        self.assertTrue(raised.exception.__suppress_context__)

    def test_rejection_does_not_expose_server_description(self):
        client = TelegramClient("101:synthetic", 101, request=lambda *args: (
            403, {"ok": False, "error_code": 403, "description": "private details"}))
        with self.assertRaises(TelegramRejected) as raised:
            client.call("sendMessage", {})
        self.assertEqual(raised.exception.error_code, 403)
        self.assertNotIn("private details", str(raised.exception))

    def test_server_error_and_invalid_success_are_uncertain(self):
        for status, body in [(500, {"ok": False, "error_code": 500}), (200, {"ok": True}),
                             (302, {"ok": True, "result": {}}), (200, []), (200, {"ok": 1, "result": {}})]:
            with self.subTest(status=status, body=body), self.assertRaises(TelegramUnavailable):
                TelegramClient("101:synthetic", 101, request=lambda *args: (status, body)).call("sendMessage", {})

    def test_sender_uses_plain_text_and_disables_link_previews(self):
        calls = []
        def request(method, payload, timeout):
            calls.append((method, payload))
            return 200, {"ok": True, "result": {"message_id": 7, "chat": {"id": 789}}}
        item = delivery()
        item.payload["result"]["food_entries"][0]["description"] = "<b>суп</b> https://example.invalid"
        self.assertEqual(TelegramSender(TelegramClient("101:synthetic", 101, request=request)).send(item), 7)
        method, payload = calls[0]
        self.assertEqual(method, "sendMessage")
        self.assertNotIn("parse_mode", payload)
        self.assertTrue(payload["link_preview_options"]["is_disabled"])
        self.assertEqual(payload["chat_id"], 789)
        self.assertIn("Ккал: 175", payload["text"])
        self.assertIn("Итого за сегодня:", payload["text"])
        self.assertNotIn("Жиры, г:", payload["text"])

    def test_sender_replies_to_the_triggering_message_when_available(self):
        calls = []
        def request(method, payload, timeout):
            calls.append(payload)
            return 200, {"ok": True, "result": {"message_id": 7, "chat": {"id": 789}}}
        item = Delivery(id=uuid4(), claim_token=uuid4(), user_id=uuid4(), private_chat_id=789,
                        payload=outcome(), bot_id=101, reply_to_message_id=42)
        TelegramSender(TelegramClient("101:synthetic", 101, request=request)).send(item)
        self.assertEqual(calls[0]["reply_parameters"],
                         {"message_id": 42, "allow_sending_without_reply": True})

    def test_cross_bot_send_is_rejected_before_api_call(self):
        client = TelegramClient("101:synthetic", 101, request=lambda *args: self.fail("must not send"))
        with self.assertRaises(DeliveryRejected):
            TelegramSender(client).send(delivery(bot_id=202))

    def test_rate_limit_and_permanent_failure_are_distinct(self):
        for code, error in [(429, RetryLater), (400, DeliveryRejected), (403, DeliveryRejected)]:
            with self.subTest(code=code):
                client = TelegramClient("101:synthetic", 101, request=lambda *args: (
                    code, {"ok": False, "error_code": code, "parameters": {"retry_after": 47}}))
                with self.assertRaises(error) as raised:
                    TelegramSender(client).send(delivery())
                if code == 429:
                    self.assertEqual(raised.exception.seconds, 47)
        long_delay = TelegramClient("101:synthetic", 101, request=lambda *args: (
            429, {"ok": False, "error_code": 429, "parameters": {"retry_after": 90000}}))
        with self.assertRaises(RetryLater) as raised:
            TelegramSender(long_delay).send(delivery())
        self.assertEqual(raised.exception.seconds, 90000)

    def test_invalid_or_wrong_chat_receipt_does_not_claim_success(self):
        for receipt in [{"message_id": True, "chat": {"id": 789}}, {"message_id": 3, "chat": {"id": 999}}, {}]:
            client = TelegramClient("101:synthetic", 101, request=lambda *args: (200, {"ok": True, "result": receipt}))
            with self.subTest(receipt=receipt), self.assertRaises(TelegramUnavailable):
                TelegramSender(client).send(delivery())
        for invalid_chat in (True, 1.0, "1"):
            client = TelegramClient("101:synthetic", 101, request=lambda *args: (
                200, {"ok": True, "result": {"message_id": 7, "chat": {"id": invalid_chat}}}))
            with self.subTest(chat_id=invalid_chat), self.assertRaises(TelegramUnavailable):
                TelegramSender(client).send(delivery(chat_id=1))


class RussianReplyTests(unittest.TestCase):
    def test_estimated_quantity_is_visible_in_acknowledgment(self):
        payload = outcome()
        payload["result"]["food_entries"][0]["estimated"] = True
        text = render_food_result(payload)
        self.assertIn("по вашему предположению", text)

    def test_unknown_partial_and_zero_are_not_conflated(self):
        payload = outcome()
        entry = payload["result"]["food_entries"][0]
        day = payload["result"]["daily_summaries"][0]
        entry["nutrition"]["fat_g"] = None
        day["nutrition"]["fat_g"] = {"kind": "unknown", "unknown_components": 1}
        entry["nutrition"]["protein_g"] = {"value": "0", "lower": None, "upper": None}
        day["nutrition"]["protein_g"]["amount"]["value"] = "0"
        text = render_food_result(payload)
        self.assertNotIn("Жиры, г:", text)
        self.assertNotIn("Углеводы, г:", text)
        self.assertEqual(text.count("Белки, г: 0"), 2)
        day["component_count"] = 2
        for key in day["nutrition"]:
            day["nutrition"][key] = {"kind": "partial", "known_subtotal": "10",
                                      "known_components": 1, "unknown_components": 1}
        self.assertIn("10 — известная часть, есть пропуски", render_food_result(payload))

    def test_long_multiline_description_does_not_hide_totals_or_exceed_limit(self):
        payload = outcome()
        payload["result"]["food_entries"][0]["description"] = "🍲\n" * 7000
        text = render_food_result(payload)
        self.assertLess(len(text.encode("utf-16-le")) // 2, 4000)
        self.assertIn("Итого за сегодня:", text)
        self.assertNotIn("на момент записи", text)
        self.assertNotIn("🍲\n🍲", text)

    def test_unsupported_outcome_is_not_presented_as_saved(self):
        payload = outcome()
        payload["result"]["food_entries"][0]["change"] = "deleted"
        payload["result"]["food_entries"][0]["nutrition"] = None
        with self.assertRaises(ValueError):
            render_food_result(payload)

    def test_corrected_food_outcome_is_rendered_as_an_update(self):
        payload = outcome()
        payload["result"]["food_entries"][0]["change"] = "corrected"
        text = render_food_result(payload)
        self.assertTrue(text.startswith("Исправлено: мой суп"))
        self.assertIn("Итого за сегодня:", text)

    def test_clarification_outcome_is_rendered_as_a_question(self):
        payload = {"result": {
            "schema_version": "1.0", "operation_id": str(uuid4()), "outcome": "needs_clarification",
            "pending_action_id": str(uuid4()), "pending_revision": 1, "effective_date": "2026-09-22",
            "questions": [{"question_ref": "q1", "field": "fat_percent",
                           "prompt": "Укажите процент жирности творога.", "answer_kind": "nutrition", "choices": []}],
            "previously_applied_operation_ids": [],
        }}
        self.assertEqual(render_clarification_result(payload), "Укажите процент жирности творога.")
