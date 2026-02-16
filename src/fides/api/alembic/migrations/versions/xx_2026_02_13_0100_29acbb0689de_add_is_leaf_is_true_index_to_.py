"""add is_leaf IS TRUE index to stagedresource and ancestor_urn index to stagedresourceancestor

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
    
    # Drop the old inefficient index ix_staged_resource_ancestor_desc_anc_dist
    # This index is rarely used with all 3 columns, and we're replacing it with a more efficient one
    # Note: May not exist if it was deferred to post_upgrade_index_creation (table >1M rows)
    # Check existence first to avoid aborting the transaction
    index_exists = connection.execute(
        sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE indexname = 'ix_staged_resource_ancestor_desc_anc_dist'
            )
        """)
    ).scalar()
    
    if index_exists:
        logger.info("Dropping old index ix_staged_resource_ancestor_desc_anc_dist")
        op.drop_index(
            'ix_staged_resource_ancestor_desc_anc_dist',
            table_name='stagedresourceancestor'
        )
        logger.info("Successfully dropped ix_staged_resource_ancestor_desc_anc_dist")
    else:
        logger.debug(
            "Index ix_staged_resource_ancestor_desc_anc_dist does not exist "
            "(expected if table had >1M rows during previous migrations)"
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
                WHERE indexname = 'ix_stagedresource_monitor_leaf_true_status_urn'
            )
        """)
    ).scalar()
    
    if stagedresource_index_exists:
        logger.info("Dropping ix_stagedresource_monitor_leaf_true_status_urn index")
        op.drop_index(
            'ix_stagedresource_monitor_leaf_true_status_urn',
            table_name='stagedresource',
            postgresql_where=text('is_leaf IS TRUE')
        )
        logger.info("Successfully dropped ix_stagedresource_monitor_leaf_true_status_urn")
    else:
        logger.debug(
            "Index ix_stagedresource_monitor_leaf_true_status_urn does not exist "
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
    
    # Recreate the old index that was dropped in upgrade (only if table is small)
    stagedresourceancestor_table_size = connection.execute(
        sa.text("SELECT COUNT(*) FROM stagedresourceancestor")
    ).scalar()
    
    if stagedresourceancestor_table_size < 1000000:
        try:
            logger.info(
                f"stagedresourceancestor table has {stagedresourceancestor_table_size} rows, "
                "recreating old index ix_staged_resource_ancestor_desc_anc_dist"
            )
            op.create_index(
                'ix_staged_resource_ancestor_desc_anc_dist',
                'stagedresourceancestor',
                ['descendant_urn', 'ancestor_urn', 'distance'],
                unique=False
            )
            logger.info("Successfully recreated ix_staged_resource_ancestor_desc_anc_dist")
        except Exception as e:
            logger.warning(
                f"Could not recreate ix_staged_resource_ancestor_desc_anc_dist index: {e}"
            )
    else:
        logger.warning(
            f"stagedresourceancestor table has {stagedresourceancestor_table_size} rows (>1M), "
            "skipping index recreation to avoid blocking. If needed, recreate manually using: "
            "CREATE INDEX CONCURRENTLY ix_staged_resource_ancestor_desc_anc_dist "
            "ON stagedresourceancestor (descendant_urn, ancestor_urn, distance)"
        )

