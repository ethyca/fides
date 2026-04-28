"""recreate ix_privacyrequest_duplicate_request_group_id

Revision ID: e8f9a0b1c2d3
Revises: d6e7f8a9b0c1
Create Date: 2026-04-20 12:00:00.000000

The index on privacyrequest.duplicate_request_group_id was created by migration
c09e76282dd1 but was dropped (along with the column) by 80d28dea3b6b when the
column was rebuilt as a UUID foreign key; the index was never recreated. This
migration restores it so the upcoming search-endpoint filter on that column is
efficient.

Conditional migration based on table size: if the table has >= 1 million rows,
index creation is deferred to post_upgrade_index_creation.py which runs the
CREATE INDEX CONCURRENTLY statement at application startup (non-blocking).

"""

import sqlalchemy as sa
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
revision = "e8f9a0b1c2d3"
down_revision = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None

INDEX_ROW_COUNT_THRESHOLD = 1_000_000
INDEX_NAME = "ix_privacyrequest_duplicate_request_group_id"


def upgrade() -> None:
    connection = op.get_bind()
    privacyrequest_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM privacyrequest")
    ).scalar()

    if privacyrequest_count < INDEX_ROW_COUNT_THRESHOLD:
        logger.info(
            f"privacyrequest table has {privacyrequest_count} rows, creating index directly"
        )
        op.create_index(
            INDEX_NAME,
            "privacyrequest",
            ["duplicate_request_group_id"],
            unique=False,
        )
    else:
        logger.warning(
            f"The privacyrequest table has {privacyrequest_count} rows (>= 1 million), "
            "skipping index creation. Index will be created during application startup "
            "via post_upgrade_index_creation.py"
        )
        op.execute(
            sa.text(
                "INSERT INTO post_upgrade_background_migration_tasks "
                "(key, task_type, completed_at) "
                "VALUES (:key, 'index', NULL) "
                "ON CONFLICT (task_type, key) DO NOTHING"
            ).bindparams(key=INDEX_NAME)
        )


def downgrade() -> None:
    # Use IF EXISTS since the index may not exist if creation was deferred
    # due to large table size (>= 1 million rows).
    op.execute(sa.text(f"DROP INDEX IF EXISTS {INDEX_NAME}"))
    op.execute(
        sa.text(
            "DELETE FROM post_upgrade_background_migration_tasks "
            "WHERE key = :key AND task_type = 'index'"
        ).bindparams(key=INDEX_NAME)
    )
