"""Backfill script for the is_leaf column on StagedResource."""

from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fides.api.migrations.backfill_scripts.utils import batched_backfill


def get_pending_is_leaf_count(db: Session) -> int:
    """Returns the count of rows that still need is_leaf backfill."""
    try:
        result = db.execute(
            text("SELECT COUNT(*) FROM stagedresource WHERE is_leaf IS NULL AND resource_type IN ('Database', 'Schema', 'Table', 'Field', 'Endpoint')")
        )
        return result.scalar() or 0
    except SQLAlchemyError as e:
        logger.error(f"stagedresource-is_leaf backfill: Failed to get pending count: {e}")
        raise


@batched_backfill(
    name="stagedresource-is_leaf",
    pending_count_fn=get_pending_is_leaf_count,
)
def backfill_stagedresource_is_leaf(db: Session, batch_size: int) -> int:
    """
    Execute one batch of is_leaf backfill.

    Sets is_leaf=True for Field resources that have no children and
    are not of data_type 'object'. All other resources get is_leaf=False.
    """
    # SQL query to update one batch of rows
    is_leaf_query = """
        UPDATE stagedresource
        SET is_leaf = (
            resource_type = 'Field'
            AND children = '{}'
            AND (meta->>'data_type' IS NULL OR meta->>'data_type' != 'object')
        )
        WHERE id IN (
            SELECT id FROM stagedresource
            WHERE is_leaf IS NULL
            AND resource_type IN ('Database', 'Schema', 'Table', 'Field', 'Endpoint')
            LIMIT :batch_size
            FOR UPDATE SKIP LOCKED
        )
    """

    result = db.execute(text(is_leaf_query), {"batch_size": batch_size})
    db.commit()
    return result.rowcount
