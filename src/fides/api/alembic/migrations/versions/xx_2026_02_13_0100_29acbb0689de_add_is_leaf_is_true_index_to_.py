"""add is_leaf IS TRUE index to stagedresource

Revision ID: 29acbb0689de
Revises: 4d64174f422e
Create Date: 2026-02-13 01:00:04.789019

"""
import sqlalchemy as sa
from alembic import op
from loguru import logger
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '29acbb0689de'
down_revision = '4d64174f422e'
branch_labels = None
depends_on = None


"""
WARNING - Conditional migration based on table size
"""


def upgrade():
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
            'ix_stagedresource_monitor_leaf_true_status_urn',
            'stagedresource',
            ['monitor_config_id', 'is_leaf', 'diff_status', 'urn'],
            unique=False,
            postgresql_where=text('is_leaf IS TRUE')
        )
        logger.info("ix_stagedresource_monitor_leaf_true_status_urn index created successfully")
    else:
        logger.warning(
            "The stagedresource table has more than 1 million rows, "
            "skipping index creation. Index will be created during application startup "
            "via post_upgrade_index_creation.py"
        )


def downgrade():
    try:
        op.drop_index(
            'ix_stagedresource_monitor_leaf_true_status_urn',
            table_name='stagedresource',
            postgresql_where=text('is_leaf IS TRUE')
        )
        logger.info("Dropped ix_stagedresource_monitor_leaf_true_status_urn index")
    except Exception as e:
        logger.warning(
            f"Could not drop ix_stagedresource_monitor_leaf_true_status_urn index: {e}"
        )

