"""
Removes the  stagedresource.child_diff_statuses column.

This migration is run _after_ the data migration
that populates the staged resource ancestor link table,
to prevent unintended data loss.

Revision ID: c586a56c25e7
Revises: bf713b5a021d
Create Date: 2025-06-03 09:47:11.389652

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c586a56c25e7"
down_revision = "bf713b5a021d"
branch_labels = None
depends_on = None


def upgrade():
    # remove the StagedResource.child_diff_statuses column as it's no longer needed
    op.drop_column("stagedresource", "child_diff_statuses")


def downgrade():
    # re-add the StagedResource.child_diff_statuses column
    op.add_column(
        "stagedresource",
        sa.Column(
            "child_diff_statuses",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )
