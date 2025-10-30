"""adding created at index

Revision ID: 8d99bee6e60a
Revises: c09e76282dd1
Create Date: 2025-10-30 21:25:29.757332

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '8d99bee6e60a'
down_revision = 'c09e76282dd1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(op.f('ix_privacy_preferences_created_at'), 'privacy_preferences', ['created_at'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_privacy_preferences_created_at'), table_name='privacy_preferences')
