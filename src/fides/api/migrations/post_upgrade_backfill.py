import time
from dataclasses import dataclass, field
from typing import List

from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from fides.api.db.session import get_db_session
from fides.api.tasks.scheduled.scheduler import scheduler
from fides.api.util.cache import get_cache
from fides.config import CONFIG

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

POST_UPGRADE_BACKFILL = "post_upgrade_backfill"

# Batch configuration - tuned for minimal database lock impact
BATCH_SIZE = 5000  # Smaller batches = shorter lock duration per batch
BATCH_DELAY_SECONDS = 1.0  # 1s pause between batches to let other transactions through

# Error handling configuration
MAX_RETRIES_PER_BATCH = 3  # Retry transient errors up to 3 times
RETRY_BACKOFF_BASE = 2.0  # Exponential backoff base (2s, 4s, 8s)
MAX_CONSECUTIVE_FAILURES = 5  # Stop after 5 consecutive failed batches

# Redis lock configuration to prevent concurrent backfills
BACKFILL_LOCK_KEY = "fides:backfill:running"
BACKFILL_LOCK_TTL = 300  # 5 minutes TTL, refreshed every 10 batches


def acquire_backfill_lock() -> bool:
    """
    Try to acquire the backfill lock.

    Returns True if the lock was acquired, False if another backfill is already running.
    Uses Redis SET with NX (only set if not exists) and EX (expiration).
    """
    cache = get_cache()
    result = cache.set(BACKFILL_LOCK_KEY, "1", ex=BACKFILL_LOCK_TTL, nx=True)
    return bool(result)


def refresh_backfill_lock() -> None:
    """
    Extend the lock TTL.

    Call this periodically during long backfills to prevent the lock from expiring
    while the backfill is still running.
    """
    cache = get_cache()
    cache.expire(BACKFILL_LOCK_KEY, BACKFILL_LOCK_TTL)


def release_backfill_lock() -> None:
    """Release the backfill lock."""
    cache = get_cache()
    cache.delete(BACKFILL_LOCK_KEY)


@dataclass
class BackfillResult:
    """Tracks the result of a backfill operation."""

    total_updated: int = 0
    total_batches: int = 0
    failed_batches: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.failed_batches == 0

    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "COMPLETED WITH ERRORS"
        result = f"{status}: {self.total_updated} rows in {self.total_batches} batches"
        if self.failed_batches > 0:
            result += f" ({self.failed_batches} failed batches)"
        return result


def is_transient_error(error: Exception) -> bool:
    """
    Determine if an error is transient and worth retrying.

    Transient errors include connection issues, timeouts, and lock conflicts.
    """
    if isinstance(error, OperationalError):
        # Connection errors, timeouts, deadlocks
        return True
    if isinstance(error, DBAPIError):
        # Check for specific error codes that are transient
        error_str = str(error).lower()
        transient_indicators = [
            "connection",
            "timeout",
            "deadlock",
            "lock wait",
            "too many connections",
            "server closed",
            "lost connection",
        ]
        return any(indicator in error_str for indicator in transient_indicators)
    return False


