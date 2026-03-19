"""add received_at to currentprivacypreferencev2

Revision ID: 94273d7e8319
Revises: a1b2c3d4e5f7
Create Date: 2026-03-18 21:59:14.123976

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '94273d7e8319'
down_revision = 'a1b2c3d4e5f7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('currentprivacypreferencev2', sa.Column('received_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column('currentprivacypreferencev2', 'received_at')
