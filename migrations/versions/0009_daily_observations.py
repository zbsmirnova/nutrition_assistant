"""Persist one revisable daily body weight and one daily steps total per user/date.

Revision ID: 0009
Revises: 0008
"""
from alembic import op
import sqlalchemy as sa


revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "observations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("metric", sa.Text(), nullable=False),
        sa.Column("series_date", sa.Date(), nullable=False),
        sa.Column("current_revision_id", sa.UUID(), nullable=False),
        sa.CheckConstraint("metric IN ('weight','daily_steps')", name=op.f("ck_observations_metric")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_observations_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_observations")),
        sa.UniqueConstraint("user_id", "id", name=op.f("uq_observations_user_id")),
        sa.UniqueConstraint("user_id", "id", "metric", name="uq_observation_metric"),
        sa.UniqueConstraint("user_id", "metric", "series_date", name="uq_observation_slot"),
    )
    op.create_table(
        "observation_revisions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("observation_id", sa.UUID(), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("metric", sa.Text(), nullable=False),
        sa.Column("applied_operation_id", sa.UUID(), nullable=False),
        sa.Column("value", sa.Numeric(18, 6)),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True)),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("time_zone", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), server_default="active", nullable=False),
        sa.Column("origin_kind", sa.Text(), server_default="manual", nullable=False),
        sa.CheckConstraint("revision_no > 0", name=op.f("ck_observation_revisions_positive_revision")),
        sa.CheckConstraint("state IN ('active','deleted')", name=op.f("ck_observation_revisions_state")),
        sa.CheckConstraint("origin_kind IN ('manual','increment')", name=op.f("ck_observation_revisions_origin_kind")),
        sa.CheckConstraint("metric IN ('weight','daily_steps')", name=op.f("ck_observation_revisions_metric")),
        sa.CheckConstraint("unit IN ('kg','steps')", name=op.f("ck_observation_revisions_unit")),
        sa.CheckConstraint(
            "(state = 'deleted' AND value IS NULL) OR "
            "(state = 'active' AND metric = 'weight' AND value IS NOT NULL AND value > 0 AND unit = 'kg') OR "
            "(state = 'active' AND metric = 'daily_steps' AND value IS NOT NULL AND value >= 0 "
            "AND value = trunc(value) AND unit = 'steps')",
            name=op.f("ck_observation_revisions_value_shape")),
        sa.ForeignKeyConstraint(["user_id", "applied_operation_id"],
                                ["applied_operations.user_id", "applied_operations.id"],
                                name=op.f("fk_observation_revisions_user_id_applied_operations"),
                                initially="DEFERRED", deferrable=True),
        sa.ForeignKeyConstraint(["user_id", "observation_id", "metric"],
                                ["observations.user_id", "observations.id", "observations.metric"],
                                name=op.f("fk_observation_revisions_user_id_observations")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_observation_revisions_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_observation_revisions")),
        sa.UniqueConstraint("user_id", "id", name=op.f("uq_observation_revisions_user_id")),
        sa.UniqueConstraint("user_id", "observation_id", "id", name="uq_observation_revision_parent"),
        sa.UniqueConstraint("user_id", "observation_id", "revision_no", name="uq_observation_revision_number"),
    )
    op.create_foreign_key("fk_observation_current_revision", "observations", "observation_revisions",
                          ["user_id", "id", "current_revision_id"], ["user_id", "observation_id", "id"],
                          initially="DEFERRED", deferrable=True)
    op.create_index("ix_observation_revisions_local_date", "observation_revisions",
                    ["user_id", "local_date", "observed_at"], unique=False)


def downgrade():
    op.drop_index("ix_observation_revisions_local_date", table_name="observation_revisions")
    op.drop_constraint("fk_observation_current_revision", "observations", type_="foreignkey")
    op.drop_table("observation_revisions")
    op.drop_table("observations")
