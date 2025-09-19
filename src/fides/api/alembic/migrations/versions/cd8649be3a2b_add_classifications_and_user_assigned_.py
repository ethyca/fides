"""add classifications and user_assigned_data_categories indices

Revision ID: cd8649be3a2b
Revises: a8e0c016afd
Create Date: 2025-09-19 13:49:02.762672

"""

import sqlalchemy as sa
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
revision = "cd8649be3a2b"
down_revision = "a8e0c016afd"
branch_labels = None
depends_on = None

"""
WARNING - Conditional migration based on table size
"""


def upgrade():
    # Check stagedresource table size
    connection = op.get_bind()

    # Check stagedresource table size to decide if we should create indexes immediately
    table_size = connection.execute(
        sa.text("SELECT COUNT(*) FROM stagedresource")
    ).scalar()

    if table_size < 1000000:
        logger.info(
            f"stagedresource table has {table_size} rows, creating GIN indices directly"
        )

        # Create GIN index for user_assigned_data_categories array operations (&&, @>, <@)
        op.execute(
            "CREATE INDEX idx_stagedresource_user_categories_gin "
            "ON stagedresource USING GIN (user_assigned_data_categories)"
        )

        # Create GIN index for classifications array operations (&&, @>, <@)
        op.execute(
            "CREATE INDEX idx_stagedresource_classifications_gin "
            "ON stagedresource USING GIN (classifications)"
        )

        logger.info("GIN indices created successfully")

    else:
        logger.warning(
            "The stagedresource table has more than 1 million rows, "
            "skipping index creation. Indexes will be created during application startup "
            "via post_upgrade_index_creation.py"
        )


def downgrade():
    # Drop indices in reverse order
    logger.info("Dropping GIN indices for stagedresource arrays")

    try:
        op.drop_index("idx_stagedresource_classifications_gin", "stagedresource")
        logger.info("Dropped classifications GIN index")
    except Exception as e:
        logger.warning(f"Could not drop classifications index: {e}")

    try:
        op.drop_index("idx_stagedresource_user_categories_gin", "stagedresource")
        logger.info("Dropped user_assigned_data_categories GIN index")
    except Exception as e:
        logger.warning(f"Could not drop user_categories index: {e}")
