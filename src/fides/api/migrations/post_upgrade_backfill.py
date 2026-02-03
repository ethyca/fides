"""
This utility is used to backfill data that was deferred as part of a standard
Fides/Alembic migration due to table size.

For large tables, running UPDATE statements in migrations can cause long-running
transactions that block other operations. This module provides a mechanism to
run backfills in small batches with delays, minimizing database lock contention.

The backfill tasks are:
- Idempotent: Safe to run multiple times
- Resumable: Can be stopped and restarted, will pick up where it left off
- Non-blocking: Uses small batches with delays and SKIP LOCKED to minimize impact
- Error-resilient: Retries transient errors, tracks failures, fails gracefully
"""

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.db.session import get_db_session
from fides.api.migrations.backfill_scripts.backfill_is_leaf import backfill_is_leaf
from fides.api.migrations.backfill_scripts.utils import (
    BACKFILL_LOCK_KEY,
    BATCH_DELAY_SECONDS,
    BATCH_SIZE,
    BackfillResult,
    acquire_backfill_lock,
    release_backfill_lock,
)
from fides.api.tasks.scheduled.scheduler import scheduler
from fides.api.util.cache import get_cache
from fides.config import CONFIG

POST_UPGRADE_BACKFILL = "post_upgrade_backfill"


def is_backfill_running() -> bool:
    """
    Check if a backfill is currently running.

    Returns True if the backfill lock exists in Redis, False otherwise.

    Note: This checks for the presence of the Redis lock. If a backfill process
    crashes without releasing the lock, this may return True for up to 5 minutes
    (the lock TTL) even though no backfill is actually running.
    """
    cache = get_cache()
    return bool(cache.exists(BACKFILL_LOCK_KEY))


def run_all_backfills(
    db: Session,
    batch_size: int = BATCH_SIZE,
    batch_delay_seconds: float = BATCH_DELAY_SECONDS,
) -> list[BackfillResult]:
    """
    Run all pending backfill tasks.

    Add new backfill functions here as needed.

    Args:
        db: Database session
        batch_size: Number of rows to update per batch
        batch_delay_seconds: Delay between batches in seconds

    Returns a list of BackfillResult objects for each backfill.
    """
    results: list[BackfillResult] = []

    # Backfill is_leaf column (added in migration d05acec55c64)
    results.append(backfill_is_leaf(db, batch_size, batch_delay_seconds))

    # Add future backfills here:
    # results.append(backfill_some_other_column(db, batch_size, batch_delay_seconds))

    return results


def post_upgrade_backfill_task() -> None:
    """
    Task for backfilling data that was deferred from migrations.

    This task is kicked off as a background task during application startup,
    after standard migrations and index creation have been applied.

    The backfills are idempotent - if all data is already backfilled,
    this is effectively a no-op.

    Uses a Redis lock to prevent concurrent backfills.
    """
    logger.info("Starting post-upgrade backfill task")

    if not acquire_backfill_lock():
        logger.info(
            "Post-upgrade backfill: Another backfill is already running, skipping"
        )
        return

    try:
        SessionLocal = get_db_session(CONFIG)
        with SessionLocal() as db:
            results = run_all_backfills(db)

        # Log summary
        all_success = all(r.success for r in results)
        total_updated = sum(r.total_updated for r in results)
        total_errors = sum(len(r.errors) for r in results)

        if all_success:
            logger.info(
                f"Post-upgrade backfill task completed successfully. "
                f"Total rows updated: {total_updated}"
            )
        else:
            logger.warning(
                f"Post-upgrade backfill task completed with errors. "
                f"Total rows updated: {total_updated}, Total errors: {total_errors}"
            )

    except Exception as e:
        logger.error(f"Post-upgrade backfill task failed with unexpected error: {e}")
        raise
    finally:
        release_backfill_lock()


def initiate_post_upgrade_backfill() -> None:
    """
    Initiates scheduler for post-upgrade backfill tasks.

    Called during application startup after migrations and index creation.
    """
    if CONFIG.test_mode:
        logger.debug("Skipping post upgrade backfill in test mode")
        return

    assert scheduler.running, "Scheduler is not running! Cannot run backfill tasks."

    logger.info("Initiating scheduler for post-upgrade backfill")
    scheduler.add_job(
        func=post_upgrade_backfill_task,
        id=POST_UPGRADE_BACKFILL,
    )


def run_backfill_manually(
    batch_size: int = BATCH_SIZE,
    batch_delay_seconds: float = BATCH_DELAY_SECONDS,
) -> list[BackfillResult]:
    """
    Entry point for running backfills manually (e.g., from API or CLI).

    The caller must acquire the lock before calling this function.
    This function will release the lock when done.

    Args:
        batch_size: Number of rows to update per batch (default: 5000)
        batch_delay_seconds: Delay between batches in seconds (default: 1.0)

    Returns a list of BackfillResult objects for each backfill.
    """
    logger.info(
        f"Running post-upgrade backfill manually "
        f"(batch_size={batch_size}, delay={batch_delay_seconds}s)"
    )

    try:
        SessionLocal = get_db_session(CONFIG)
        with SessionLocal() as db:
            results = run_all_backfills(db, batch_size, batch_delay_seconds)

        all_success = all(r.success for r in results)
        if all_success:
            logger.info("Manual backfill completed successfully")
        else:
            logger.warning("Manual backfill completed with errors")

        return results
    finally:
        release_backfill_lock()
