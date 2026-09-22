"""Private Telegram transport metadata, cursor, and delivery receipts.

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("inbox_updates", sa.Column("reply_to_message_id", sa.BigInteger()))
    op.add_column("inbox_updates", sa.Column("forwarded", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_check_constraint("positive_reply", "inbox_updates", "reply_to_message_id IS NULL OR reply_to_message_id > 0")
    op.add_column("outbox", sa.Column("next_attempt_at", sa.DateTime(timezone=True)))
    op.add_column("outbox", sa.Column("telegram_message_id", sa.BigInteger()))
    op.create_check_constraint("sent_message", "outbox", "telegram_message_id IS NULL OR (telegram_message_id > 0 AND status = 'sent')")
    op.create_table("telegram_poll_cursors",
        sa.Column("bot_id", sa.BigInteger(), primary_key=True),
        sa.Column("next_update_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.CheckConstraint("bot_id > 0 AND next_update_id >= 0", name="valid_cursor"))


def downgrade():
    op.drop_table("telegram_poll_cursors")
    op.drop_constraint("sent_message", "outbox", type_="check")
    op.drop_column("outbox", "telegram_message_id")
    op.drop_column("outbox", "next_attempt_at")
    op.drop_constraint("positive_reply", "inbox_updates", type_="check")
    op.drop_column("inbox_updates", "forwarded")
    op.drop_column("inbox_updates", "reply_to_message_id")
