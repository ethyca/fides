"""make answer_version created_by nullable

Revision ID: b3a7e2d41f09
Revises: ae57c33876cc
Create Date: 2026-05-01 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b3a7e2d41f09"
down_revision = "ae57c33876cc"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "answer_version",
        "created_by",
        existing_type=sa.String(),
        nullable=True,
    )
    # Backfill sentinel values to NULL
    op.execute(
        "UPDATE answer_version SET created_by = NULL "
        "WHERE created_by IN ('system', 'scheduler', 'unknown')"
    )
    # Backfill usernames to emails where a matching FidesUser exists
    op.execute(
        "UPDATE answer_version av "
        "SET created_by = fu.email_address "
        "FROM fidesuser fu "
        "WHERE av.created_by = fu.username "
        "AND fu.email_address IS NOT NULL "
        "AND av.created_by NOT LIKE '%%@%%'"
    )


def downgrade():
    # Restore NULL values to 'system' for backward compatibility
    op.execute(
        "UPDATE answer_version SET created_by = 'system' WHERE created_by IS NULL"
    )
    op.alter_column(
        "answer_version",
        "created_by",
        existing_type=sa.String(),
        nullable=False,
    )
