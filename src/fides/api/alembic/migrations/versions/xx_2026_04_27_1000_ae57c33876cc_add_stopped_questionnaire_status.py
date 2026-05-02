"""add stopped questionnaire status

Revision ID: ae57c33876cc
Revises: d71c7d274c04
Create Date: 2026-04-27 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ae57c33876cc"
down_revision = "d71c7d274c04"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE questionnairestatus ADD VALUE IF NOT EXISTS 'stopped'")


def downgrade():
    # PostgreSQL does not support removing enum values directly.
    # The 'stopped' value will remain but be unused after downgrade.
    pass
