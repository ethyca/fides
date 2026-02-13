import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, Optional

from loguru import logger
from redis.lock import Lock
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from fides.api.util.lock import get_redis_lock

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


def acquire_backfill_lock() -> Optional[Lock]:
    """
    Try to acquire the backfill lock.

    Returns the Lock object if acquired, None if another backfill is already running.
    Uses native Redis Lock for proper ownership tracking.
    """
    lock = get_redis_lock(BACKFILL_LOCK_KEY, timeout=BACKFILL_LOCK_TTL)

    if lock.acquire(blocking=False):
        logger.info(
            f"Acquired lock for '{BACKFILL_LOCK_KEY}' (TTL: {BACKFILL_LOCK_TTL}s)."
        )
        return lock

    logger.info(f"Failed to acquire lock for '{BACKFILL_LOCK_KEY}'.")
    return None


def refresh_backfill_lock(lock: Optional[Lock]) -> None:
    """
    Extend the lock TTL.

    Call this periodically during long backfills to prevent the lock from expiring
    while the backfill is still running.
    """
    if lock is not None and lock.owned():
        lock.extend(BACKFILL_LOCK_TTL)
        logger.debug(
            f"Refreshed lock for '{BACKFILL_LOCK_KEY}' (TTL: {BACKFILL_LOCK_TTL}s)."
        )


def release_backfill_lock(lock: Optional[Lock]) -> None:
    """Release the backfill lock if we own it."""
    if lock is not None and lock.owned():
        lock.release()
        logger.info(f"Released lock for '{BACKFILL_LOCK_KEY}'.")


def is_backfill_completed(db: Session, backfill_name: str) -> bool:
    """
    Check if a backfill has already been completed.

    Returns True if the backfill is recorded in backfill_history, False otherwise.
    """
    result = db.execute(
        text("SELECT 1 FROM backfill_history WHERE backfill_name = :name"),
        {"name": backfill_name},
    )
    return result.scalar() is not None


async def is_backfill_completed_async(db: AsyncSession, backfill_name: str) -> bool:
    """
    Async version of is_backfill_completed for use with AsyncSession.
    
    Check if a backfill has already been completed.
    Returns True if the backfill is recorded in backfill_history, False otherwise.
    """
    result = await db.execute(
        text("SELECT 1 FROM backfill_history WHERE backfill_name = :name"),
        {"name": backfill_name},
    )
    return result.scalar() is not None


def mark_backfill_completed(db: Session, backfill_name: str) -> None:
    """
    Record that a backfill has completed successfully.

    Uses ON CONFLICT DO NOTHING as a safety net for duplicate calls.
    """
    db.execute(
        text(
            "INSERT INTO backfill_history (backfill_name) VALUES (:name) "
            "ON CONFLICT (backfill_name) DO NOTHING"
        ),
        {"name": backfill_name},
    )
    db.commit()
    logger.info(f"Marked backfill '{backfill_name}' as completed in backfill_history")


@dataclass
class BackfillResult:
    """Tracks the result of a backfill operation."""

    name: str = ""
    total_updated: int = 0
    total_batches: int = 0
    failed_batches: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.failed_batches == 0

    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "COMPLETED WITH ERRORS"
        prefix = f"[{self.name}] " if self.name else ""
        result = f"{prefix}{status}: {self.total_updated} rows in {self.total_batches} batches"
        if self.failed_batches > 0:
            result += f" ({self.failed_batches} failed batches)"
        return result


