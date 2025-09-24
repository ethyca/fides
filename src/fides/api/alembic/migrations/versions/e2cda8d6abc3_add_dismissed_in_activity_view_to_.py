"""add_dismissed_in_activity_view_to_monitor_task

Revision ID: e2cda8d6abc3
Revises: 0eef0016cf06
Create Date: 2025-09-17 23:37:49.678071

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e2cda8d6abc3"
down_revision = "0eef0016cf06"
branch_labels = None
depends_on = None


def upgrade():
    # Add the dismissed_in_activity_view column to monitortask table
    op.add_column(
        "monitortask",
        sa.Column(
            "dismissed_in_activity_view", sa.Boolean(), nullable=True, default=False
        ),
    )


def downgrade():
    # Remove the dismissed_in_activity_view column from monitortask table
    op.drop_column("monitortask", "dismissed_in_activity_view")
