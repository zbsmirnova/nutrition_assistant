"""Persist immutable user recipe versions and original ingredient snapshots.

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def _nutrition_columns():
    columns = []
    for nutrient in ("kcal", "protein_g", "fat_g", "carbs_g"):
        columns.extend([
            sa.Column(nutrient, sa.Numeric(18, 6)),
            sa.Column(nutrient + "_lower", sa.Numeric(18, 6)),
            sa.Column(nutrient + "_upper", sa.Numeric(18, 6)),
        ])
        columns.append(sa.CheckConstraint(
            f"({nutrient} IS NULL AND {nutrient}_lower IS NULL AND {nutrient}_upper IS NULL) OR "
            f"({nutrient} IS NOT NULL AND {nutrient} >= 0 AND "
            f"(({nutrient}_lower IS NULL AND {nutrient}_upper IS NULL) OR "
            f"({nutrient}_lower IS NOT NULL AND {nutrient}_upper IS NOT NULL AND "
            f"0 <= {nutrient}_lower AND {nutrient}_lower <= {nutrient} AND {nutrient} <= {nutrient}_upper)))",
            name=op.f(f"ck_recipe_versions_{nutrient}_bounds")))
    return columns


def upgrade():
    op.create_table(
        "recipes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("current_version_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_recipes_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipes")),
        sa.UniqueConstraint("user_id", "id", name=op.f("uq_recipes_user_id")),
    )
    op.create_table(
        "recipe_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("recipe_id", sa.UUID(), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("cooking_instructions", sa.Text()),
        sa.Column("nutrition_kind", sa.Text(), nullable=False),
        sa.Column("data_source_id", sa.UUID()),
        sa.Column("finished_yield_g", sa.Numeric(18, 6)),
        sa.Column("yield_basis", sa.Text()),
        sa.Column("estimate_approval_update_id", sa.UUID()),
        sa.Column("calculation_policy_version", sa.Text()),
        *_nutrition_columns(),
        sa.CheckConstraint("version_no > 0", name=op.f("ck_recipe_versions_positive_version")),
        sa.CheckConstraint("nutrition_kind IN ('provided','calculate')", name=op.f("ck_recipe_versions_nutrition_kind")),
        sa.CheckConstraint("yield_basis IS NULL OR yield_basis IN ('measured','ingredient_sum_no_evaporation','user_confirmed_estimate')",
                           name=op.f("ck_recipe_versions_yield_basis")),
        sa.CheckConstraint("finished_yield_g IS NULL OR finished_yield_g > 0", name=op.f("ck_recipe_versions_positive_yield")),
        sa.CheckConstraint("(nutrition_kind = 'provided' AND finished_yield_g IS NULL AND yield_basis IS NULL) OR "
                           "(nutrition_kind = 'calculate' AND finished_yield_g IS NOT NULL AND yield_basis IS NOT NULL)",
                           name=op.f("ck_recipe_versions_nutrition_shape")),
        sa.ForeignKeyConstraint(["user_id", "recipe_id"], ["recipes.user_id", "recipes.id"],
                                name=op.f("fk_recipe_versions_user_id_recipes")),
        sa.ForeignKeyConstraint(["user_id", "data_source_id"], ["data_sources.user_id", "data_sources.id"],
                                name=op.f("fk_recipe_versions_user_id_data_sources")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_recipe_versions_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipe_versions")),
        sa.UniqueConstraint("user_id", "id", name=op.f("uq_recipe_versions_user_id")),
        sa.UniqueConstraint("user_id", "recipe_id", "id", name="uq_recipe_version_parent"),
        sa.UniqueConstraint("user_id", "recipe_id", "version_no", name="uq_recipe_version_number"),
    )
    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("recipe_version_id", sa.UUID(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name_as_entered", sa.Text(), nullable=False),
        sa.Column("original_quantity", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("weight_basis", sa.Text()),
        sa.Column("source", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint("position >= 0 AND position < 100", name=op.f("ck_recipe_ingredients_position_range")),
        sa.CheckConstraint("weight_basis IS NULL OR weight_basis IN ('raw','cooked','as_sold')",
                           name=op.f("ck_recipe_ingredients_weight_basis")),
        sa.ForeignKeyConstraint(["user_id", "recipe_version_id"], ["recipe_versions.user_id", "recipe_versions.id"],
                                name=op.f("fk_recipe_ingredients_user_id_recipe_versions")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_recipe_ingredients_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipe_ingredients")),
        sa.UniqueConstraint("user_id", "id", name=op.f("uq_recipe_ingredients_user_id")),
        sa.UniqueConstraint("user_id", "recipe_version_id", "position", name="uq_recipe_ingredient_position"),
    )
    op.create_foreign_key("fk_recipe_current_version", "recipes", "recipe_versions",
                          ["user_id", "id", "current_version_id"], ["user_id", "recipe_id", "id"],
                          initially="DEFERRED", deferrable=True)
    op.create_index("ix_recipe_versions_parent", "recipe_versions", ["user_id", "recipe_id"], unique=False)
    op.create_index("ix_recipe_ingredients_version", "recipe_ingredients", ["user_id", "recipe_version_id"], unique=False)


def downgrade():
    op.drop_index("ix_recipe_ingredients_version", table_name="recipe_ingredients")
    op.drop_index("ix_recipe_versions_parent", table_name="recipe_versions")
    op.drop_constraint("fk_recipe_current_version", "recipes", type_="foreignkey")
    op.drop_table("recipe_ingredients")
    op.drop_table("recipe_versions")
    op.drop_table("recipes")
