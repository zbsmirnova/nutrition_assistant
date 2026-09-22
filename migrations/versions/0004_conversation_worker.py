"""Durable interpretation work and versioned product identity.

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    # NULL preserves the fact that legacy catalogs have not been classified.
    op.add_column("product_versions", sa.Column("food_kind", sa.Text()))
    op.add_column("product_versions", sa.Column("declared_fat_percent", sa.Numeric(5, 2)))
    op.create_check_constraint("food_kind", "product_versions",
                               "food_kind IS NULL OR food_kind IN ('general','dairy')")
    op.create_check_constraint("declared_fat", "product_versions",
        "declared_fat_percent IS NULL OR (food_kind IS NOT NULL AND food_kind = 'dairy' "
        "AND declared_fat_percent >= 0 AND declared_fat_percent <= 100)")
    op.create_table("conversation_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "id"),
        sa.Column("origin_update_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("pending_food_date", sa.Date()),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("claim_token", UUID(as_uuid=True)),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("context", JSONB(none_as_null=True)),
        sa.Column("proposal", JSONB(none_as_null=True)),
        sa.ForeignKeyConstraint(["user_id", "origin_update_id"], ["inbox_updates.user_id", "inbox_updates.id"]),
        sa.UniqueConstraint("user_id", "origin_update_id", name="uq_conversation_origin"),
        sa.CheckConstraint("attempts >= 0", name="nonnegative_attempts"),
        sa.CheckConstraint("status IN ('processing','ready','retry','applied','non_logging','unresolved',"
                           "'unsupported','rejected','failed')", name="status"),
        sa.CheckConstraint("(status = 'processing' AND claim_token IS NOT NULL AND lease_until IS NOT NULL) OR "
                           "(status <> 'processing' AND claim_token IS NULL AND lease_until IS NULL)", name="lease_state"))
    op.create_index("ix_conversation_work", "conversation_jobs", ["user_id", "status", "next_attempt_at"])


def downgrade():
    op.drop_index("ix_conversation_work", table_name="conversation_jobs")
    op.drop_table("conversation_jobs")
    op.drop_constraint("declared_fat", "product_versions", type_="check")
    op.drop_constraint("food_kind", "product_versions", type_="check")
    op.drop_column("product_versions", "declared_fat_percent")
    op.drop_column("product_versions", "food_kind")
