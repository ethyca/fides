"""staged resource ancestor link data migration

Revision ID: bf713b5a021d
Revises: 5474a47c77da
Create Date: 2025-06-03 09:44:58.769535

"""

import csv
import uuid
from io import StringIO
from pathlib import Path

import sqlalchemy as sa
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
revision = "bf713b5a021d"
down_revision = "5474a47c77da"
branch_labels = None
depends_on = None


def upgrade():
    logger.info("Populating staged resource ancestor links...")

    conn = op.get_bind()

    # Get all resources and their children into memory
    resources_query = """
    SELECT urn, children
    FROM stagedresource
    """
    resources = conn.execute(resources_query).fetchall()

    # Build resource -> children map in memory
    resource_children = {}
    for resource in resources:
        if resource.children:
            resource_children[resource.urn] = resource.children

    # Build list of all ancestor-descendant pairs to insert
    ancestor_links = []

    def process_children(ancestor_urn, children, visited=None):
        """Recursively process children and collect ancestor links"""
        if visited is None:
            visited = set()

        for child_urn in children:
            if child_urn not in visited:
                visited.add(child_urn)
                # Add direct ancestor link
                ancestor_links.append(
                    {
                        "id": f"{ancestor_urn}_{child_urn}",
                        "ancestor_urn": ancestor_urn,
                        "descendant_urn": child_urn,
                    }
                )

                # Recursively process this child's children
                if child_urn in resource_children:
                    process_children(
                        ancestor_urn, resource_children[child_urn], visited
                    )

    logger.info(
        f"Recursively processing {len(resource_children)} resources for ancestor links"
    )
    # Process each resource's children recursively
    for ancestor_urn, children in resource_children.items():
        process_children(ancestor_urn, children)

    logger.info(f"Found {len(ancestor_links)} ancestor links to insert")

    logger.info(f"Writing {len(ancestor_links)} ancestor links to memory buffer")

    # Create in-memory string buffer
    csv_buffer = StringIO()
    writer = csv.DictWriter(
        csv_buffer, fieldnames=["id", "ancestor_urn", "descendant_urn"]
    )
    writer.writeheader()
    for link in ancestor_links:
        # Generate a UUID for each row
        link["id"] = f"srl_{uuid.uuid4()}"
        writer.writerow(link)

    # Reset buffer position to start
    csv_buffer.seek(0)

    logger.info(
        "Copying ancestor links data from memory buffer into stagedresourceancestor table..."
    )
    copy_query = """
        COPY stagedresourceancestor (id, ancestor_urn, descendant_urn)
        FROM STDIN
        WITH (FORMAT CSV, HEADER TRUE)
    """
    conn.connection.cursor().copy_expert(copy_query, csv_buffer)
    logger.info(
        "Completed copying ancestor links data from memory buffer into stagedresourceancestor table"
    )

    if len(ancestor_links) < 1000000:

        logger.info("Creating primary key index on stagedresourceancestor table...")

        op.create_index(
            "ix_staged_resource_ancestor_pkey",
            "stagedresourceancestor",
            ["id"],
            unique=True,
        )

        logger.info("Completed creating primary key index")

        logger.info("Creating foreign key constraints stagedresourceancestor table...")

        op.create_foreign_key(
            "fk_staged_resource_ancestor_ancestor",
            "stagedresourceancestor",
            "stagedresource",
            ["ancestor_urn"],
            ["urn"],
            ondelete="CASCADE",
        )

        op.create_foreign_key(
            "fk_staged_resource_ancestor_descendant",
            "stagedresourceancestor",
            "stagedresource",
            ["descendant_urn"],
            ["urn"],
            ondelete="CASCADE",
        )

        logger.info("Completed creating foreign key constraints")

        logger.info("Creating unique constraint on stagedresourceancestor table...")

        op.create_unique_constraint(
            "uq_staged_resource_ancestor",
            "stagedresourceancestor",
            ["ancestor_urn", "descendant_urn"],
        )

        logger.info("Completed creating unique constraint")

        logger.info("Creating indexes on stagedresourceancestor table...")

        op.create_index(
            "ix_staged_resource_ancestor_ancestor",
            "stagedresourceancestor",
            ["ancestor_urn"],
            unique=False,
        )
        op.create_index(
            "ix_staged_resource_ancestor_descendant",
            "stagedresourceancestor",
            ["descendant_urn"],
            unique=False,
        )

        logger.info("Completed creating indexes on stagedresourceancestor table")
    else:
        logger.info(
            "Skipping creation of primary key index, foreign key constraints, unique constraint, and indexes on stagedresourceancestor table because there are more than 1,000,000 ancestor links. Please run `post_upgrade_index_creation.py` to create these indexes and constraints."
        )


def downgrade():
    logger.info(
        "Downgrading staged resource ancestor link data migration, populating child_diff_statuses..."
    )

    # Get child diff statuses for each ancestor
    conn = op.get_bind()
    child_diff_statuses_query = """
        UPDATE stagedresource
        SET child_diff_statuses = child_statuses.status_map
        FROM (
            SELECT
                stagedresourceancestor.ancestor_urn,
                jsonb_object_agg(distinct(stagedresource.diff_status), True) as status_map
            FROM stagedresourceancestor
            JOIN stagedresource ON stagedresourceancestor.descendant_urn = stagedresource.urn
            GROUP BY stagedresourceancestor.ancestor_urn
        ) AS child_statuses
        WHERE stagedresource.urn = child_statuses.ancestor_urn
    """
    result = conn.execute(child_diff_statuses_query)
    updated_rows = result.rowcount

    logger.info(
        f"Downgraded staged resource ancestor link data migration, completed populating child_diff_statuses for {updated_rows} rows"
    )

    # drop the StagedResourceAncestor table and its indexes

    op.drop_index(
        "ix_staged_resource_ancestor_descendant",
        table_name="stagedresourceancestor",
    )
    op.drop_index(
        "ix_staged_resource_ancestor_ancestor", table_name="stagedresourceancestor"
    )

    op.drop_index(
        "ix_staged_resource_ancestor_pkey",
        table_name="stagedresourceancestor",
    )
