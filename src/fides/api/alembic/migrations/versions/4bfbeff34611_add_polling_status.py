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
    op.execute("ALTER TYPE executionlogstatus ADD VALUE 'polling'")


def downgrade():
    # Remove any records that have the 'polling' enum value before dropping it
    # Fallback to 'paused' (awaiting_processing) for backward compatibility

    op.execute("UPDATE requesttask SET status = 'paused' WHERE status = 'polling'")
    op.execute("UPDATE executionlog SET status = 'paused' WHERE status = 'polling'")
    op.execute(
        "UPDATE digest_task_execution SET status = 'paused' WHERE status = 'polling'"
    )
    op.execute("UPDATE monitortask SET status = 'paused' WHERE status = 'polling'")
    op.execute(
        "UPDATE monitortaskexecutionlog SET status = 'paused' WHERE status = 'polling'"
    )

    # Recreate the enum without the 'polling' value
    op.execute("ALTER TYPE executionlogstatus RENAME TO executionlogstatus_old")
    op.execute(
        "CREATE TYPE executionlogstatus AS ENUM ("
        "'in_processing', 'pending', 'complete', 'error', 'paused', 'retrying', 'skipped'"
        ")"
    )

    # Update all tables that use the enum type
    op.execute(
        "ALTER TABLE requesttask ALTER COLUMN status TYPE executionlogstatus USING "
        "status::text::executionlogstatus"
    )
    op.execute(
        "ALTER TABLE executionlog ALTER COLUMN status TYPE executionlogstatus USING "
        "status::text::executionlogstatus"
    )
    op.execute(
        "ALTER TABLE digest_task_execution ALTER COLUMN status TYPE executionlogstatus USING "
        "status::text::executionlogstatus"
    )
    op.execute(
        "ALTER TABLE monitortask ALTER COLUMN status TYPE executionlogstatus USING "
        "status::text::executionlogstatus"
    )
    op.execute(
        "ALTER TABLE monitortaskexecutionlog ALTER COLUMN status TYPE executionlogstatus USING "
        "status::text::executionlogstatus"
    )

    # Drop the old enum type
    op.execute("DROP TYPE executionlogstatus_old")
