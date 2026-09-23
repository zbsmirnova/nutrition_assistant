"""Persist whether a food quantity was measured or user-approved as an estimate.

Revision ID: 0008
Revises: 0007
"""
from alembic import op
import sqlalchemy as sa


revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("food_components", sa.Column("quantity_provenance", sa.Text(),
                                                 server_default="measured", nullable=False))
    op.add_column("food_components", sa.Column("approval_update_id", sa.UUID()))
    op.create_foreign_key("fk_food_components_user_id_approval_update", "food_components", "inbox_updates",
                          ["user_id", "approval_update_id"], ["user_id", "id"])
    op.create_check_constraint("ck_food_components_quantity_provenance", "food_components",
        "quantity_provenance IN ('measured','user_approved_estimate')")
    op.create_check_constraint("ck_food_components_quantity_provenance_approval", "food_components",
        "(quantity_provenance = 'measured' AND approval_update_id IS NULL) OR "
        "(quantity_provenance = 'user_approved_estimate' AND approval_update_id IS NOT NULL)")


def downgrade():
    op.drop_constraint("ck_food_components_quantity_provenance_approval", "food_components", type_="check")
    op.drop_constraint("ck_food_components_quantity_provenance", "food_components", type_="check")
    op.drop_constraint("fk_food_components_user_id_approval_update", "food_components", type_="foreignkey")
    op.drop_column("food_components", "approval_update_id")
    op.drop_column("food_components", "quantity_provenance")
