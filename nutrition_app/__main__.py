"""Trusted local operator CLI; Telegram commands explicitly select real transport."""

import argparse
from datetime import date
import json
import os
from pathlib import Path
from uuid import UUID

from pydantic import TypeAdapter, ValidationError
from sqlalchemy.exc import DBAPIError

from nutrition_contracts.common import TimeZoneName

from .db import engine_for, migrate
from .conversation import ConversationWorker
from .conversation_demo import run_conversation_demo
from .catalog import create_product, create_recipe
from .interpretation import SyntheticParser
from .nebius import NebiusConfig, NebiusParser, run_synthetic_smoke
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
    sub.add_parser("conversation-demo", help="Synthetic text-to-food-to-reply exercise; no external calls")
    run = sub.add_parser("conversation-run", help="Process one source with a source-bound synthetic parser fixture")
    run.add_argument("--user", type=UUID, required=True)
    run.add_argument("--source", type=UUID, required=True)
    run.add_argument("--fixture", type=Path, required=True)
    run.add_argument("--crash", choices=["after_claim", "after_parse", "after_prepare", "before_domain_commit", "after_domain_commit"])
    status = sub.add_parser("conversation-status", help="Inspect processing status without printing message text")
    status.add_argument("--user", type=UUID, required=True)
    status.add_argument("--source", type=UUID)
    live = sub.add_parser("conversation-nebius", help="Explicitly send one inbox source to Nebius and validate its proposal")
    live.add_argument("--user", type=UUID, required=True)
    live.add_argument("--source", type=UUID, required=True)
    sub.add_parser("nebius-smoke", help="Send one fixed synthetic request to Nebius; no database reads or writes")
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
    product = sub.add_parser("product-create", help="Create one owner-scoped product from supplied nutrition values")
    product.add_argument("--user", type=UUID, required=True)
    product.add_argument("--name", required=True)
    product.add_argument("--kcal")
    product.add_argument("--protein-g")
    product.add_argument("--fat-g")
    product.add_argument("--carbs-g")
    product.add_argument("--nutrition-basis", choices=["per_100_g", "per_100_ml"], default="per_100_g")
    product.add_argument("--weight-basis", choices=["raw", "cooked", "as_sold"], default="as_sold")
    product.add_argument("--food-kind", choices=["general", "dairy"], default="general")
    product.add_argument("--declared-fat-percent")
    recipe = sub.add_parser("recipe-create", help="Create one owner-scoped recipe profile from supplied nutrition values")
    recipe.add_argument("--user", type=UUID, required=True)
    recipe.add_argument("--name", required=True)
    recipe.add_argument("--kcal")
    recipe.add_argument("--protein-g")
    recipe.add_argument("--fat-g")
    recipe.add_argument("--carbs-g")
    recipe.add_argument("--instructions")
    recipe.add_argument("--ingredients-json", help="JSON array of {name, amount, unit, weight_basis?} snapshots")
    link = sub.add_parser("telegram-link", help="Explicitly link a private Telegram account to an existing owner")
    link.add_argument("--user", type=UUID, required=True)
    link.add_argument("--bot-id", type=int, required=True)
    link.add_argument("--telegram-user-id", type=int, required=True)
    link.add_argument("--chat-id", type=int, required=True)
    poll = sub.add_parser("telegram-poll", help="Receive one batch of private text into the inbox; does not parse food")
    poll.add_argument("--timeout", type=int, default=25)
    sub.add_parser("telegram-send", help="Send one committed food response through the configured real bot")
    process = sub.add_parser("telegram-process", help="Poll, process one owner's next message, and send one reply")
    process.add_argument("--user", type=UUID, required=True)
    process.add_argument("--timeout", type=int, default=25)
    args = parser.parse_args()
    engine = None
    try:
        if args.action == "nebius-smoke":
            output = run_synthetic_smoke(NebiusParser(NebiusConfig.from_environment()))
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return
        # Check provider configuration before creating a database engine or job.
        live_parser = (NebiusParser(NebiusConfig.from_environment())
                       if args.action in {"conversation-nebius", "telegram-process"} else None)
        engine = engine_for()
        if args.action == "migrate":
            migrate(engine)
            output = {"migrations": "head"}
        elif args.action == "demo":
            output = run_demo(engine)
        elif args.action == "conversation-demo":
            output = run_conversation_demo(engine)
        elif args.action == "conversation-run":
            try:
                with args.fixture.open("rb") as stream:
                    raw = stream.read(256 * 1024 + 1)
                if len(raw) > 256 * 1024:
                    raise ValueError("Fixture too large")
                fixture_parser = SyntheticParser(json.loads(raw))
            except (OSError, ValueError, UnicodeError):
                raise ApplicationError("Cannot read a valid bounded synthetic fixture") from None
            def fault(point):
                if point == args.crash:
                    os._exit(77)
            output = ConversationWorker(engine).run_one(args.user, fixture_parser, origin=args.source, fault=fault)
            output.pop("outcome", None)  # Operational CLI output does not print personal food records.
        elif args.action == "conversation-status":
            output = ConversationWorker(engine).status(args.user, args.source)
        elif args.action == "conversation-nebius":
            output = ConversationWorker(engine).run_one(args.user, live_parser, origin=args.source)
            output.pop("outcome", None)
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
        elif args.action == "product-create":
            output = create_product(engine, args.user, name=args.name,
                                    nutrition={"kcal": args.kcal, "protein_g": args.protein_g,
                                               "fat_g": args.fat_g, "carbs_g": args.carbs_g},
                                    nutrition_basis=args.nutrition_basis, weight_basis=args.weight_basis,
                                    food_kind=args.food_kind, declared_fat_percent=args.declared_fat_percent)
        elif args.action == "recipe-create":
            ingredients = None
            if args.ingredients_json is not None:
                try:
                    ingredients = json.loads(args.ingredients_json)
                except (TypeError, json.JSONDecodeError):
                    raise ApplicationError("--ingredients-json must be valid JSON") from None
            output = create_recipe(engine, args.user, name=args.name,
                                   nutrition={"kcal": args.kcal, "protein_g": args.protein_g,
                                              "fat_g": args.fat_g, "carbs_g": args.carbs_g},
                                   ingredients=ingredients, cooking_instructions=args.instructions)
        elif args.action == "telegram-link":
            account = link_account(engine, args.user, args.bot_id, args.telegram_user_id, args.chat_id)
            output = {"account_id": str(account)}
        elif args.action in {"telegram-poll", "telegram-send", "telegram-process"}:
            try:
                bot_id = int(os.environ.get("NUTRITION_TELEGRAM_BOT_ID", ""))
            except ValueError:
                raise TelegramError("Set NUTRITION_TELEGRAM_BOT_ID locally") from None
            api = TelegramClient(os.environ.get("NUTRITION_TELEGRAM_TOKEN", ""), bot_id)
            api.verify(polling=args.action in {"telegram-poll", "telegram-process"})
            if args.action == "telegram-poll":
                output = TelegramPoller(engine, api).poll_once(timeout=args.timeout)
            elif args.action == "telegram-send":
                output = {"adapter": "telegram", "status": OutboxWorker(engine, bot_id=bot_id)
                          .dispatch_one(TelegramSender(api))}
            else:
                polled = TelegramPoller(engine, api).poll_once(timeout=args.timeout)
                processed = ConversationWorker(engine).run_one(args.user, live_parser)
                # Keep the operator output useful without echoing source text,
                # clarification wording, or the private outcome payload.
                process_keys = {"status", "reason", "origin_update_id"}
                safe_processed = {key: value for key, value in processed.items() if key in process_keys}
                output = {"adapter": "telegram", "poll": polled, "process": safe_processed,
                          "delivery": OutboxWorker(engine, bot_id=bot_id)
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
    except DBAPIError:
        print(json.dumps({"error": "database_unavailable", "message": "Database operation failed; retry after checking local database health"}))
        raise SystemExit(1) from None
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    main()
