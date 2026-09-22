"""Claim/send/ack delivery boundary; no external send occurs inside a transaction."""

from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from . import schema as db


class DefinitelyNotSent(Exception):
    """An adapter can prove that the external service did not accept the send."""


class DeliveryRejected(DefinitelyNotSent):
    """Permanent rejection: an automatic retry would not resolve it."""


class RetryLater(DefinitelyNotSent):
    def __init__(self, seconds: int):
        super().__init__("Delivery rate limited")
        self.seconds = seconds


@dataclass(frozen=True)
class Delivery:
    id: UUID
    claim_token: UUID
    user_id: UUID
    private_chat_id: int
    payload: dict
    bot_id: int


class Sender(Protocol):
    def send(self, delivery: Delivery) -> int | None: ...


class OutboxWorker:
    def __init__(self, engine: Engine, *, lease_seconds: int = 60, bot_id: int | None = None):
        if lease_seconds < 1:
            raise ValueError("A positive delivery lease is required")
        self.engine = engine
        self.lease_seconds = lease_seconds
        self.bot_id = bot_id

    def _scope(self):
        if self.bot_id is None:
            return sa.true()  # Local fake/testing only; real CLI always scopes a bot.
        return db.outbox.c.telegram_account_id.in_(sa.select(db.telegram_accounts.c.id)
            .where(db.telegram_accounts.c.bot_id == self.bot_id))

    def claim(self) -> Delivery | None:
        with self.engine.begin() as connection:
            # A stale sender may already have sent. Keep the durable intent visible
            # as uncertain; do not blindly repeat an ambiguous external side effect.
            connection.execute(db.outbox.update().where(db.outbox.c.status == "sending",
                self._scope(), db.outbox.c.lease_until <= sa.func.now()).values(status="uncertain", claim_token=None, lease_until=None))
            row = connection.execute(sa.select(db.outbox).where(db.outbox.c.status == "pending", self._scope(),
                sa.or_(db.outbox.c.next_attempt_at.is_(None), db.outbox.c.next_attempt_at <= sa.func.now()))
                .order_by(db.outbox.c.created_at, db.outbox.c.id).limit(1)
                .with_for_update(skip_locked=True)).mappings().one_or_none()
            if row is None:
                return None
            token = uuid4()
            connection.execute(db.outbox.update().where(db.outbox.c.id == row["id"])
                .values(status="sending", claim_token=token,
                        lease_until=sa.func.now() + timedelta(seconds=self.lease_seconds), attempts=row["attempts"] + 1))
            account = connection.execute(sa.select(db.telegram_accounts).where(
                db.telegram_accounts.c.id == row["telegram_account_id"], db.telegram_accounts.c.user_id == row["user_id"],
            )).mappings().one()
            delivery = Delivery(id=row["id"], claim_token=token, user_id=row["user_id"],
                                private_chat_id=account["private_chat_id"], payload=row["payload"], bot_id=account["bot_id"])
        return delivery

    def _finish(self, delivery: Delivery, status: str, *, delay: int = 0, message_id: int | None = None) -> bool:
        with self.engine.begin() as connection:
            if status == "pending":
                # A proven pre-send failure can retry, but not forever.
                state = sa.case((db.outbox.c.attempts >= 3, "failed"), else_="pending")
            else:
                state = status
            result = connection.execute(db.outbox.update().where(
                db.outbox.c.id == delivery.id, db.outbox.c.user_id == delivery.user_id,
                db.outbox.c.status == "sending", db.outbox.c.claim_token == delivery.claim_token,
                db.outbox.c.lease_until > sa.func.now(),
            ).values(status=state, claim_token=None, lease_until=None,
                     next_attempt_at=sa.func.now() + timedelta(seconds=delay) if status == "pending" and delay else None,
                     telegram_message_id=message_id if status == "sent" else None,
                     sent_at=sa.func.now() if status == "sent" else None))
            return result.rowcount == 1

    def dispatch_one(self, sender: Sender) -> str:
        delivery = self.claim()
        if delivery is None:
            return "idle"
        try:
            message_id = sender.send(delivery)
        except DeliveryRejected:
            return "failed" if self._finish(delivery, "failed") else "claim_expired"
        except RetryLater as exc:
            return "retry_or_failed" if self._finish(delivery, "pending", delay=exc.seconds) else "claim_expired"
        except DefinitelyNotSent:
            return "retry_or_failed" if self._finish(delivery, "pending") else "claim_expired"
        except Exception:
            # Neither exception text nor payload is placed in operational output.
            self._finish(delivery, "uncertain")
            return "uncertain"
        return "sent" if self._finish(delivery, "sent", message_id=message_id) else "claim_expired"


class FakeSender:
    """Local harness only: captures committed payloads, never contacts Telegram."""

    def __init__(self):
        self.deliveries: list[Delivery] = []

    def send(self, delivery: Delivery) -> None:
        self.deliveries.append(delivery)
