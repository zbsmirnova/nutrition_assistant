"""Private Telegram boundary. Never derive application identity from message text."""

from datetime import datetime, timezone
import hashlib
import http.client
import json
import re
from typing import Callable, Protocol
from uuid import UUID

from pydantic import ValidationError
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from . import schema as db
from .errors import ApplicationError, Conflict
from .outbox import Delivery, DeliveryRejected, RetryLater
from .rendering import render_result
from .service import FoodService, IncomingMessage


class TelegramError(ApplicationError):
    code = "telegram_error"


class TelegramUnavailable(TelegramError):
    code = "telegram_unavailable"


class TelegramRejected(TelegramError):
    code = "telegram_rejected"

    def __init__(self, error_code: int, retry_after: int | None = None):
        super().__init__("Telegram rejected the request")
        self.error_code = error_code
        self.retry_after = retry_after


def positive_id(value) -> bool:
    return type(value) is int and 0 < value <= 9223372036854775807


class API(Protocol):
    bot_id: int

    def call(self, method: str, payload: dict, *, timeout: int = 15): ...


class TelegramClient:
    """Fixed HTTPS origin, no redirects; errors deliberately exclude token/URL/body."""

    def __init__(self, token: str, bot_id: int, *, request: Callable | None = None):
        if not isinstance(token, str) or not re.fullmatch(r"[0-9]+:[A-Za-z0-9_-]+", token) or not positive_id(bot_id):
            raise TelegramError("Configure a valid Telegram token and positive bot ID locally")
        self._token = token
        self.bot_id = bot_id
        self._request = request or self._https

    def _https(self, method, payload, timeout):
        connection = http.client.HTTPSConnection("api.telegram.org", timeout=timeout)
        try:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            connection.request("POST", f"/bot{self._token}/{method}", body=body,
                               headers={"Content-Type": "application/json"})
            response = connection.getresponse()
            raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError("Oversized response")
            return response.status, json.loads(raw)
        finally:
            connection.close()

    def call(self, method: str, payload: dict, *, timeout: int = 15):
        if method not in {"getMe", "getWebhookInfo", "getUpdates", "sendMessage"}:
            raise TelegramError("Unsupported Telegram method")
        try:
            status, response = self._request(method, payload, timeout)
        except Exception:
            raise TelegramUnavailable("Telegram request outcome is unavailable") from None
        if not isinstance(response, dict) or type(status) is not int:
            raise TelegramUnavailable("Invalid Telegram response")
        if status == 200 and response.get("ok") is True and "result" in response:
            return response["result"]
        code = response.get("error_code")
        if (response.get("ok") is False and type(code) is int and 400 <= code < 500
                and status in {200, code}):
            parameters = response.get("parameters")
            delay = parameters.get("retry_after") if isinstance(parameters, dict) else None
            if delay is not None and (not positive_id(delay) or delay > 2147483647):
                raise TelegramUnavailable("Invalid Telegram retry delay")
            raise TelegramRejected(code, delay)
        # A server error or malformed success cannot prove an external send failed.
        raise TelegramUnavailable("Telegram request outcome is uncertain")

    def verify(self, *, polling: bool = False):
        me = self.call("getMe", {})
        if not isinstance(me, dict) or type(me.get("id")) is not int or me["id"] != self.bot_id or me.get("is_bot") is not True:
            raise TelegramError("Telegram token does not match the configured bot")
        if polling:
            info = self.call("getWebhookInfo", {})
            if not isinstance(info, dict) or not isinstance(info.get("url"), str):
                raise TelegramUnavailable("Invalid Telegram webhook status")
            if info["url"]:
                raise TelegramError("Polling requires an unconfigured webhook; existing webhook was left intact")


def link_account(engine, actor: UUID, bot_id: int, telegram_user_id: int, chat_id: int) -> UUID:
    """Trusted local provisioning only. An existing mapping cannot be reassigned."""
    if not all(positive_id(value) for value in (bot_id, telegram_user_id, chat_id)):
        raise ApplicationError("Telegram IDs must be positive integers")
    with engine.begin() as connection:
        FoodService._user(connection, actor)
        existing = connection.execute(sa.select(db.telegram_accounts).where(
            db.telegram_accounts.c.bot_id == bot_id,
            sa.or_(db.telegram_accounts.c.telegram_user_id == telegram_user_id,
                   db.telegram_accounts.c.private_chat_id == chat_id))).mappings().all()
        if existing:
            if (len(existing) == 1 and existing[0]["user_id"] == actor
                    and existing[0]["telegram_user_id"] == telegram_user_id
                    and existing[0]["private_chat_id"] == chat_id):
                return existing[0]["id"]
            raise Conflict("Telegram identity is already linked")
        account = connection.execute(insert(db.telegram_accounts).values(user_id=actor, bot_id=bot_id,
            telegram_user_id=telegram_user_id, private_chat_id=chat_id).on_conflict_do_nothing()
            .returning(db.telegram_accounts.c.id)).scalar_one_or_none()
        if account is None:
            raise Conflict("Telegram identity is already linked")
        return account


