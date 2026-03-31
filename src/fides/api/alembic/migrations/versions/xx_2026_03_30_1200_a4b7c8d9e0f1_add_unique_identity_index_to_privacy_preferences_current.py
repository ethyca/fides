"""Add unique identity index to privacy_preferences_current

Adds a unique expression index on (search_data->'identity') to the
privacy_preferences_current partition, enforcing at most one is_latest=true
row per identity at the database level.

Any pre-existing duplicates are demoted to is_latest=false before the
index is created. For large tables (>1M rows), index creation is deferred
to the post-upgrade background task (post_upgrade_index_creation.py).

Revision ID: a4b7c8d9e0f1
Revises: 29113e44faec
Create Date: 2026-03-30 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
revision = "a4b7c8d9e0f1"
down_revision = "29113e44faec"
branch_labels = None
depends_on = None

INDEX_NAME = "idx_privacy_preferences_current_unique_identity"
MIGRATION_KEY = INDEX_NAME


def upgrade() -> None:
    connection = op.get_bind()

    # Step 1: Fix any existing duplicates.
    # Keep the row with the highest id (most recent insert) and demote the rest
    # to is_latest=false. PostgreSQL row movement will relocate them to the
    # privacy_preferences_historic partition automatically.
    op.execute(
        """
        WITH duplicates AS (
            SELECT id, is_latest,
                   ROW_NUMBER() OVER (
                       PARTITION BY search_data->'identity'
                       ORDER BY id DESC
                   ) AS rn
            FROM privacy_preferences_current
        )
        UPDATE privacy_preferences
        SET is_latest = false, updated_at = now()
        FROM duplicates d
        WHERE privacy_preferences.id = d.id
          AND privacy_preferences.is_latest = true
          AND d.rn > 1
        """
    )

    # Step 2: Register the deferred index in post_upgrade_background_migration_tasks
    op.execute(
        sa.text(
            "INSERT INTO post_upgrade_background_migration_tasks (key, task_type, completed_at) "
            "VALUES (:key, 'index', NULL) ON CONFLICT (task_type, key) DO NOTHING"
        ).bindparams(key=MIGRATION_KEY)
    )

    # Step 3: Check table size to decide if we should create index immediately
    table_size = connection.execute(
        sa.text("SELECT COUNT(*) FROM privacy_preferences_current")
    ).scalar()

    if table_size < 1000000:
        logger.info(
            f"privacy_preferences_current has {table_size} rows, creating unique index directly"
        )
        op.execute(
            sa.text(
                f"CREATE UNIQUE INDEX {INDEX_NAME} "
                "ON privacy_preferences_current ((search_data->'identity'))"
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
        logger.info(f"{INDEX_NAME} index created successfully")
    else:
        logger.warning(
            f"privacy_preferences_current has {table_size} rows (>1M), "
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