def is_transient_error(error: Exception) -> bool:
    """
    Determine if an error is transient and worth retrying.

    Transient errors include connection issues, timeouts, and lock conflicts.
    """
    # OperationalError is a subclass of DBAPIError, so check it first
    # to immediately return True for connection errors, timeouts, deadlocks
    if isinstance(error, OperationalError):
        return True
    # For other DBAPIError subclasses, check the error message for transient indicators.
    # Some indicators overlap with OperationalError as a safety net for drivers that
    # might categorize certain transient errors differently.
    if isinstance(error, DBAPIError):
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
    fn: Callable[[], int],
    db: Session,
    batch_num: int,
    backfill_name: str = "backfill",
) -> int:
    """
    Execute a batch function with retry logic for transient errors.

    Args:
        fn: Function that executes one batch and returns rows_updated.
            Should handle its own commit.
        db: Database session (used for rollback on error)
        batch_num: Batch number for logging
        backfill_name: Name of the backfill operation for logging

    Returns the number of rows updated.
    Raises the last exception if all retries fail.
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES_PER_BATCH + 1):
        try:
            return fn()

        except SQLAlchemyError as e:
            last_error = e
            db.rollback()

            if is_transient_error(e) and attempt < MAX_RETRIES_PER_BATCH:
                wait_time = RETRY_BACKOFF_BASE**attempt
                logger.warning(
                    f"{backfill_name}: Batch {batch_num} attempt {attempt} failed "
                    f"with transient error: {e}. Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
            else:
                logger.error(
                    f"{backfill_name}: Batch {batch_num} failed after {attempt} attempts: {e}"
                )
                raise

    # Should not reach here, but just in case
    raise last_error  # type: ignore


def batched_backfill(
    name: str,
    pending_count_fn: Callable[[Session], int],
) -> Callable[[Callable[[Session, int], int]], Callable[..., BackfillResult]]:
    """
    Decorator that wraps a batch execution function with full backfill infrastructure.

    The decorated function should:
    - Accept (db: Session, batch_size: int) -> int
    - Execute ONE batch and return rows_updated
    - Handle its own commit

    The decorator provides:
    - Progress logging with rate/ETA
    - Retry logic for transient errors
    - Consecutive failure tracking
    - Lock refresh every 10 batches
    - Final summary logging

    Args:
        name: Name for logging (e.g., "stagedresource-is_leaf")
        pending_count_fn: Function that returns count of rows needing backfill

    Example:
        def get_pending_count(db: Session) -> int:
            result = db.execute(text("SELECT COUNT(*) FROM table WHERE col IS NULL"))
            return result.scalar() or 0

        @batched_backfill(
            name="table-column",
            pending_count_fn=get_pending_count,
        )
        def backfill_column(db: Session, batch_size: int) -> int:
            result = db.execute(text(UPDATE_QUERY), {"batch_size": batch_size})
            db.commit()
            return result.rowcount
    """

    def decorator(
        batch_fn: Callable[[Session, int], int],
    ) -> Callable[..., BackfillResult]:
        @wraps(batch_fn)
        def wrapper(
            db: Session,
            batch_size: int = BATCH_SIZE,
            batch_delay_seconds: float = BATCH_DELAY_SECONDS,
            lock: Optional[Lock] = None,
        ) -> BackfillResult:
            result = BackfillResult(name=name)

            # Check if this backfill has already been completed
            if is_backfill_completed(db, name):
                logger.debug(f"{name} backfill: Already completed, skipping")
                return result

            consecutive_failures = 0
            start_time = time.time()

            # Get initial count for progress logging
            try:
                pending_count = pending_count_fn(db)
            except SQLAlchemyError as e:
                result.errors.append(f"Failed to get initial count: {e}")
                logger.error(f"{name} backfill: Cannot start - {e}")
                return result

            if pending_count == 0:
                logger.debug(f"{name} backfill: No rows need backfilling")
                mark_backfill_completed(db, name)
                return result

            logger.info(
                f"{name} backfill: Starting backfill for {pending_count} rows "
                f"(batch_size={batch_size}, delay={batch_delay_seconds}s)"
            )

            while True:
                result.total_batches += 1
                batch_start = time.time()

                try:
                    rows_updated = execute_batch_with_retry(
                        fn=lambda: batch_fn(db, batch_size),
                        db=db,
                        batch_num=result.total_batches,
                        backfill_name=f"{name} backfill",
                    )
                    batch_duration = time.time() - batch_start
                    consecutive_failures = 0  # Reset on success

                    result.total_updated += rows_updated

                    if rows_updated > 0:
                        # Log progress and refresh lock every 10 batches or when batch completes
                        if result.total_batches % 10 == 0 or rows_updated < batch_size:
                            elapsed = time.time() - start_time
                            rate = result.total_updated / elapsed if elapsed > 0 else 0
                            remaining = pending_count - result.total_updated
                            eta = remaining / rate if rate > 0 else 0

                            progress_pct = (
                                f"{100 * result.total_updated / pending_count:.1f}%"
                                if pending_count > 0
                                else "100%"
                            )
                            logger.info(
                                f"{name} backfill: Progress {result.total_updated}/{pending_count} rows "
                                f"({progress_pct}) | "
                                f"Batch {result.total_batches} took {batch_duration:.2f}s | "
                                f"Rate: {rate:.0f} rows/s | "
                                f"ETA: {eta:.0f}s"
                            )

                            # Refresh the lock to prevent it from expiring during long backfills
                            refresh_backfill_lock(lock)

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
                            f"{name} backfill: Stopping after {consecutive_failures} consecutive failures. "
                            f"Last error: {e}"
                        )
                        break

                    logger.warning(
                        f"{name} backfill: {error_msg}. "
                        f"Consecutive failures: {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}. Continuing..."
                    )

                # Delay between batches to reduce database pressure
                time.sleep(batch_delay_seconds)

            total_duration = time.time() - start_time

            if result.success:
                logger.info(
                    f"{name} backfill: Completed successfully! "
                    f"Updated {result.total_updated} rows in {result.total_batches} batches "
                    f"({total_duration:.1f}s total)"
                )
                mark_backfill_completed(db, name)
            else:
                logger.warning(
                    f"{name} backfill: Completed with errors. "
                    f"Updated {result.total_updated} rows in {result.total_batches} batches "
                    f"({result.failed_batches} failed). Duration: {total_duration:.1f}s. "
                    f"Errors: {result.errors}"
                )

            return result

        return wrapper

    return decorator
