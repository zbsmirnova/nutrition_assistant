"""Long-running private Telegram pilot runner."""

from __future__ import annotations

import logging
import signal
import time
from threading import Event
from uuid import UUID

from .conversation import ConversationWorker
from .food_sources import lookup_from_environment
from .nebius import NebiusConfig, NebiusParser
from .outbox import OutboxWorker
from .telegram import TelegramClient, TelegramPoller, TelegramSender


log = logging.getLogger("nutrition_app.runner")


class PilotRunner:
    """Run exactly one private poll/process/send loop.

    The loop deliberately processes one durable inbox job per iteration. The
    database claims and Telegram poll lock provide recovery and single-poller
    protection across restarts.
    """

    def __init__(self, engine, *, actor: UUID, bot_id: int, token: str,
                 poll_timeout: int = 25, idle_delay: float = 1.0,
                 max_backoff: float = 60.0, sleep=time.sleep):
        if not 0 <= poll_timeout <= 30:
            raise ValueError("poll_timeout must be between 0 and 30")
        if idle_delay < 0 or max_backoff < idle_delay:
            raise ValueError("invalid runner delays")
        self.engine = engine
        self.actor = actor
        self.poll_timeout = poll_timeout
        self.idle_delay = idle_delay
        self.max_backoff = max_backoff
        self.sleep = sleep
        self.stop = Event()
        self.api = TelegramClient(token, bot_id)
        self.poller = TelegramPoller(engine, self.api)
        self.parser = NebiusParser(NebiusConfig.from_environment())
        self.worker = ConversationWorker(engine, food_lookup=lookup_from_environment())
        self.sender = OutboxWorker(engine, bot_id=bot_id)

    def request_stop(self, *_args):
        self.stop.set()

    def install_signal_handlers(self):
        signal.signal(signal.SIGTERM, self.request_stop)
        signal.signal(signal.SIGINT, self.request_stop)

    def run(self):
        self.api.verify(polling=True)
        backoff = self.idle_delay
        while not self.stop.is_set():
            try:
                poll = self.poller.poll_once(timeout=self.poll_timeout)
                processed = self.worker.run_one(self.actor, self.parser)
                delivery = self.sender.dispatch_one(TelegramSender(self.api))
                log.info("pilot_iteration poll_received=%s poll_accepted=%s process_status=%s delivery_status=%s",
                         poll.get("received", 0), poll.get("accepted", 0),
                         processed.get("status"), delivery)
                backoff = self.idle_delay
                if self.stop.wait(backoff):
                    break
            except Exception:
                # Details may contain credentials, message text, or provider
                # payloads. Keep the log useful without echoing the exception.
                log.error("pilot_iteration_failed; retrying")
                if self.stop.wait(backoff):
                    break
                backoff = min(self.max_backoff, max(2.0, backoff * 2 or 2.0))
