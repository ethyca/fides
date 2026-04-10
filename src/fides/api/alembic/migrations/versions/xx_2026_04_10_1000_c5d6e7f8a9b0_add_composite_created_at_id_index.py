"""Add composite (created_at, id) index to privacy_preferences

Adds a composite index on (created_at, id) to the privacy_preferences table.
Postgres automatically creates matching indexes on both partitions.
This enables efficient cursor-based pagination with ORDER BY created_at, id
when filtering by time window, avoiding full-table sorts at scale.

For large tables (>1M rows), index creation is deferred to the post-upgrade
background task (post_upgrade_index_creation.py).

Revision ID: c5d6e7f8a9b0
Revises: b9c4d5e6f7a8
Create Date: 2026-04-10 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
revision = "c5d6e7f8a9b0"
down_revision = "b9c4d5e6f7a8"
branch_labels = None
depends_on = None

INDEX_NAME = "idx_privacy_preferences_created_at_id"
MIGRATION_KEY = INDEX_NAME


def upgrade() -> None:
    connection = op.get_bind()

    # Register in post_upgrade_background_migration_tasks
    op.execute(
        sa.text(
            "INSERT INTO post_upgrade_background_migration_tasks (key, task_type, completed_at) "
            "VALUES (:key, 'index', NULL) ON CONFLICT (task_type, key) DO NOTHING"
        ).bindparams(key=MIGRATION_KEY)
    )

    # Check table size to decide if we should create index immediately
    table_size = connection.execute(
        sa.text("SELECT COUNT(*) FROM privacy_preferences")
    ).scalar()

    if table_size < 1000000:
        logger.info(
            f"privacy_preferences has {table_size} rows, creating composite index directly"
        )
        op.execute(
            sa.text(
                f"CREATE INDEX {INDEX_NAME} "
                "ON privacy_preferences (created_at, id)"
            )
        )
        # Mark as completed so the post-upgrade startup task doesn't re-check
        op.execute(
            sa.text(
                "UPDATE post_upgrade_background_migration_tasks "
                "SET completed_at = now() "
                "WHERE key = :key AND task_type = 'index' AND completed_at IS NULL"
            ).bindparams(key=MIGRATION_KEY)
        )
        logger.info(f"{INDEX_NAME} created successfully")
    else:
        logger.warning(
            f"privacy_preferences has {table_size} rows (>1M), "
            "skipping index creation. Index will be created during application startup "
            "via post_upgrade_index_creation.py"
        )


def downgrade() -> None:
    op.execute(sa.text(f"DROP INDEX IF EXISTS {INDEX_NAME}"))
    op.execute(
        sa.text(
            "DELETE FROM post_upgrade_background_migration_tasks "
            "WHERE key = :key AND task_type = 'index'"
        ).bindparams(key=MIGRATION_KEY)
    )
