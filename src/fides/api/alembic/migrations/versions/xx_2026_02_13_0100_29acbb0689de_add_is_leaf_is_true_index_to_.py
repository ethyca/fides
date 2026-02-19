"""add is_leaf IS TRUE index to stagedresource and ancestor_urn index to stagedresourceancestor

Revision ID: 29acbb0689de
Revises: cc9a5690f9e7
Create Date: 2026-02-13 01:00:04.789019

"""
import sqlalchemy as sa
from alembic import op
from loguru import logger
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '29acbb0689de'
down_revision = 'cc9a5690f9e7'
branch_labels = None
depends_on = None


"""
WARNING - Conditional migration based on table size
"""


def upgrade():
    connection = op.get_bind()
    
    # Check stagedresource table size to decide if we should create index immediately
    stagedresource_table_size = connection.execute(
        sa.text("SELECT COUNT(*) FROM stagedresource")
    ).scalar()

    if stagedresource_table_size < 1000000:
        logger.info(
            f"stagedresource table has {stagedresource_table_size} rows, creating index directly"
        )
        op.create_index(
            'ix_stagedresource_leaf_true_monitor_status_urn',
            'stagedresource',
            ['monitor_config_id', 'diff_status', 'urn'],
            unique=False,
            postgresql_where=text('is_leaf IS TRUE')
        )
        logger.info("ix_stagedresource_leaf_true_monitor_status_urn index created successfully")
    else:
        logger.warning(
            "The stagedresource table has more than 1 million rows, "
            "skipping index creation. Index will be created during application startup "
            "via post_upgrade_index_creation.py"
        )
    
    # Check stagedresourceancestor table size to decide if we should create new index immediately
    stagedresourceancestor_table_size = connection.execute(
        sa.text("SELECT COUNT(*) FROM stagedresourceancestor")
    ).scalar()
    
    if stagedresourceancestor_table_size < 1000000:
        logger.info(
            f"stagedresourceancestor table has {stagedresourceancestor_table_size} rows, creating index directly"
        )
        op.create_index(
            'ix_staged_resource_ancestor_anc_dist_desc',
            'stagedresourceancestor',
            ['ancestor_urn', 'distance', 'descendant_urn'],
            unique=False
        )
        logger.info("ix_staged_resource_ancestor_anc_dist_desc index created successfully")
    else:
        logger.warning(
            "The stagedresourceancestor table has more than 1 million rows, "
            "skipping index creation. Index will be created during application startup "
            "via post_upgrade_index_creation.py"
        )


def downgrade():
    connection = op.get_bind()
    
    # Drop the new stagedresource index (check existence first to avoid transaction abort)
    stagedresource_index_exists = connection.execute(
        sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE indexname = 'ix_stagedresource_leaf_true_monitor_status_urn'
            )
        """)
    ).scalar()
    
    if stagedresource_index_exists:
        logger.info("Dropping ix_stagedresource_leaf_true_monitor_status_urn index")
        op.drop_index(
            'ix_stagedresource_leaf_true_monitor_status_urn',
            table_name='stagedresource',
            postgresql_where=text('is_leaf IS TRUE')
        )
        logger.info("Successfully dropped ix_stagedresource_leaf_true_monitor_status_urn")
    else:
        logger.debug(
            "Index ix_stagedresource_leaf_true_monitor_status_urn does not exist "
            "(expected if table had >1M rows during upgrade)"
        )
    
    # Drop the new stagedresourceancestor index (check existence first to avoid transaction abort)
    ancestor_index_exists = connection.execute(
        sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE indexname = 'ix_staged_resource_ancestor_anc_dist_desc'
            )
        """)
    ).scalar()
    
    if ancestor_index_exists:
        logger.info("Dropping ix_staged_resource_ancestor_anc_dist_desc index")
        op.drop_index(
            'ix_staged_resource_ancestor_anc_dist_desc',
            table_name='stagedresourceancestor'
        )
        logger.info("Successfully dropped ix_staged_resource_ancestor_anc_dist_desc")
    else:
        logger.debug(
            "Index ix_staged_resource_ancestor_anc_dist_desc does not exist "
            "(expected if table had >1M rows during upgrade)"
        )
