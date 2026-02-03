"""add backfill history

Revision ID: 841e0b148993
Revises: 6d5f70dd0ba5
Create Date: 2026-02-03 20:29:57.879185

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '841e0b148993'
down_revision = '6d5f70dd0ba5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'backfill_history',
        sa.Column('backfill_name', sa.String(255), primary_key=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade():
    op.drop_table('backfill_history')
