"""add saas_version to executionlog

Adds a nullable saas_version column to the executionlog table to record which
version of a SaaS integration config was active when a DSR collection was processed.
Only populated for SaaS connectors (connection_type = 'saas'); null for all others.

Revision ID: a1ca9ddf3c3c
Revises: 4ac4864180db
Create Date: 2026-03-11

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1ca9ddf3c3c"
down_revision = "4ac4864180db"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "executionlog",
        sa.Column("saas_version", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("executionlog", "saas_version")