class TelegramIngress:
    def __init__(self, engine, bot_id: int):
        self.engine = engine
        self.bot_id = bot_id
        self.service = FoodService(engine)

    def accept(self, update: dict) -> UUID | None:
        message = update.get("message")
        if not isinstance(message, dict):
            return None
        sender, chat = message.get("from"), message.get("chat")
        if not isinstance(sender, dict) or not isinstance(chat, dict):
            return None
        if (chat.get("type") != "private" or sender.get("is_bot") is not False
                or not positive_id(sender.get("id")) or not positive_id(chat.get("id"))):
            return None
        # Ignore non-text updates. They do not become food or a success response.
        if not isinstance(message.get("text"), str):
            return None
        with self.engine.connect() as connection:
            actor = connection.execute(sa.select(db.telegram_accounts.c.user_id).where(
                db.telegram_accounts.c.bot_id == self.bot_id,
                db.telegram_accounts.c.telegram_user_id == sender["id"],
                db.telegram_accounts.c.private_chat_id == chat["id"],
            )).scalar_one_or_none()
        if actor is None:
            return None
        reply = message.get("reply_to_message")
        reply_id = reply.get("message_id") if isinstance(reply, dict) else None
        try:
            if type(message.get("date")) is not int:
                raise ValueError("Invalid source timestamp")
            incoming = IncomingMessage(bot_id=self.bot_id, telegram_update_id=update["update_id"],
                telegram_message_id=message["message_id"], telegram_user_id=sender["id"],
                private_chat_id=chat["id"], sent_at=datetime.fromtimestamp(message["date"], timezone.utc),
                text=message["text"], reply_to_message_id=reply_id,
                forwarded="forward_origin" in message or "forward_date" in message)
        except (ValidationError, ValueError, OverflowError, OSError, KeyError):
            raise TelegramError("Invalid supported Telegram update; cursor not advanced") from None
        return self.service.accept_message(actor, incoming)


class TelegramPoller:
    def __init__(self, engine, api: API):
        self.engine = engine
        self.api = api
        self.ingress = TelegramIngress(engine, api.bot_id)
        self.lock_key = int.from_bytes(hashlib.sha256(f"nutrition-poll:{api.bot_id}".encode()).digest()[:8],
                                       "big", signed=True)

    def poll_once(self, *, timeout: int = 25, fault: Callable | None = None) -> dict:
        if type(timeout) is not int or not 0 <= timeout <= 30:
            raise TelegramError("Polling timeout must be between 0 and 30 seconds")
        with self.engine.connect() as guard:
            locked = guard.execute(sa.select(sa.func.pg_try_advisory_lock(self.lock_key))).scalar_one()
            guard.commit()
            if not locked:
                raise Conflict("Another poller is active for this bot")
            try:
                with guard.begin():
                    guard.execute(insert(db.telegram_poll_cursors).values(bot_id=self.api.bot_id)
                                  .on_conflict_do_nothing())
                    offset = guard.execute(sa.select(db.telegram_poll_cursors.c.next_update_id)
                        .where(db.telegram_poll_cursors.c.bot_id == self.api.bot_id)).scalar_one()
                updates = self.api.call("getUpdates", {"offset": offset, "timeout": timeout,
                    "limit": 100, "allowed_updates": ["message"]}, timeout=timeout + 10)
                if not isinstance(updates, list) or len(updates) > 100:
                    raise TelegramUnavailable("Invalid Telegram update batch")
                identifiers = []
                for update in updates:
                    if (not isinstance(update, dict) or type(update.get("update_id")) is not int
                            or not 0 <= update["update_id"] < 9223372036854775807):
                        raise TelegramUnavailable("Invalid Telegram update identity")
                    identifiers.append(update["update_id"])
                if len(set(identifiers)) != len(identifiers):
                    raise TelegramUnavailable("Duplicate identities in Telegram batch")
                accepted = 0
                for update in sorted(updates, key=lambda item: item["update_id"]):
                    accepted += self.ingress.accept(update) is not None
                if fault:
                    fault("before_checkpoint")
                next_offset = max(identifiers) + 1 if identifiers else offset
                with guard.begin():
                    guard.execute(db.telegram_poll_cursors.update()
                        .where(db.telegram_poll_cursors.c.bot_id == self.api.bot_id).values(next_update_id=next_offset))
                return {"received": len(updates), "accepted": accepted,
                        "ignored": len(updates) - accepted, "next_update_id": next_offset}
            finally:
                if guard.in_transaction():
                    guard.rollback()
                guard.execute(sa.select(sa.func.pg_advisory_unlock(self.lock_key)))
                guard.commit()


class TelegramSender:
    def __init__(self, api: API):
        self.api = api

    def send(self, delivery: Delivery) -> int:
        if delivery.bot_id != self.api.bot_id:
            raise DeliveryRejected("Delivery belongs to a different bot")
        try:
            text = render_result(delivery.payload)
        except (ValidationError, ValueError, TypeError):
            raise DeliveryRejected("Unsupported response payload") from None
        try:
            payload = {"chat_id": delivery.private_chat_id, "text": text,
                       "link_preview_options": {"is_disabled": True}}
            if delivery.reply_to_message_id is not None:
                payload["reply_parameters"] = {"message_id": delivery.reply_to_message_id,
                                                "allow_sending_without_reply": True}
            result = self.api.call("sendMessage", payload)
        except TelegramRejected as exc:
            if exc.error_code == 429:
                # A valid 429 proves rejection even if retry_after was omitted.
                raise RetryLater(exc.retry_after or 60) from None
            raise DeliveryRejected("Telegram rejected delivery") from None
        if (not isinstance(result, dict) or not positive_id(result.get("message_id"))
                or not isinstance(result.get("chat"), dict)
                or not positive_id(result["chat"].get("id"))
                or result["chat"].get("id") != delivery.private_chat_id):
            raise TelegramUnavailable("Telegram delivery receipt is uncertain")
        return result["message_id"]
