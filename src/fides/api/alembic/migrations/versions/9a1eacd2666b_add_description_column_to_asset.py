"""add description column to asset

Revision ID: 9a1eacd2666b
Revises: bd875a8b5d96
Create Date: 2025-02-28 13:59:26.022822

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9a1eacd2666b"
down_revision = "bd875a8b5d96"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("asset", sa.Column("description", sa.String(), nullable=True))


def downgrade():
    op.drop_column("asset", "description")
