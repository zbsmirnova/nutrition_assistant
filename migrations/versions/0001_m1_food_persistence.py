"""M1 food persistence

Revision ID: 0001
Revises: none
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('time_zone', sa.Text(), nullable=False),
    sa.Column('language', sa.Text(), server_default='ru', nullable=False),
    sa.Column('context_revision', sa.BigInteger(), server_default='0', nullable=False),
    sa.CheckConstraint('context_revision >= 0', name=op.f('ck_users_nonnegative_revision')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    op.create_table('data_sources',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('kind', sa.Text(), nullable=False),
    sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_data_sources_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_data_sources')),
    sa.UniqueConstraint('user_id', 'id', name=op.f('uq_data_sources_user_id'))
    )
    op.create_table('food_days',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('local_date', sa.Date(), nullable=False),
    sa.Column('time_zone', sa.Text(), nullable=False),
    sa.Column('revision', sa.BigInteger(), server_default='0', nullable=False),
    sa.Column('completeness', sa.Text(), server_default='unconfirmed', nullable=False),
    sa.Column('explicit_zero_food', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.CheckConstraint("NOT explicit_zero_food OR completeness = 'complete'", name=op.f('ck_food_days_zero_requires_completion')),
    sa.CheckConstraint("completeness IN ('unconfirmed','complete')", name=op.f('ck_food_days_completeness')),
    sa.CheckConstraint('revision >= 0', name=op.f('ck_food_days_nonnegative_revision')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_food_days_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_food_days')),
    sa.UniqueConstraint('user_id', 'id', name=op.f('uq_food_days_user_id')),
    sa.UniqueConstraint('user_id', 'local_date', name='uq_food_day_date')
    )
    op.create_table('food_entries',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('current_revision_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_food_entries_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_food_entries')),
    sa.UniqueConstraint('user_id', 'id', name=op.f('uq_food_entries_user_id'))
    )
    op.create_table('products',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('current_version_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_products_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_products')),
    sa.UniqueConstraint('user_id', 'id', name=op.f('uq_products_user_id'))
    )
    op.create_table('telegram_accounts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('bot_id', sa.BigInteger(), nullable=False),
    sa.Column('telegram_user_id', sa.BigInteger(), nullable=False),
    sa.Column('private_chat_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_telegram_accounts_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_telegram_accounts')),
    sa.UniqueConstraint('bot_id', 'private_chat_id', name='uq_telegram_bot_chat'),
    sa.UniqueConstraint('bot_id', 'telegram_user_id', name='uq_telegram_bot_user'),
    sa.UniqueConstraint('user_id', 'id', name=op.f('uq_telegram_accounts_user_id'))
    )
    op.create_table('inbox_updates',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('telegram_account_id', sa.UUID(), nullable=False),
    sa.Column('telegram_update_id', sa.BigInteger(), nullable=False),
    sa.Column('telegram_message_id', sa.BigInteger(), nullable=False),
    sa.Column('source_sent_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('source_time_zone', sa.Text(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('payload_hash', sa.String(length=64), nullable=False),
    sa.ForeignKeyConstraint(['user_id', 'telegram_account_id'], ['telegram_accounts.user_id', 'telegram_accounts.id'], name=op.f('fk_inbox_updates_user_id_telegram_accounts')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_inbox_updates_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_inbox_updates')),
    sa.UniqueConstraint('telegram_account_id', 'telegram_update_id', name='uq_inbox_transport_delivery'),
    sa.UniqueConstraint('user_id', 'id', name=op.f('uq_inbox_updates_user_id'))
    )
    op.create_table('product_versions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('product_id', sa.UUID(), nullable=False),
    sa.Column('version_no', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('data_source_id', sa.UUID(), nullable=False),
    sa.Column('nutrition_basis', sa.Text(), nullable=False),
    sa.Column('weight_basis', sa.Text(), nullable=False),
    sa.Column('kcal', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('kcal_lower', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('kcal_upper', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('protein_g', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('protein_g_lower', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('protein_g_upper', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('fat_g', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('fat_g_lower', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('fat_g_upper', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('carbs_g', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('carbs_g_lower', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('carbs_g_upper', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.CheckConstraint("nutrition_basis IN ('per_100_g','per_100_ml')", name=op.f('ck_product_versions_nutrition_basis')),
    sa.CheckConstraint("weight_basis IN ('raw','cooked','as_sold')", name=op.f('ck_product_versions_weight_basis')),
    sa.CheckConstraint('(carbs_g IS NULL AND carbs_g_lower IS NULL AND carbs_g_upper IS NULL) OR (carbs_g IS NOT NULL AND carbs_g >= 0 AND ((carbs_g_lower IS NULL AND carbs_g_upper IS NULL) OR (carbs_g_lower IS NOT NULL AND carbs_g_upper IS NOT NULL AND 0 <= carbs_g_lower AND carbs_g_lower <= carbs_g AND carbs_g <= carbs_g_upper)))', name=op.f('ck_product_versions_carbs_g_bounds')),
    sa.CheckConstraint('(fat_g IS NULL AND fat_g_lower IS NULL AND fat_g_upper IS NULL) OR (fat_g IS NOT NULL AND fat_g >= 0 AND ((fat_g_lower IS NULL AND fat_g_upper IS NULL) OR (fat_g_lower IS NOT NULL AND fat_g_upper IS NOT NULL AND 0 <= fat_g_lower AND fat_g_lower <= fat_g AND fat_g <= fat_g_upper)))', name=op.f('ck_product_versions_fat_g_bounds')),
    sa.CheckConstraint('(kcal IS NULL AND kcal_lower IS NULL AND kcal_upper IS NULL) OR (kcal IS NOT NULL AND kcal >= 0 AND ((kcal_lower IS NULL AND kcal_upper IS NULL) OR (kcal_lower IS NOT NULL AND kcal_upper IS NOT NULL AND 0 <= kcal_lower AND kcal_lower <= kcal AND kcal <= kcal_upper)))', name=op.f('ck_product_versions_kcal_bounds')),
    sa.CheckConstraint('(protein_g IS NULL AND protein_g_lower IS NULL AND protein_g_upper IS NULL) OR (protein_g IS NOT NULL AND protein_g >= 0 AND ((protein_g_lower IS NULL AND protein_g_upper IS NULL) OR (protein_g_lower IS NOT NULL AND protein_g_upper IS NOT NULL AND 0 <= protein_g_lower AND protein_g_lower <= protein_g AND protein_g <= protein_g_upper)))', name=op.f('ck_product_versions_protein_g_bounds')),
    sa.CheckConstraint('version_no > 0', name=op.f('ck_product_versions_positive_version')),
    sa.ForeignKeyConstraint(['user_id', 'data_source_id'], ['data_sources.user_id', 'data_sources.id'], name=op.f('fk_product_versions_user_id_data_sources')),
    sa.ForeignKeyConstraint(['user_id', 'product_id'], ['products.user_id', 'products.id'], name=op.f('fk_product_versions_user_id_products')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_product_versions_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_product_versions')),
    sa.UniqueConstraint('user_id', 'id', 'data_source_id', name='uq_product_version_source'),
    sa.UniqueConstraint('user_id', 'id', name=op.f('uq_product_versions_user_id')),
    sa.UniqueConstraint('user_id', 'product_id', 'id', name='uq_product_version_parent'),
    sa.UniqueConstraint('user_id', 'product_id', 'version_no', name='uq_product_version_number')
    )
    op.create_table('prepared_operations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('origin_update_id', sa.UUID(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('request_hash', sa.String(length=64), nullable=False),
    sa.Column('command', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.CheckConstraint('position >= 0 AND position < 32', name=op.f('ck_prepared_operations_position_range')),
    sa.ForeignKeyConstraint(['user_id', 'origin_update_id'], ['inbox_updates.user_id', 'inbox_updates.id'], name=op.f('fk_prepared_operations_user_id_inbox_updates')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_prepared_operations_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_prepared_operations')),
    sa.UniqueConstraint('user_id', 'id', name=op.f('uq_prepared_operations_user_id')),
    sa.UniqueConstraint('user_id', 'origin_update_id', 'position', name='uq_prepared_operation_position')
    )
    op.create_index('ix_prepared_origin', 'prepared_operations', ['user_id', 'origin_update_id'], unique=False)
    op.create_table('applied_operations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('outcome', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.ForeignKeyConstraint(['user_id', 'id'], ['prepared_operations.user_id', 'prepared_operations.id'], name=op.f('fk_applied_operations_user_id_prepared_operations')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_applied_operations_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_applied_operations')),
    sa.UniqueConstraint('user_id', 'id', name=op.f('uq_applied_operations_user_id'))
    )
    op.create_table('food_entry_revisions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('food_entry_id', sa.UUID(), nullable=False),
    sa.Column('revision_no', sa.Integer(), nullable=False),
    sa.Column('food_day_id', sa.UUID(), nullable=False),
    sa.Column('applied_operation_id', sa.UUID(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('meal', sa.Text(), nullable=False),
    sa.Column('time_zone', sa.Text(), nullable=False),
    sa.Column('state', sa.Text(), server_default='active', nullable=False),
    sa.CheckConstraint("meal IN ('breakfast','lunch','dinner','snack','unspecified')", name=op.f('ck_food_entry_revisions_meal')),
    sa.CheckConstraint("state IN ('active','deleted')", name=op.f('ck_food_entry_revisions_state')),
    sa.CheckConstraint('revision_no > 0', name=op.f('ck_food_entry_revisions_positive_revision')),
    sa.ForeignKeyConstraint(['user_id', 'applied_operation_id'], ['applied_operations.user_id', 'applied_operations.id'], name=op.f('fk_food_entry_revisions_user_id_applied_operations'), initially='DEFERRED', deferrable=True),
    sa.ForeignKeyConstraint(['user_id', 'food_day_id'], ['food_days.user_id', 'food_days.id'], name=op.f('fk_food_entry_revisions_user_id_food_days')),
    sa.ForeignKeyConstraint(['user_id', 'food_entry_id'], ['food_entries.user_id', 'food_entries.id'], name=op.f('fk_food_entry_revisions_user_id_food_entries')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_food_entry_revisions_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_food_entry_revisions')),
    sa.UniqueConstraint('user_id', 'food_entry_id', 'id', name='uq_food_revision_parent'),
    sa.UniqueConstraint('user_id', 'food_entry_id', 'revision_no', name='uq_food_revision_number'),
    sa.UniqueConstraint('user_id', 'id', name=op.f('uq_food_entry_revisions_user_id'))
    )
    op.create_index('ix_food_revisions_day', 'food_entry_revisions', ['user_id', 'food_day_id'], unique=False)
    op.create_table('outbox',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('operation_id', sa.UUID(), nullable=False),
    sa.Column('telegram_account_id', sa.UUID(), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('status', sa.Text(), server_default='pending', nullable=False),
    sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
    sa.Column('claim_token', sa.UUID(), nullable=True),
    sa.Column('lease_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("(status = 'sending' AND claim_token IS NOT NULL AND lease_until IS NOT NULL) OR (status <> 'sending' AND claim_token IS NULL AND lease_until IS NULL)", name=op.f('ck_outbox_lease_state')),
    sa.CheckConstraint("(status = 'sent') = (sent_at IS NOT NULL)", name=op.f('ck_outbox_sent_time')),
    sa.CheckConstraint("status IN ('pending','sending','sent','uncertain','failed')", name=op.f('ck_outbox_status')),
    sa.CheckConstraint('attempts >= 0', name=op.f('ck_outbox_nonnegative_attempts')),
    sa.ForeignKeyConstraint(['user_id', 'operation_id'], ['applied_operations.user_id', 'applied_operations.id'], name=op.f('fk_outbox_user_id_applied_operations')),
    sa.ForeignKeyConstraint(['user_id', 'telegram_account_id'], ['telegram_accounts.user_id', 'telegram_accounts.id'], name=op.f('fk_outbox_user_id_telegram_accounts')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_outbox_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_outbox')),
    sa.UniqueConstraint('user_id', 'id', name=op.f('uq_outbox_user_id')),
    sa.UniqueConstraint('user_id', 'operation_id', name='uq_outbox_operation')
    )
    op.create_index('ix_outbox_dispatch', 'outbox', ['status', 'created_at'], unique=False)
    op.create_table('food_components',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('food_entry_revision_id', sa.UUID(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('product_version_id', sa.UUID(), nullable=False),
    sa.Column('data_source_id', sa.UUID(), nullable=False),
    sa.Column('quantity_kind', sa.Text(), nullable=False),
    sa.Column('edible_g', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('gross_g', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('inedible_g', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('volume_ml', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('weight_basis', sa.Text(), nullable=False),
    sa.Column('calculation_version', sa.Text(), nullable=False),
    sa.Column('kcal', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('kcal_lower', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('kcal_upper', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('protein_g', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('protein_g_lower', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('protein_g_upper', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('fat_g', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('fat_g_lower', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('fat_g_upper', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('carbs_g', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('carbs_g_lower', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.Column('carbs_g_upper', sa.Numeric(precision=18, scale=6), nullable=True),
    sa.CheckConstraint("(quantity_kind = 'mass' AND edible_g IS NOT NULL AND edible_g > 0 AND volume_ml IS NULL) OR (quantity_kind = 'volume' AND volume_ml IS NOT NULL AND volume_ml > 0 AND edible_g IS NULL AND gross_g IS NULL AND inedible_g IS NULL)", name=op.f('ck_food_components_quantity')),
    sa.CheckConstraint("weight_basis IN ('raw','cooked','as_sold')", name=op.f('ck_food_components_weight_basis')),
    sa.CheckConstraint('(carbs_g IS NULL AND carbs_g_lower IS NULL AND carbs_g_upper IS NULL) OR (carbs_g IS NOT NULL AND carbs_g >= 0 AND ((carbs_g_lower IS NULL AND carbs_g_upper IS NULL) OR (carbs_g_lower IS NOT NULL AND carbs_g_upper IS NOT NULL AND 0 <= carbs_g_lower AND carbs_g_lower <= carbs_g AND carbs_g <= carbs_g_upper)))', name=op.f('ck_food_components_carbs_g_bounds')),
    sa.CheckConstraint('(fat_g IS NULL AND fat_g_lower IS NULL AND fat_g_upper IS NULL) OR (fat_g IS NOT NULL AND fat_g >= 0 AND ((fat_g_lower IS NULL AND fat_g_upper IS NULL) OR (fat_g_lower IS NOT NULL AND fat_g_upper IS NOT NULL AND 0 <= fat_g_lower AND fat_g_lower <= fat_g AND fat_g <= fat_g_upper)))', name=op.f('ck_food_components_fat_g_bounds')),
    sa.CheckConstraint('(kcal IS NULL AND kcal_lower IS NULL AND kcal_upper IS NULL) OR (kcal IS NOT NULL AND kcal >= 0 AND ((kcal_lower IS NULL AND kcal_upper IS NULL) OR (kcal_lower IS NOT NULL AND kcal_upper IS NOT NULL AND 0 <= kcal_lower AND kcal_lower <= kcal AND kcal <= kcal_upper)))', name=op.f('ck_food_components_kcal_bounds')),
    sa.CheckConstraint('(protein_g IS NULL AND protein_g_lower IS NULL AND protein_g_upper IS NULL) OR (protein_g IS NOT NULL AND protein_g >= 0 AND ((protein_g_lower IS NULL AND protein_g_upper IS NULL) OR (protein_g_lower IS NOT NULL AND protein_g_upper IS NOT NULL AND 0 <= protein_g_lower AND protein_g_lower <= protein_g AND protein_g <= protein_g_upper)))', name=op.f('ck_food_components_protein_g_bounds')),
    sa.CheckConstraint('gross_g IS NULL OR (gross_g > 0 AND gross_g >= edible_g)', name=op.f('ck_food_components_gross')),
    sa.CheckConstraint('gross_g IS NULL OR inedible_g IS NULL OR gross_g = edible_g + inedible_g', name=op.f('ck_food_components_mass_balance')),
    sa.CheckConstraint('inedible_g IS NULL OR inedible_g >= 0', name=op.f('ck_food_components_inedible')),
    sa.CheckConstraint('position >= 0 AND position < 100', name=op.f('ck_food_components_position_range')),
    sa.ForeignKeyConstraint(['user_id', 'food_entry_revision_id'], ['food_entry_revisions.user_id', 'food_entry_revisions.id'], name=op.f('fk_food_components_user_id_food_entry_revisions')),
    sa.ForeignKeyConstraint(['user_id', 'product_version_id', 'data_source_id'], ['product_versions.user_id', 'product_versions.id', 'product_versions.data_source_id'], name=op.f('fk_food_components_user_id_product_versions')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_food_components_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_food_components')),
    sa.UniqueConstraint('user_id', 'food_entry_revision_id', 'position', name='uq_component_position'),
    sa.UniqueConstraint('user_id', 'id', name=op.f('uq_food_components_user_id'))
    )
    # Add circular current-pointer constraints after both sides exist.
    op.create_foreign_key('fk_product_current_version', 'products', 'product_versions',
        ['user_id', 'id', 'current_version_id'], ['user_id', 'product_id', 'id'],
        deferrable=True, initially='DEFERRED')
    op.create_foreign_key('fk_food_current_revision', 'food_entries', 'food_entry_revisions',
        ['user_id', 'id', 'current_revision_id'], ['user_id', 'food_entry_id', 'id'],
        deferrable=True, initially='DEFERRED')
    op.execute("""CREATE FUNCTION reject_snapshot_update() RETURNS trigger
        LANGUAGE plpgsql AS $$ BEGIN
        RAISE EXCEPTION 'Snapshot rows cannot be updated' USING ERRCODE = '55000';
        END; $$""")
    for table in ('data_sources', 'product_versions', 'inbox_updates', 'prepared_operations',
                  'applied_operations', 'food_entry_revisions', 'food_components'):
        op.execute(f'CREATE TRIGGER immutable_snapshot BEFORE UPDATE ON {table} '
                   'FOR EACH ROW EXECUTE FUNCTION reject_snapshot_update()')
    op.execute("""CREATE FUNCTION protect_outbox_intent() RETURNS trigger
        LANGUAGE plpgsql AS $$ BEGIN
        IF NEW.user_id IS DISTINCT FROM OLD.user_id
           OR NEW.operation_id IS DISTINCT FROM OLD.operation_id
           OR NEW.telegram_account_id IS DISTINCT FROM OLD.telegram_account_id
           OR NEW.payload IS DISTINCT FROM OLD.payload THEN
            RAISE EXCEPTION 'Response intent cannot be replaced' USING ERRCODE = '55000';
        END IF;
        RETURN NEW;
        END; $$""")
    op.execute('CREATE TRIGGER immutable_outbox_intent BEFORE UPDATE ON outbox '
               'FOR EACH ROW EXECUTE FUNCTION protect_outbox_intent()')



def downgrade():
    op.drop_constraint('fk_food_current_revision', 'food_entries', type_='foreignkey')
    op.drop_constraint('fk_product_current_version', 'products', type_='foreignkey')
    op.drop_table('food_components')
    op.drop_index('ix_outbox_dispatch', table_name='outbox')
    op.drop_table('outbox')
    op.drop_index('ix_food_revisions_day', table_name='food_entry_revisions')
    op.drop_table('food_entry_revisions')
    op.drop_table('applied_operations')
    op.drop_index('ix_prepared_origin', table_name='prepared_operations')
    op.drop_table('prepared_operations')
    op.drop_table('product_versions')
    op.drop_table('inbox_updates')
    op.drop_table('telegram_accounts')
    op.drop_table('products')
    op.drop_table('food_entries')
    op.drop_table('food_days')
    op.drop_table('data_sources')
    op.drop_table('users')
    op.execute('DROP FUNCTION protect_outbox_intent()')
    op.execute('DROP FUNCTION reject_snapshot_update()')
