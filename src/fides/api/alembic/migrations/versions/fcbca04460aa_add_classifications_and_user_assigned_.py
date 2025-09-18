"""add classifications and user_assigned_data_categories indices

Revision ID: fcbca04460aa
Revises: 4d8c0fcc5771
Create Date: 2025-09-15 20:23:15.715499

"""

import sqlalchemy as sa
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
revision = "fcbca04460aa"
down_revision = "4d8c0fcc5771"
branch_labels = None
depends_on = None

"""
WARNING - Conditional migration based on table size
"""


def upgrade():
    # Check stagedresource table size
    connection = op.get_bind()
    try:
        result = connection.execute(
            sa.text("SELECT COUNT(*) FROM stagedresource")
        ).fetchone()
        table_size = result[0] if result else 0
    except Exception as e:
        logger.warning(f"Could not check stagedresource table size: {e}")
        logger.info("Proceeding with direct index creation")
        table_size = 0

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
