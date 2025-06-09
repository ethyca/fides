"""
Staged resource ancestor link data migration.

Indexes and constraints are created on this table _after_ data is populated.
If > 1,000,000 stagedresourceancestor records are created as part
of the data migration, the migration will skip creating the indexes
and constraints, and will instead log a message
indicating that index migration should be performed as part of app runtime.

The data migration has the following steps:
- Query for all staged resources and their children
- Build a list in-memory of all ancestor-descendant pairs to insert by recursively
    processing each resource's children
- Write the ancestor links to a CSV string in-memory
- Copy the CSV string into the stagedresourceancestor table via a PostgreSQL COPY
    command
- Create the indexes and constraints on the stagedresourceancestor table if
    < 1,000,000 ancestor links are created


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

    # Get all resources and their children in batches
    BATCH_SIZE = 500000

    # Query resources in batches using yield_per
    resources_query = sa.text(
        """
        SELECT urn, children
        FROM stagedresource
    """
    )
    resource_children = {}

    # process resources and populate resource_children map in batches
    # to limit memory usage
    for batch in (
        conn.execution_options(stream_results=True)
        .execute(resources_query)
        .yield_per(BATCH_SIZE)
        .partitions()
    ):
        logger.info(f"Processing batch of {BATCH_SIZE} resources")

        # Build resource -> children map for this batch
        for result in batch:
            urn = result.urn
            children = result.children
            if children:
                resource_children[urn] = children
            else:
                # even if no children, we still add the resource to the map
                # so that we maintain a record of all resources and can
                # check for orphaned descendant records later
                resource_children[urn] = []

    # Build list of ancestor-descendant pairs
    ancestor_links = []

    def process_children(ancestor_urn, children, visited=None):
        """Recursively process children and collect ancestor links"""
        if visited is None:
            visited = set()

        for child_urn in children:
            if child_urn not in visited:
                visited.add(child_urn)
                if child_urn not in resource_children:
                    logger.warning(
                        f"Found orphaned descendant URN: {child_urn}, not adding ancestor link"
                    )
                else:
                    # Add direct ancestor link
                    ancestor_links.append(
                        {
                            "id": f"srl_{uuid.uuid4()}",
                            "ancestor_urn": ancestor_urn,
                            "descendant_urn": child_urn,
                        }
                    )

                    # Recursively process this child's children
                    process_children(
                        ancestor_urn, resource_children[child_urn], visited
                    )

    logger.info(
        f"Recursively processing {len(resource_children)} resources for ancestor links in current batch"
    )

    # Process each resource's children recursively
    for ancestor_urn, children in resource_children.items():
        process_children(ancestor_urn, children)

    # remove the resource_children map from memory
    del resource_children

    ancestor_links_count = len(ancestor_links)
    logger.info(f"Found {ancestor_links_count} ancestor links in current batch")

    if ancestor_links_count > 0:
        # Create temporary CSV file
        temp_csv_path = Path("staged_resource_ancestors.csv")
        with open(temp_csv_path, "w", newline="") as csv_file:
            writer = csv.DictWriter(
                csv_file, fieldnames=["id", "ancestor_urn", "descendant_urn"]
            )
            writer.writeheader()
            logger.info(f"Writing {ancestor_links_count} ancestor links to CSV file")
            writer.writerows(ancestor_links)

        del ancestor_links

        # Copy all data from CSV file into table
        logger.info(
            f"Copying {ancestor_links_count} ancestor links from CSV file into stagedresourceancestor table..."
        )
        with open(temp_csv_path, "r") as csv_file:
            copy_query = """
                COPY stagedresourceancestor (id, ancestor_urn, descendant_urn)
                FROM STDIN
                WITH (FORMAT CSV, HEADER TRUE)
            """
            conn.connection.cursor().copy_expert(copy_query, csv_file)

        # Clean up temp file
        temp_csv_path.unlink()

        logger.info(
            f"Completed copying all ancestor links. Total ancestor links created: {ancestor_links_count}"
        )

    if ancestor_links_count < 1000000:

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
            "Skipping creation of primary key index, foreign key constraints, unique constraint, and indexes on stagedresourceancestor table because there are more than 1,000,000 ancestor links. These will be populated as part of the `post_upgrade_index_creation.py` task kicked off during application startup."
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

    # Intentionally not dropping the stagedresourceancestor indexes here because they
    # may not have been created as part of the data migration above. If they were not created,
    # then the downgrade would fail trying to drop the non-existent indexes.

    # The indexes and constraints will be dropped as part of the overall table drop that's done
    # as part of the downgrade in the `5474a47c77da_create_staged_resource_ancestor_link_table.py`
    # migration.
