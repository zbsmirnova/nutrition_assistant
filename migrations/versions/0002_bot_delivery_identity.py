"""Enforce delivery uniqueness for the whole bot, retaining existing source rows.

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("inbox_updates", sa.Column("bot_id", sa.BigInteger(), nullable=True))
    # This is an administrative schema migration, not an ordinary source edit.
    op.execute("ALTER TABLE inbox_updates DISABLE TRIGGER immutable_snapshot")
    op.execute("""UPDATE inbox_updates AS i SET bot_id = a.bot_id
                  FROM telegram_accounts AS a
                  WHERE i.user_id = a.user_id AND i.telegram_account_id = a.id""")
    op.execute("ALTER TABLE inbox_updates ENABLE TRIGGER immutable_snapshot")
    op.alter_column("inbox_updates", "bot_id", nullable=False)
    op.create_unique_constraint("uq_telegram_account_bot", "telegram_accounts", ["user_id", "id", "bot_id"])
    op.drop_constraint("fk_inbox_updates_user_id_telegram_accounts", "inbox_updates", type_="foreignkey")
    op.create_foreign_key("fk_inbox_updates_user_id_telegram_accounts", "inbox_updates", "telegram_accounts",
                         ["user_id", "telegram_account_id", "bot_id"], ["user_id", "id", "bot_id"])
    op.drop_constraint("uq_inbox_transport_delivery", "inbox_updates", type_="unique")
    op.create_unique_constraint("uq_inbox_transport_delivery", "inbox_updates", ["bot_id", "telegram_update_id"])


def downgrade():
    op.drop_constraint("uq_inbox_transport_delivery", "inbox_updates", type_="unique")
    op.create_unique_constraint("uq_inbox_transport_delivery", "inbox_updates", ["telegram_account_id", "telegram_update_id"])
    op.drop_constraint("fk_inbox_updates_user_id_telegram_accounts", "inbox_updates", type_="foreignkey")
    op.create_foreign_key("fk_inbox_updates_user_id_telegram_accounts", "inbox_updates", "telegram_accounts",
                         ["user_id", "telegram_account_id"], ["user_id", "id"])
    op.drop_constraint("uq_telegram_account_bot", "telegram_accounts", type_="unique")
    op.drop_column("inbox_updates", "bot_id")
