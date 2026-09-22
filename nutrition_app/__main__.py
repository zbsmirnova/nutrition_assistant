"""Trusted local operator CLI; Telegram commands explicitly select real transport."""

import argparse
from datetime import date
import json
import os
from uuid import UUID

from pydantic import TypeAdapter, ValidationError

from nutrition_contracts.common import TimeZoneName

from .db import engine_for, migrate
from .demo import run_demo
from .errors import ApplicationError
from .outbox import FakeSender, OutboxWorker
from .service import FoodService
from . import schema as db
from .telegram import TelegramClient, TelegramError, TelegramPoller, TelegramSender, link_account


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("migrate")
    sub.add_parser("demo")
    sub.add_parser("db-info")
    execute = sub.add_parser("execute", help="Resume a prepared operation as a trusted local operator")
    execute.add_argument("--user", type=UUID, required=True)
    execute.add_argument("--operation", type=UUID, required=True)
    execute.add_argument("--crash", choices=["before_commit", "after_commit"], help="Local crash-test hook")
    day = sub.add_parser("day")
    day.add_argument("--user", type=UUID, required=True)
    day.add_argument("--date", type=date.fromisoformat, required=True)
    sub.add_parser("dispatch", help="Send one queued result to an in-memory fake, never Telegram")
    create = sub.add_parser("user-create", help="Create a local application owner; no public onboarding")
    create.add_argument("--time-zone", default="Europe/Berlin")
    link = sub.add_parser("telegram-link", help="Explicitly link a private Telegram account to an existing owner")
    link.add_argument("--user", type=UUID, required=True)
    link.add_argument("--bot-id", type=int, required=True)
    link.add_argument("--telegram-user-id", type=int, required=True)
    link.add_argument("--chat-id", type=int, required=True)
    poll = sub.add_parser("telegram-poll", help="Receive one batch of private text into the inbox; does not parse food")
    poll.add_argument("--timeout", type=int, default=25)
    sub.add_parser("telegram-send", help="Send one committed food response through the configured real bot")
    args = parser.parse_args()
    engine = engine_for()
    try:
        if args.action == "migrate":
            migrate(engine)
            output = {"migrations": "head"}
        elif args.action == "demo":
            output = run_demo(engine)
        elif args.action == "db-info":
            with engine.connect() as connection:
                output = {"postgresql": connection.exec_driver_sql("SHOW server_version").scalar_one(),
                          "schema": connection.exec_driver_sql("SELECT current_schema()").scalar_one()}
        elif args.action == "execute":
            def fault(point):
                if point == args.crash:
                    os._exit(77)  # Real process loss, without rollback/finally helpers.
            output = FoodService(engine).execute(args.user, args.operation, fault=fault).model_dump(mode="json")
        elif args.action == "day":
            output = FoodService(engine).get_day(args.user, args.date).model_dump(mode="json")
        elif args.action == "user-create":
            try:
                zone = TypeAdapter(TimeZoneName).validate_python(args.time_zone)
            except ValidationError:
                raise ApplicationError("Use a valid IANA time zone") from None
            with engine.begin() as connection:
                actor = connection.execute(db.users.insert().values(time_zone=zone).returning(db.users.c.id)).scalar_one()
            output = {"user_id": str(actor), "time_zone": zone}
        elif args.action == "telegram-link":
            account = link_account(engine, args.user, args.bot_id, args.telegram_user_id, args.chat_id)
            output = {"account_id": str(account)}
        elif args.action in {"telegram-poll", "telegram-send"}:
            try:
                bot_id = int(os.environ.get("NUTRITION_TELEGRAM_BOT_ID", ""))
            except ValueError:
                raise TelegramError("Set NUTRITION_TELEGRAM_BOT_ID locally") from None
            api = TelegramClient(os.environ.get("NUTRITION_TELEGRAM_TOKEN", ""), bot_id)
            api.verify(polling=args.action == "telegram-poll")
            if args.action == "telegram-poll":
                output = TelegramPoller(engine, api).poll_once(timeout=args.timeout)
            else:
                output = {"adapter": "telegram", "status": OutboxWorker(engine, bot_id=bot_id)
                          .dispatch_one(TelegramSender(api))}
        else:
            sender = FakeSender()
            status = OutboxWorker(engine).dispatch_one(sender)
            output = {"adapter": "fake", "status": status,
                      "deliveries": [{"id": str(item.id), "payload": item.payload} for item in sender.deliveries]}
        print(json.dumps(output, ensure_ascii=False, indent=2))
    except ApplicationError as exc:
        print(json.dumps({"error": exc.code, "message": str(exc)}))
        raise SystemExit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
