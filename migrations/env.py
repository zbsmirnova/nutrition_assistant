"""Use the application's configured engine, or a connection passed by tests."""

from alembic import context

from nutrition_app.db import database_url, engine_for
from nutrition_app.schema import metadata


def run(connection):
    context.configure(connection=connection, target_metadata=metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(url=database_url(), target_metadata=metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
elif context.config.attributes.get("connection") is not None:
    run(context.config.attributes["connection"])
else:
    engine = engine_for()
    try:
        with engine.connect() as connection:
            run(connection)
    finally:
        engine.dispose()
