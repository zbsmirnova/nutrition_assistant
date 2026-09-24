"""Record user approval separately from immutable external source snapshots.

Revision ID: 0010
Revises: 0009
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("product_confirmations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("product_version_id", UUID(as_uuid=True), nullable=False),
        sa.Column("confirmed_by_update_id", UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(["user_id", "product_version_id"],
                                ["product_versions.user_id", "product_versions.id"]),
        sa.ForeignKeyConstraint(["user_id", "confirmed_by_update_id"],
                                ["inbox_updates.user_id", "inbox_updates.id"]),
        sa.UniqueConstraint("user_id", "id", name="uq_product_confirmations_user_id"),
        sa.UniqueConstraint("user_id", "product_version_id", name="uq_product_confirmation_version"))


def downgrade():
    op.drop_table("product_confirmations")
