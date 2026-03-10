"""add distance to stagedresourceancestor

Revision ID: d304f57aea6d
Revises: f85bd4c08401
Create Date: 2026-02-09 00:10:27.559747

"""
import sqlalchemy as sa
from alembic import op
from loguru import logger


# revision identifiers, used by Alembic.
revision = "d304f57aea6d"
down_revision = "f85bd4c08401"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "stagedresourceancestor", sa.Column("distance", sa.Integer(), nullable=True)
    )

    # Check stagedresourceancestor table size to decide if we should create index immediately
    connection = op.get_bind()
    table_size = connection.execute(
        sa.text("SELECT COUNT(*) FROM stagedresourceancestor")
    ).scalar()

    if table_size < 1000000:
        logger.info(
            f"stagedresourceancestor table has {table_size} rows, creating index directly"
        )
        op.create_index(
            "ix_staged_resource_ancestor_desc_anc_dist",
            "stagedresourceancestor",
            ["descendant_urn", "ancestor_urn", "distance"],
            unique=False,
        )
        logger.info(
            "ix_staged_resource_ancestor_desc_anc_dist index created successfully"
        )
    else:
        logger.warning(
            "The stagedresourceancestor table has more than 1 million rows, "
            "skipping index creation. Index will be created during application startup "
            "via post_upgrade_index_creation.py"
        )


def downgrade():
    try:
        op.drop_index(
            "ix_staged_resource_ancestor_desc_anc_dist",
            table_name="stagedresourceancestor",
        )
        logger.info("Dropped ix_staged_resource_ancestor_desc_anc_dist index")
    except Exception as e:
        logger.warning(
            f"Could not drop ix_staged_resource_ancestor_desc_anc_dist index: {e}"
        )

    op.drop_column("stagedresourceancestor", "distance")

    # Clear backfill tracking to allow re-execution if migration is re-applied
    logger.info("Clearing backfill tracking for stagedresourceancestor-distance")
    op.execute(
        "DELETE FROM backfill_history WHERE backfill_name = 'stagedresourceancestor-distance'"
    )
