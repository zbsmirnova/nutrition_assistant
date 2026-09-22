"""M1's queryable relational model. Alembic revisions freeze migration history."""

from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


metadata = sa.MetaData(naming_convention={
    "pk": "pk_%(table_name)s", "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "ix": "ix_%(table_name)s_%(column_0_name)s",
})
NUTRIENTS = ("kcal", "protein_g", "fat_g", "carbs_g")


def identity():
    return sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4)


def created():
    return sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def owned(name, *parts):
    return sa.Table(name, metadata, identity(),
                    sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
                    created(), sa.UniqueConstraint("user_id", "id"), *parts)


def nutrition_columns():
    parts = []
    for nutrient in NUTRIENTS:
        parts.extend(sa.Column(nutrient + suffix, sa.Numeric(18, 6)) for suffix in ("", "_lower", "_upper"))
        parts.append(sa.CheckConstraint(
            f"({nutrient} IS NULL AND {nutrient}_lower IS NULL AND {nutrient}_upper IS NULL) OR "
            f"({nutrient} IS NOT NULL AND {nutrient} >= 0 AND "
            f"(({nutrient}_lower IS NULL AND {nutrient}_upper IS NULL) OR "
            f"({nutrient}_lower IS NOT NULL AND {nutrient}_upper IS NOT NULL AND "
            f"0 <= {nutrient}_lower AND {nutrient}_lower <= {nutrient} AND {nutrient} <= {nutrient}_upper)))",
            name=f"{nutrient}_bounds"))
    return parts


users = sa.Table("users", metadata, identity(), created(),
    sa.Column("time_zone", sa.Text, nullable=False),
    sa.Column("language", sa.Text, nullable=False, server_default="ru"),
    sa.Column("context_revision", sa.BigInteger, nullable=False, server_default="0"),
    sa.CheckConstraint("context_revision >= 0", name="nonnegative_revision"))

telegram_accounts = owned("telegram_accounts",
    sa.Column("bot_id", sa.BigInteger, nullable=False),
    sa.Column("telegram_user_id", sa.BigInteger, nullable=False),
    sa.Column("private_chat_id", sa.BigInteger, nullable=False),
    sa.UniqueConstraint("user_id", "id", "bot_id", name="uq_telegram_account_bot"),
    sa.UniqueConstraint("bot_id", "telegram_user_id", name="uq_telegram_bot_user"),
    sa.UniqueConstraint("bot_id", "private_chat_id", name="uq_telegram_bot_chat"))

