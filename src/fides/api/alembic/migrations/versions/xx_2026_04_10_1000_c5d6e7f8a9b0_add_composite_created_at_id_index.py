"""Add composite (created_at, id) indexes to privacy_preferences partitions

Registers one composite (created_at, id) index per child partition of the
privacy_preferences partitioned table. These support efficient cursor-based
pagination with ORDER BY created_at, id and created_at range filters, via
Merge Append across per-partition index scans.

CREATE INDEX CONCURRENTLY is not supported on partitioned parent tables, so
the indexes are created directly on each child partition (the same
convention used by idx_privacy_preferences_current_unique_identity in
migration a4b7c8d9e0f1). Creation is deferred to the post-upgrade
background task (post_upgrade_index_creation.py) because
CREATE INDEX CONCURRENTLY cannot run inside the migration transaction.

Revision ID: c5d6e7f8a9b0
Revises: b9c4d5e6f7a8
Create Date: 2026-04-10 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c5d6e7f8a9b0"
down_revision = "b9c4d5e6f7a8"
branch_labels = None
depends_on = None

CURRENT_INDEX_NAME = "idx_privacy_preferences_current_created_at_id"
HISTORIC_INDEX_NAME = "idx_privacy_preferences_historic_created_at_id"
MIGRATION_KEYS = (CURRENT_INDEX_NAME, HISTORIC_INDEX_NAME)


def upgrade() -> None:
    # Register each per-partition index for deferred creation by the
    # post-upgrade startup task (see post_upgrade_index_creation.py).
    for key in MIGRATION_KEYS:
        op.execute(
            sa.text(
                "INSERT INTO post_upgrade_background_migration_tasks (key, task_type, completed_at) "
                "VALUES (:key, 'index', NULL) ON CONFLICT (task_type, key) DO NOTHING"
            ).bindparams(key=key)
        )


def downgrade() -> None:
    # Raw SQL because op.drop_index(..., if_exists=True) requires alembic>=1.12
    # and we pin 1.8.1. The indexes may not exist yet if the background task
    # hasn't run, so IF EXISTS is necessary.
    op.execute(sa.text(f"DROP INDEX IF EXISTS {CURRENT_INDEX_NAME}"))
    op.execute(sa.text(f"DROP INDEX IF EXISTS {HISTORIC_INDEX_NAME}"))
    op.execute(
        sa.text(
            "DELETE FROM post_upgrade_background_migration_tasks "
            "WHERE key = ANY(:keys) AND task_type = 'index'"
        ).bindparams(keys=list(MIGRATION_KEYS))
    )
