"""Persist one-question clarification state for resumable food actions.

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("conversation_jobs", sa.Column("pending_questions", JSONB(none_as_null=True)))


def downgrade():
    op.drop_column("conversation_jobs", "pending_questions")