def execute_batch_with_retry(
    db: Session,
    batch_num: int,
    batch_size: int = BATCH_SIZE,
) -> int:
    """
    Execute a single batch with retry logic for transient errors.

    Returns the number of rows updated.
    Raises the last exception if all retries fail.
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES_PER_BATCH + 1):
        try:
            result = db.execute(
                text(
                    """
                    UPDATE stagedresource
                    SET is_leaf = (
                        resource_type = 'Field'
                        AND children = '{}'
                        AND (meta->>'data_type' IS NULL OR meta->>'data_type' != 'object')
                    )
                    WHERE id IN (
                        SELECT id FROM stagedresource
                        WHERE is_leaf IS NULL
                        LIMIT :batch_size
                        FOR UPDATE SKIP LOCKED
                    )
                    """
                ),
                {"batch_size": batch_size},
            )
            db.commit()
            return result.rowcount

        except SQLAlchemyError as e:
            last_error = e
            db.rollback()

            if is_transient_error(e) and attempt < MAX_RETRIES_PER_BATCH:
                wait_time = RETRY_BACKOFF_BASE**attempt
                logger.warning(
                    f"is_leaf backfill: Batch {batch_num} attempt {attempt} failed "
                    f"with transient error: {e}. Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
            else:
                logger.error(
                    f"is_leaf backfill: Batch {batch_num} failed after {attempt} attempts: {e}"
                )
                raise

    # Should not reach here, but just in case
    raise last_error  # type: ignore


def get_pending_is_leaf_count(db: Session) -> int:
    """Returns the count of rows that still need is_leaf backfill."""
    try:
        result = db.execute(
            text("SELECT COUNT(*) FROM stagedresource WHERE is_leaf IS NULL")
        )
        return result.scalar() or 0
    except SQLAlchemyError as e:
        logger.error(f"is_leaf backfill: Failed to get pending count: {e}")
        raise


def backfill_is_leaf(
    db: Session,
    batch_size: int = BATCH_SIZE,
    batch_delay_seconds: float = BATCH_DELAY_SECONDS,
) -> BackfillResult:
    """
    Backfill is_leaf column for all rows where it's NULL.

    Runs in batches with delays to minimize database lock impact.
    Includes retry logic for transient errors and tracks failures.

    Args:
        db: Database session
        batch_size: Number of rows to update per batch (default: 5000)
        batch_delay_seconds: Delay between batches in seconds (default: 1.0)

    Returns a BackfillResult with statistics and any errors encountered.
    """
    result = BackfillResult()
    consecutive_failures = 0
    start_time = time.time()

    # Get initial count for progress logging
    try:
        pending_count = get_pending_is_leaf_count(db)
    except SQLAlchemyError as e:
        result.errors.append(f"Failed to get initial count: {e}")
        logger.error(f"is_leaf backfill: Cannot start - {e}")
        return result

    if pending_count == 0:
        logger.debug("is_leaf backfill: No rows need backfilling")
        return result

    logger.info(
        f"is_leaf backfill: Starting backfill for {pending_count} rows "
        f"(batch_size={batch_size}, delay={batch_delay_seconds}s)"
    )

    while True:
        result.total_batches += 1
        batch_start = time.time()

        try:
            rows_updated = execute_batch_with_retry(
                db, result.total_batches, batch_size
            )
            batch_duration = time.time() - batch_start
            consecutive_failures = 0  # Reset on success

            result.total_updated += rows_updated

            if rows_updated > 0:
                # Log progress and refresh lock every 10 batches or when a batch completes
                if result.total_batches % 10 == 0 or rows_updated < batch_size:
                    elapsed = time.time() - start_time
                    rate = result.total_updated / elapsed if elapsed > 0 else 0
                    remaining = pending_count - result.total_updated
                    eta = remaining / rate if rate > 0 else 0

                    logger.info(
                        f"is_leaf backfill: Progress {result.total_updated}/{pending_count} rows "
                        f"({100 * result.total_updated / pending_count:.1f}%) | "
                        f"Batch {result.total_batches} took {batch_duration:.2f}s | "
                        f"Rate: {rate:.0f} rows/s | "
                        f"ETA: {eta:.0f}s"
                    )

                    # Refresh the lock to prevent it from expiring during long backfills
                    refresh_backfill_lock()

            if rows_updated < batch_size:
                # No more rows to process
                break

        except SQLAlchemyError as e:
            result.failed_batches += 1
            consecutive_failures += 1
            error_msg = f"Batch {result.total_batches} failed: {e}"
            result.errors.append(error_msg)

            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                logger.error(
                    f"is_leaf backfill: Stopping after {consecutive_failures} consecutive failures. "
                    f"Last error: {e}"
                )
                break

            logger.warning(
                f"is_leaf backfill: {error_msg}. "
                f"Consecutive failures: {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}. Continuing..."
            )

        # Delay between batches to reduce database pressure
        time.sleep(batch_delay_seconds)

    total_duration = time.time() - start_time

    if result.success:
        logger.info(
            f"is_leaf backfill: Completed successfully! "
            f"Updated {result.total_updated} rows in {result.total_batches} batches "
            f"({total_duration:.1f}s total)"
        )
    else:
        logger.warning(
            f"is_leaf backfill: Completed with errors. "
            f"Updated {result.total_updated} rows in {result.total_batches} batches "
            f"({result.failed_batches} failed). Duration: {total_duration:.1f}s. "
            f"Errors: {result.errors}"
        )

    return result


def run_all_backfills(
    db: Session,
    batch_size: int = BATCH_SIZE,
    batch_delay_seconds: float = BATCH_DELAY_SECONDS,
) -> List[BackfillResult]:
    """
    Run all pending backfill tasks.

    Add new backfill functions here as needed.

    Args:
        db: Database session
        batch_size: Number of rows to update per batch
        batch_delay_seconds: Delay between batches in seconds

    Returns a list of BackfillResult objects for each backfill.
    """
    results: List[BackfillResult] = []

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
) -> List[BackfillResult]:
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
