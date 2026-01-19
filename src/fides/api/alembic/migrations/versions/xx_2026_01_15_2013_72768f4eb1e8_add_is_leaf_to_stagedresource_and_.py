"""add is_leaf to stagedresource and distance to stagedresourceancestor

Revision ID: 72768f4eb1e8
Revises: 6d5f70dd0ba5
Create Date: 2026-01-15 20:13:38.968462

"""
from alembic import op
import sqlalchemy as sa
from loguru import logger


# revision identifiers, used by Alembic.
revision = '72768f4eb1e8'
down_revision = '6d5f70dd0ba5'
branch_labels = None
depends_on = None


def upgrade():
    logger.info("Adding is_leaf column to stagedresource table")
    op.add_column('stagedresource', sa.Column('is_leaf', sa.Boolean(), nullable=False, server_default='false'))

    logger.info("Added is_leaf index to stagedresource table")
    op.create_index('ix_stagedresource_monitor_config_is_leaf', 'stagedresource', ['monitor_config_id', 'is_leaf'], unique=False)
    logger.info("Note: is_leaf will be calculated when creating new staged resources")

    logger.info("Adding distance column to stagedresourceancestor table")
    op.add_column('stagedresourceancestor', sa.Column('distance', sa.Integer(), nullable=False, server_default='0'))

    logger.info("Added distance index to stagedresourceancestor table")
    op.create_index('ix_staged_resource_ancestor_ancestor_distance', 'stagedresourceancestor', ['ancestor_urn', 'distance'], unique=False)
    logger.info("Note: distance will be calculated when creating new staged resource ancestors")

def downgrade():
    op.drop_index('ix_staged_resource_ancestor_ancestor_distance', table_name='stagedresourceancestor')
    op.drop_column('stagedresourceancestor', 'distance')
    op.execute("DROP INDEX IF EXISTS ix_stagedresource_monitor_config_is_leaf")
    op.execute("ALTER TABLE stagedresource DROP COLUMN IF EXISTS is_leaf")
