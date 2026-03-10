"""Backfill script for the distance column on StagedResourceAncestor."""

from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fides.api.migrations.backfill_scripts.utils import batched_backfill


def get_pending_distance_count(db: Session) -> int:
    """Returns the count of rows that still need distance backfill."""
    try:
        result = db.execute(
            text("SELECT COUNT(*) FROM stagedresourceancestor WHERE distance IS NULL")
        )
        return result.scalar() or 0
    except SQLAlchemyError as e:
        logger.error(
            f"stagedresourceancestor-distance backfill: Failed to get pending count: {e}"
        )
        raise


# SQL expression to calculate distance between ancestor and descendant URNs.
# Extracted as a constant so tests can verify this exact calculation logic in isolation
# without running the full backfill (UPDATE/batching/locking). This ensures tests break
# if the calculation changes, maintaining single source of truth.
DISTANCE_CALCULATION_EXPR = """
    array_length(string_to_array(descendant_urn, '.'), 1) - array_length(string_to_array(ancestor_urn, '.'), 1)
"""


@batched_backfill(
    name="stagedresourceancestor-distance",
    pending_count_fn=get_pending_distance_count,
)
def backfill_stagedresourceancestor_distance(db: Session, batch_size: int) -> int:
    """
    Execute one batch of distance backfill.

    Calculates distance by counting URN segments. The URN structure naturally
    encodes the hierarchy depth:
    - Database: 'db' (1 segment)
    - Schema: 'db.schema' (2 segments)
    - Table: 'db.schema.table' (3 segments)
    - Field: 'db.schema.table.field' (4 segments)
    - Nested field: 'db.schema.table.field1.field2' (5+ segments, arbitrary depth)

    Distance = descendant_urn_segments - ancestor_urn_segments

    This works for all cases including deeply nested fields where the URN directly
    reflects the nesting depth.
    """
    # SQL query to calculate distance directly from URN segment counts
    distance_query = f"""
        UPDATE stagedresourceancestor
        SET distance = ({DISTANCE_CALCULATION_EXPR})
        WHERE id IN (
            SELECT id
            FROM stagedresourceancestor
            WHERE distance IS NULL
            LIMIT :batch_size
            FOR UPDATE SKIP LOCKED
        )
    """

    result = db.execute(text(distance_query), {"batch_size": batch_size})
    db.commit()
    return result.rowcount
