"""staged resource ancestor link data migration

Revision ID: bf713b5a021d
Revises: 5474a47c77da
Create Date: 2025-06-03 09:44:58.769535

"""

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

    # Bulk insert all ancestor links in batches of 10000
    if ancestor_links:
        insert_query = """
        INSERT INTO stagedresourceancestor (id, ancestor_urn, descendant_urn)
        VALUES (
            encode(digest(:ancestor_urn || :descendant_urn, 'sha256'), 'hex'),
            :ancestor_urn,
            :descendant_urn
        )
        ON CONFLICT DO NOTHING
        """

        batch_size = 100000
        for i in range(0, len(ancestor_links), batch_size):
            batch = ancestor_links[i : i + batch_size]
            conn.execute(sa.text(insert_query), batch)
            logger.info(
                f"Inserted batch of {len(batch)} ancestor links ({i + len(batch)}/{len(ancestor_links)} total)"
            )

    logger.info(
        f"Completed populating {len(ancestor_links)} staged resource ancestor links"
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
