"""add is_leaf to stagedresource

Revision ID: 358e65f31c16
Revises: 8ac778399348
Create Date: 2026-01-06 03:58:34.377949

"""
from alembic import op
import sqlalchemy as sa
from loguru import logger


# revision identifiers, used by Alembic.
revision = '358e65f31c16'
down_revision = '8ac778399348'
branch_labels = None
depends_on = None


def upgrade():
    logger.info("Adding is_leaf column to stagedresource table")

    # Add the is_leaf column with a server default value
    op.add_column(
        'stagedresource',
        sa.Column('is_leaf', sa.Boolean(), nullable=False, server_default='false')
    )
    logger.info("Added is_leaf column")

    # Create a composite index on (monitor_config_id, is_leaf) for query performance
    op.create_index(
        'ix_stagedresource_monitor_config_is_leaf',
        'stagedresource',
        ['monitor_config_id', 'is_leaf'],
        unique=False
    )
    logger.info("Created composite index on (monitor_config_id, is_leaf)")
    logger.info("Note: is_leaf will be calculated when creating new staged resources")


def downgrade():
    logger.info("Removing is_leaf column and index")

    # Drop the index using execute with IF EXISTS
    op.execute("DROP INDEX IF EXISTS ix_stagedresource_monitor_config_is_leaf")

    # Drop the column using execute with IF EXISTS
    op.execute("ALTER TABLE stagedresource DROP COLUMN IF EXISTS is_leaf")

    logger.info("Removed is_leaf column from stagedresource table")
