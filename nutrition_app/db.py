"""PostgreSQL connections and versioned migrations; no implicit production URL."""

import os
from pathlib import Path
import re

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url


ROOT = Path(__file__).resolve().parents[1]
LOCAL_DATABASE_URL = "postgresql+psycopg://nutrition:nutrition_local_dev@127.0.0.1:55432/nutrition_dev"


def database_url() -> str:
    return os.environ.get("NUTRITION_DATABASE_URL", LOCAL_DATABASE_URL)


def engine_for(url: str | None = None, *, schema: str | None = None) -> Engine:
    parsed = make_url(url or database_url())
    if parsed.drivername != "postgresql+psycopg":
        raise ValueError("Use the postgresql+psycopg driver")
    schema = schema or os.environ.get("NUTRITION_DB_SCHEMA")
    connect_args = {"connect_timeout": 5}
    if schema:
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", schema):
            raise ValueError("Invalid database schema name")
        # Do not fall back to public: isolated tests must never see another schema's
        # version table or food rows when their own schema is still empty.
        connect_args["options"] = f"-csearch_path={schema}"
    return create_engine(parsed, connect_args=connect_args, pool_pre_ping=True, hide_parameters=True)


def migrate(engine: Engine) -> None:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
