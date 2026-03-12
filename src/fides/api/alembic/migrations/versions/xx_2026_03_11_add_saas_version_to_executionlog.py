"""add saas_version to executionlog

Adds a nullable saas_version column to the executionlog table to record which
version of a SaaS integration config was active when a DSR collection was processed.
Only populated for SaaS connectors (connection_type = 'saas'); null for all others.

Revision ID: a1b2c3d4e5f6
Revises: 04281f44cc0b
Create Date: 2026-03-11

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "04281f44cc0b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "executionlog",
        sa.Column("saas_version", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("executionlog", "saas_version")
