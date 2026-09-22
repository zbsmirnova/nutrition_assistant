"""Internal local CLI. It is not a public authentication or Telegram interface."""

import argparse
from datetime import date
import json
import os
from uuid import UUID

from .db import engine_for, migrate
from .demo import run_demo
from .errors import ApplicationError
from .outbox import FakeSender, OutboxWorker
from .service import FoodService


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
