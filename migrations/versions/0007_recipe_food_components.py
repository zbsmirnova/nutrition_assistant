"""Allow consumed food components to pin recipe versions.

Revision ID: 0007
Revises: 0006
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("food_components", "product_version_id", existing_type=sa.UUID(), nullable=True)
    op.alter_column("food_components", "data_source_id", existing_type=sa.UUID(), nullable=True)
    op.alter_column("food_components", "weight_basis", existing_type=sa.Text(), nullable=True)
    op.add_column("food_components", sa.Column("component_kind", sa.Text(), server_default="product", nullable=False))
    op.add_column("food_components", sa.Column("recipe_version_id", sa.UUID()))
    op.create_foreign_key("fk_food_components_user_id_recipe_versions", "food_components", "recipe_versions",
                          ["user_id", "recipe_version_id"], ["user_id", "id"])
    op.create_check_constraint("ck_food_components_component_kind", "food_components",
        "component_kind IN ('product','recipe')")
    op.create_check_constraint("ck_food_components_component_source", "food_components",
        "(component_kind = 'product' AND product_version_id IS NOT NULL AND recipe_version_id IS NULL AND data_source_id IS NOT NULL AND weight_basis IS NOT NULL) OR "
        "(component_kind = 'recipe' AND product_version_id IS NULL AND recipe_version_id IS NOT NULL AND data_source_id IS NULL AND weight_basis IS NULL AND quantity_kind = 'mass')")


def downgrade():
    op.drop_constraint("ck_food_components_component_source", "food_components", type_="check")
    op.drop_constraint("ck_food_components_component_kind", "food_components", type_="check")
    op.drop_constraint("fk_food_components_user_id_recipe_versions", "food_components", type_="foreignkey")
    op.drop_column("food_components", "recipe_version_id")
    op.drop_column("food_components", "component_kind")
    op.alter_column("food_components", "weight_basis", existing_type=sa.Text(), nullable=False)
    op.alter_column("food_components", "data_source_id", existing_type=sa.UUID(), nullable=False)
    op.alter_column("food_components", "product_version_id", existing_type=sa.UUID(), nullable=False)
