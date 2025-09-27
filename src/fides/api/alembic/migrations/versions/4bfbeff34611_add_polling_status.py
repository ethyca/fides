"""add polling status

Revision ID: 4bfbeff34611
Revises: 7db29f9cd77b
Create Date: 2025-09-20 23:02:45.550170

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4bfbeff34611"
down_revision = "7db29f9cd77b"
branch_labels = None
depends_on = None


def upgrade():
    # Add 'polling' to executionlogstatus enum
    op.execute("alter type executionlogstatus add value 'polling'")


def downgrade():
    # Remove 'polling' from executionlogstatus enum (requires recreating the enum)
    op.execute("alter type executionlogstatus rename to executionlogstatus_old")
    op.execute(
        "create type executionlogstatus as enum('in_processing', 'pending', 'complete', 'error', 'paused', 'retrying', 'skipped')"
    )
    op.execute(
        (
            "alter table executionlog alter column status type executionlogstatus using "
            "status::text::executionlogstatus"
        )
    )
    op.execute("drop type executionlogstatus_old")
