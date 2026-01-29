"""add is_leaf to stagedresource

Revision ID: d05acec55c64
Revises: 6d5f70dd0ba5
Create Date: 2026-01-26 14:51:03.086087

"""

import sqlalchemy as sa
from alembic import op
from loguru import logger
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "d05acec55c64"
down_revision = "6d5f70dd0ba5"
branch_labels = None
depends_on = None

"""
WARNING - Conditional migration based on table size
"""


def upgrade():
    op.add_column("stagedresource", sa.Column("is_leaf", sa.Boolean(), nullable=True))

    # Check stagedresource table size to decide if we should create index immediately
    connection = op.get_bind()
    table_size = connection.execute(
        sa.text("SELECT COUNT(*) FROM stagedresource")
    ).scalar()

    if table_size < 1000000:
        logger.info(
            f"stagedresource table has {table_size} rows, creating index directly"
        )
        op.create_index(
            "ix_stagedresource_monitor_leaf_status_urn",
            "stagedresource",
            ["monitor_config_id", "is_leaf", "diff_status", "urn"],
            postgresql_where=text("is_leaf IS NOT NULL"),
        )
        logger.info("Index created successfully")
    else:
        logger.warning(
            "The stagedresource table has more than 1 million rows, "
            "skipping index creation. Index will be created during application startup "
            "via post_upgrade_index_creation.py"
        )


def downgrade():
    try:
        op.drop_index(
            "ix_stagedresource_monitor_leaf_status_urn", table_name="stagedresource"
        )
        logger.info("Dropped ix_stagedresource_monitor_leaf_status_urn index")
    except Exception as e:
        logger.warning(
            f"Could not drop ix_stagedresource_monitor_leaf_status_urn index: {e}"
        )

    op.drop_column("stagedresource", "is_leaf")