inbox_updates = owned("inbox_updates",
    sa.Column("telegram_account_id", UUID(as_uuid=True), nullable=False),
    sa.Column("bot_id", sa.BigInteger, nullable=False),
    sa.Column("telegram_update_id", sa.BigInteger, nullable=False),
    sa.Column("telegram_message_id", sa.BigInteger, nullable=False),
    sa.Column("source_sent_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("source_time_zone", sa.Text, nullable=False),
    sa.Column("text", sa.Text, nullable=False),
    sa.Column("payload_hash", sa.String(64), nullable=False),
    sa.ForeignKeyConstraint(["user_id", "telegram_account_id", "bot_id"],
                           ["telegram_accounts.user_id", "telegram_accounts.id", "telegram_accounts.bot_id"]),
    sa.UniqueConstraint("bot_id", "telegram_update_id", name="uq_inbox_transport_delivery"))

prepared_operations = owned("prepared_operations",
    sa.Column("origin_update_id", UUID(as_uuid=True), nullable=False),
    sa.Column("position", sa.Integer, nullable=False),
    sa.Column("request_hash", sa.String(64), nullable=False),
    sa.Column("command", JSONB, nullable=False),
    sa.ForeignKeyConstraint(["user_id", "origin_update_id"], ["inbox_updates.user_id", "inbox_updates.id"]),
    sa.UniqueConstraint("user_id", "origin_update_id", "position", name="uq_prepared_operation_position"),
    sa.CheckConstraint("position >= 0 AND position < 32", name="position_range"))

applied_operations = owned("applied_operations",
    sa.Column("outcome", JSONB, nullable=False),
    sa.ForeignKeyConstraint(["user_id", "id"], ["prepared_operations.user_id", "prepared_operations.id"]))

data_sources = owned("data_sources",
    sa.Column("kind", sa.Text, nullable=False),
    sa.Column("evidence", JSONB, nullable=False))

products = owned("products", sa.Column("current_version_id", UUID(as_uuid=True), nullable=False))

product_versions = owned("product_versions",
    sa.Column("product_id", UUID(as_uuid=True), nullable=False),
    sa.Column("version_no", sa.Integer, nullable=False),
    sa.Column("name", sa.Text, nullable=False),
    sa.Column("data_source_id", UUID(as_uuid=True), nullable=False),
    sa.Column("nutrition_basis", sa.Text, nullable=False),
    sa.Column("weight_basis", sa.Text, nullable=False),
    *nutrition_columns(),
    sa.ForeignKeyConstraint(["user_id", "product_id"], ["products.user_id", "products.id"]),
    sa.ForeignKeyConstraint(["user_id", "data_source_id"], ["data_sources.user_id", "data_sources.id"]),
    sa.UniqueConstraint("user_id", "product_id", "version_no", name="uq_product_version_number"),
    sa.UniqueConstraint("user_id", "product_id", "id", name="uq_product_version_parent"),
    sa.UniqueConstraint("user_id", "id", "data_source_id", name="uq_product_version_source"),
    sa.CheckConstraint("version_no > 0", name="positive_version"),
    sa.CheckConstraint("nutrition_basis IN ('per_100_g','per_100_ml')", name="nutrition_basis"),
    sa.CheckConstraint("weight_basis IN ('raw','cooked','as_sold')", name="weight_basis"))
products.append_constraint(sa.ForeignKeyConstraint(
    ["user_id", "id", "current_version_id"],
    ["product_versions.user_id", "product_versions.product_id", "product_versions.id"],
    name="fk_product_current_version", use_alter=True, deferrable=True, initially="DEFERRED"))

food_days = owned("food_days",
    sa.Column("local_date", sa.Date, nullable=False),
    sa.Column("time_zone", sa.Text, nullable=False),
    sa.Column("revision", sa.BigInteger, nullable=False, server_default="0"),
    sa.Column("completeness", sa.Text, nullable=False, server_default="unconfirmed"),
    sa.Column("explicit_zero_food", sa.Boolean, nullable=False, server_default=sa.false()),
    sa.UniqueConstraint("user_id", "local_date", name="uq_food_day_date"),
    sa.CheckConstraint("revision >= 0", name="nonnegative_revision"),
    sa.CheckConstraint("completeness IN ('unconfirmed','complete')", name="completeness"),
    sa.CheckConstraint("NOT explicit_zero_food OR completeness = 'complete'", name="zero_requires_completion"))

food_entries = owned("food_entries", sa.Column("current_revision_id", UUID(as_uuid=True), nullable=False))

food_entry_revisions = owned("food_entry_revisions",
    sa.Column("food_entry_id", UUID(as_uuid=True), nullable=False),
    sa.Column("revision_no", sa.Integer, nullable=False),
    sa.Column("food_day_id", UUID(as_uuid=True), nullable=False),
    sa.Column("applied_operation_id", UUID(as_uuid=True), nullable=False),
    sa.Column("description", sa.Text, nullable=False),
    sa.Column("meal", sa.Text, nullable=False),
    sa.Column("time_zone", sa.Text, nullable=False),
    sa.Column("state", sa.Text, nullable=False, server_default="active"),
    sa.ForeignKeyConstraint(["user_id", "food_entry_id"], ["food_entries.user_id", "food_entries.id"]),
    sa.ForeignKeyConstraint(["user_id", "food_day_id"], ["food_days.user_id", "food_days.id"]),
    sa.ForeignKeyConstraint(["user_id", "applied_operation_id"], ["applied_operations.user_id", "applied_operations.id"],
                           deferrable=True, initially="DEFERRED"),
    sa.UniqueConstraint("user_id", "food_entry_id", "revision_no", name="uq_food_revision_number"),
    sa.UniqueConstraint("user_id", "food_entry_id", "id", name="uq_food_revision_parent"),
    sa.CheckConstraint("revision_no > 0", name="positive_revision"),
    sa.CheckConstraint("state IN ('active','deleted')", name="state"),
    sa.CheckConstraint("meal IN ('breakfast','lunch','dinner','snack','unspecified')", name="meal"))
food_entries.append_constraint(sa.ForeignKeyConstraint(
    ["user_id", "id", "current_revision_id"],
    ["food_entry_revisions.user_id", "food_entry_revisions.food_entry_id", "food_entry_revisions.id"],
    name="fk_food_current_revision", use_alter=True, deferrable=True, initially="DEFERRED"))

food_components = owned("food_components",
    sa.Column("food_entry_revision_id", UUID(as_uuid=True), nullable=False),
    sa.Column("position", sa.Integer, nullable=False),
    sa.Column("description", sa.Text, nullable=False),
    sa.Column("product_version_id", UUID(as_uuid=True), nullable=False),
    sa.Column("data_source_id", UUID(as_uuid=True), nullable=False),
    sa.Column("quantity_kind", sa.Text, nullable=False),
    sa.Column("edible_g", sa.Numeric(18, 6)),
    sa.Column("gross_g", sa.Numeric(18, 6)),
    sa.Column("inedible_g", sa.Numeric(18, 6)),
    sa.Column("volume_ml", sa.Numeric(18, 6)),
    sa.Column("weight_basis", sa.Text, nullable=False),
    sa.Column("calculation_version", sa.Text, nullable=False),
    *nutrition_columns(),
    sa.ForeignKeyConstraint(["user_id", "food_entry_revision_id"], ["food_entry_revisions.user_id", "food_entry_revisions.id"]),
    sa.ForeignKeyConstraint(["user_id", "product_version_id", "data_source_id"],
                           ["product_versions.user_id", "product_versions.id", "product_versions.data_source_id"]),
    sa.UniqueConstraint("user_id", "food_entry_revision_id", "position", name="uq_component_position"),
    sa.CheckConstraint("position >= 0 AND position < 100", name="position_range"),
    sa.CheckConstraint("weight_basis IN ('raw','cooked','as_sold')", name="weight_basis"),
    sa.CheckConstraint("(quantity_kind = 'mass' AND edible_g IS NOT NULL AND edible_g > 0 AND volume_ml IS NULL) OR "
                       "(quantity_kind = 'volume' AND volume_ml IS NOT NULL AND volume_ml > 0 "
                       "AND edible_g IS NULL AND gross_g IS NULL AND inedible_g IS NULL)", name="quantity"),
    sa.CheckConstraint("gross_g IS NULL OR (gross_g > 0 AND gross_g >= edible_g)", name="gross"),
    sa.CheckConstraint("inedible_g IS NULL OR inedible_g >= 0", name="inedible"),
    sa.CheckConstraint("gross_g IS NULL OR inedible_g IS NULL OR gross_g = edible_g + inedible_g", name="mass_balance"))

outbox = owned("outbox",
    sa.Column("operation_id", UUID(as_uuid=True), nullable=False),
    sa.Column("telegram_account_id", UUID(as_uuid=True), nullable=False),
    sa.Column("payload", JSONB, nullable=False),
    sa.Column("status", sa.Text, nullable=False, server_default="pending"),
    sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
    sa.Column("claim_token", UUID(as_uuid=True)),
    sa.Column("lease_until", sa.DateTime(timezone=True)),
    sa.Column("sent_at", sa.DateTime(timezone=True)),
    sa.ForeignKeyConstraint(["user_id", "operation_id"], ["applied_operations.user_id", "applied_operations.id"]),
    sa.ForeignKeyConstraint(["user_id", "telegram_account_id"], ["telegram_accounts.user_id", "telegram_accounts.id"]),
    sa.UniqueConstraint("user_id", "operation_id", name="uq_outbox_operation"),
    sa.CheckConstraint("attempts >= 0", name="nonnegative_attempts"),
    sa.CheckConstraint("status IN ('pending','sending','sent','uncertain','failed')", name="status"),
    sa.CheckConstraint("(status = 'sending' AND claim_token IS NOT NULL AND lease_until IS NOT NULL) OR "
                       "(status <> 'sending' AND claim_token IS NULL AND lease_until IS NULL)", name="lease_state"),
    sa.CheckConstraint("(status = 'sent') = (sent_at IS NOT NULL)", name="sent_time"))

sa.Index("ix_food_revisions_day", food_entry_revisions.c.user_id, food_entry_revisions.c.food_day_id)
sa.Index("ix_prepared_origin", prepared_operations.c.user_id, prepared_operations.c.origin_update_id)
sa.Index("ix_outbox_dispatch", outbox.c.status, outbox.c.created_at)
