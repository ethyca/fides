"""add index on providedidentity.privacy_request_id

Revision ID: 3ff6449c099e
Revises: 56fe6fad2d89
Create Date: 2025-11-25 18:54:50.135782

"""

import sqlalchemy as sa
from alembic import op
from loguru import logger

from fides.api.migrations.post_upgrade_index_creation import INDEX_ROW_COUNT_THRESHOLD

# revision identifiers, used by Alembic.
revision = "3ff6449c099e"
down_revision = "56fe6fad2d89"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()

    # Check providedidentity table size to decide if we should create index immediately
    providedidentity_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM providedidentity")
    ).scalar()

    if providedidentity_count < INDEX_ROW_COUNT_THRESHOLD:
        op.create_index(
            op.f("ix_providedidentity_privacy_request_id"),
            "providedidentity",
            ["privacy_request_id"],
            unique=False,
        )
    else:
        logger.warning(
            "The providedidentity table has more than 1 million rows, "
            "skipping index creation. Indexes will be created during application startup "
            "via post_upgrade_index_creation.py"
        )


def downgrade():
    # Drop index if it exists (it may not exist if it was deferred)
    # Note: If you downgrade this migration, you should also remove the
    # "providedidentity" entry from TABLE_OBJECT_MAP in post_upgrade_index_creation.py
    # to prevent the index from being automatically recreated on app startup
    op.execute("DROP INDEX IF EXISTS ix_providedidentity_privacy_request_id")
