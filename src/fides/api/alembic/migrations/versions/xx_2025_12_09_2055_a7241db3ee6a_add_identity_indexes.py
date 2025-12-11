"""add identity indexes

Revision ID: a7241db3ee6a
Revises: 71f3ded6045a
Create Date: 2025-12-09 20:55:55.170914

Conditional migration based on table size

This migration creates indexes to optimize duplicate detection queries.
If tables have >= 1 million rows, index creation is deferred to
post_upgrade_index_creation.py which runs at application startup
using CREATE INDEX CONCURRENTLY (non-blocking).
"""

import sqlalchemy as sa
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
revision = "a7241db3ee6a"
down_revision = "71f3ded6045a"
branch_labels = None
depends_on = None

INDEX_ROW_COUNT_THRESHOLD = 1000000


def upgrade():
    connection = op.get_bind()

    # Check providedidentity table size
    providedidentity_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM providedidentity")
    ).scalar()

    if providedidentity_count < INDEX_ROW_COUNT_THRESHOLD:
        logger.info(
            f"providedidentity table has {providedidentity_count} rows, creating index directly"
        )
        op.create_index(
            "ix_providedidentity_reqid_field_hash",
            "providedidentity",
            ["privacy_request_id", "field_name", "hashed_value"],
            unique=False,
        )
    else:
        logger.warning(
            f"The providedidentity table has {providedidentity_count} rows (>= 1 million), "
            "skipping index creation. Index will be created during application startup "
            "via post_upgrade_index_creation.py"
        )

    # Check privacyrequest table size
    privacyrequest_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM privacyrequest")
    ).scalar()

    if privacyrequest_count < INDEX_ROW_COUNT_THRESHOLD:
        logger.info(
            f"privacyrequest table has {privacyrequest_count} rows, creating index directly"
        )
        op.create_index(
            "ix_privacyrequest_policy_created",
            "privacyrequest",
            ["policy_id", "created_at"],
            unique=False,
        )
    else:
        logger.warning(
            f"The privacyrequest table has {privacyrequest_count} rows (>= 1 million), "
            "skipping index creation. Index will be created during application startup "
            "via post_upgrade_index_creation.py"
        )


def downgrade():
    # Use IF EXISTS since indexes may not exist if creation was deferred
    # due to large table size (>= 1 million rows)
    op.execute("DROP INDEX IF EXISTS ix_providedidentity_reqid_field_hash")
    op.execute("DROP INDEX IF EXISTS ix_privacyrequest_policy_created")
