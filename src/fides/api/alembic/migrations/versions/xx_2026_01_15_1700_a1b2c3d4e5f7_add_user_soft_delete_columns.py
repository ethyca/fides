"""add user soft delete columns

Revision ID: a1b2c3d4e5f7
Revises: 627c230d9917
Create Date: 2026-01-15 17:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f7"
down_revision = "627c230d9917"
branch_labels = None
depends_on = None


def upgrade():
    """Add soft-delete columns to fidesuser table."""
    op.add_column(
        "fidesuser",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "fidesuser",
        sa.Column("deleted_by", sa.String(), nullable=True),
    )


def downgrade():
    """Remove soft-delete columns from fidesuser table."""
    op.drop_column("fidesuser", "deleted_by")
    op.drop_column("fidesuser", "deleted_at")

