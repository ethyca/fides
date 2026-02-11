"""Tests for post_upgrade_backfill module."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from fides.api.migrations.backfill_scripts.utils import (
    BACKFILL_LOCK_KEY,
    BACKFILL_LOCK_TTL,
    BackfillResult,
    acquire_backfill_lock,
    batched_backfill,
    execute_batch_with_retry,
    is_backfill_completed,
    is_transient_error,
    mark_backfill_completed,
    refresh_backfill_lock,
    release_backfill_lock,
)


class TestBackfillResult:
    """Tests for BackfillResult dataclass."""

    @pytest.mark.parametrize(
        "failed_batches,expected_success",
        [(0, True), (1, False)],
        ids=["no_failures", "with_failures"],
    )
    def test_success_property(self, failed_batches, expected_success):
        """Verify success property based on failed_batches count."""
        result = BackfillResult(
            name="test",
            total_updated=100,
            total_batches=5,
            failed_batches=failed_batches,
        )
        assert result.success is expected_success


class TestIsTransientError:
    """Tests for is_transient_error function."""

    @pytest.mark.parametrize(
        "error,expected",
        [
            # OperationalError is always transient
            (OperationalError("connection lost", None, None), True),
            # DBAPIError with transient keywords
            (DBAPIError("connection refused", None, None), True),
            (DBAPIError("timeout exceeded", None, None), True),
            (DBAPIError("deadlock detected", None, None), True),
            # DBAPIError without transient keywords
            (DBAPIError("unique constraint violated", None, None), False),
            # Non-database errors are not transient
            (ValueError("not a db error"), False),
        ],
    )
    def test_is_transient_error(self, error, expected):
        """Verify is_transient_error correctly identifies transient errors."""
        assert is_transient_error(error) == expected


class TestBackfillLock:
    """Tests for backfill lock functions."""

    def test_acquire_backfill_lock_success(self):
        """Verify lock acquisition returns lock object when successful."""
        mock_lock = MagicMock()
        mock_lock.acquire.return_value = True

        with patch(
            "fides.api.migrations.backfill_scripts.utils.get_redis_lock",
            return_value=mock_lock,
        ) as mock_get_lock:
            result = acquire_backfill_lock()

        mock_get_lock.assert_called_once_with(
            BACKFILL_LOCK_KEY, timeout=BACKFILL_LOCK_TTL
        )
        assert result is mock_lock
        mock_lock.acquire.assert_called_once_with(blocking=False)

    def test_acquire_backfill_lock_failure(self):
        """Verify lock acquisition returns None when lock is already held."""
        mock_lock = MagicMock()
        mock_lock.acquire.return_value = False

        with patch(
            "fides.api.migrations.backfill_scripts.utils.get_redis_lock",
            return_value=mock_lock,
        ) as mock_get_lock:
            result = acquire_backfill_lock()

        mock_get_lock.assert_called_once_with(
            BACKFILL_LOCK_KEY, timeout=BACKFILL_LOCK_TTL
        )
        assert result is None
        mock_lock.acquire.assert_called_once_with(blocking=False)

    @pytest.mark.parametrize("owned", [True, False], ids=["owned", "not_owned"])
    def test_release_backfill_lock(self, owned):
        """Verify lock is released when owned, skipped when not owned."""
        mock_lock = MagicMock()
        mock_lock.owned.return_value = owned

        release_backfill_lock(mock_lock)

        if owned:
            mock_lock.release.assert_called_once()
        else:
            mock_lock.release.assert_not_called()

    @pytest.mark.parametrize("owned", [True, False], ids=["owned", "not_owned"])
    def test_refresh_backfill_lock(self, owned):
        """Verify lock TTL is extended when owned, skipped when not owned."""
        mock_lock = MagicMock()
        mock_lock.owned.return_value = owned

        refresh_backfill_lock(mock_lock)

        if owned:
            mock_lock.extend.assert_called_once_with(BACKFILL_LOCK_TTL)
        else:
            mock_lock.extend.assert_not_called()


class TestBackfillHistory:
    """Tests for backfill completion tracking functions."""

    @pytest.mark.parametrize(
        "record_exists",
        [True, False],
        ids=["record_exists", "record_not_exists"],
    )
    def test_is_backfill_completed(self, db: Session, record_exists):
        """Verify is_backfill_completed() checks database correctly."""
        # Use unique name per test case to avoid conflicts between parametrized runs
        backfill_name = f"test-is-backfill-completed-{record_exists}"

        # Clean up any leftover record from previous runs
        db.execute(
            text("DELETE FROM backfill_history WHERE backfill_name = :name"),
            {"name": backfill_name},
        )
        db.commit()

        if record_exists:
            # Insert a record directly into backfill_history
            db.execute(
                text("INSERT INTO backfill_history (backfill_name) VALUES (:name)"),
                {"name": backfill_name},
            )
            db.commit()

        # Execute
        result = is_backfill_completed(db, backfill_name)

        # Verify
        assert result == record_exists

    def test_mark_backfill_completed_inserts_record(self, db: Session):
        """Verify mark_backfill_completed() inserts and commits record."""
        backfill_name = "test-mark-completed-insert"

        # Clean up any leftover record from previous runs (DELETE is safe even if record doesn't exist)
        db.execute(
            text("DELETE FROM backfill_history WHERE backfill_name = :name"),
            {"name": backfill_name},
        )
        db.commit()

        # Execute
        mark_backfill_completed(db, backfill_name)

        # Verify record now exists using direct SQL
        result = db.execute(
            text("SELECT COUNT(*) FROM backfill_history WHERE backfill_name = :name"),
            {"name": backfill_name},
        ).scalar()
        assert result == 1

    def test_mark_backfill_completed_idempotency(self, db: Session):
        """Verify mark_backfill_completed() is idempotent (ON CONFLICT DO NOTHING)."""
        backfill_name = "test-mark-completed-idempotent"

        # Insert once
        mark_backfill_completed(db, backfill_name)

        # Get timestamp and count after first insert
        result = db.execute(
            text(
                "SELECT COUNT(*), completed_at FROM backfill_history WHERE backfill_name = :name GROUP BY completed_at"
            ),
            {"name": backfill_name},
        ).first()
        assert result[0] == 1
        first_timestamp = result[1]

        # Insert again - should not raise error due to ON CONFLICT DO NOTHING
        mark_backfill_completed(db, backfill_name)

        # Verify still only one record (not duplicated) and timestamp unchanged
        result = db.execute(
            text(
                "SELECT COUNT(*), completed_at FROM backfill_history WHERE backfill_name = :name GROUP BY completed_at"
            ),
            {"name": backfill_name},
        ).first()
        assert result[0] == 1
        assert result[1] == first_timestamp  # Timestamp should not change


class TestExecuteBatchWithRetry:
    """Tests for execute_batch_with_retry() function."""

    def test_success_path(self):
        """Verify function executes and returns value successfully."""
        mock_db = MagicMock()
        mock_fn = MagicMock(return_value=42)

        # Execute
        result = execute_batch_with_retry(mock_fn, mock_db, batch_num=1)

        # Verify
        assert result == 42
        mock_fn.assert_called_once()
        mock_db.rollback.assert_not_called()

    @pytest.mark.parametrize(
        "is_transient,expected_attempts",
        [
            (True, 3),  # Transient error: retries 3 times
            (False, 1),  # Non-transient error: fails immediately
        ],
        ids=["transient_error", "non_transient_error"],
    )
    def test_retry_behavior(self, is_transient, expected_attempts):
        """Verify retry logic for transient and non-transient errors."""
        mock_db = MagicMock()
        mock_fn = MagicMock(side_effect=SQLAlchemyError("Test error"))

        with (
            patch(
                "fides.api.migrations.backfill_scripts.utils.is_transient_error",
                return_value=is_transient,
            ),
            patch(
                "fides.api.migrations.backfill_scripts.utils.time.sleep"
            ) as mock_sleep,
        ):
            # Execute and verify exception is raised
            with pytest.raises(SQLAlchemyError, match="Test error"):
                execute_batch_with_retry(
                    mock_fn, mock_db, batch_num=1, backfill_name="test-backfill"
                )

            # Verify retry attempts
            assert mock_fn.call_count == expected_attempts

            # Verify rollback is called on each failure
            assert mock_db.rollback.call_count == expected_attempts

            if is_transient:
                # Verify exponential backoff: 2^1=2s, 2^2=4s (stops before 3rd sleep)
                assert mock_sleep.call_count == expected_attempts - 1
                sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
                assert sleep_calls == [2.0, 4.0]
            else:
                # Non-transient should not sleep (fails immediately)
                mock_sleep.assert_not_called()


class TestBatchedBackfillDecorator:
    """Tests for @batched_backfill decorator."""

    @pytest.mark.parametrize(
        "exit_reason,is_completed,pending_count",
        [
            ("already_completed", True, 100),
            ("no_pending_rows", False, 0),
        ],
        ids=["already_completed", "no_pending_rows"],
    )
    def test_early_exit_conditions(self, exit_reason, is_completed, pending_count):
        """Verify decorator returns early for completion cases."""
        mock_db = MagicMock()
        mock_pending_count_fn = MagicMock(return_value=pending_count)
        mock_batch_fn = MagicMock(return_value=0)

        # Create a decorated function
        @batched_backfill(
            name="test-backfill",
            pending_count_fn=mock_pending_count_fn,
        )
        def test_backfill(db, batch_size):
            return mock_batch_fn(db, batch_size)

        with (
            patch(
                "fides.api.migrations.backfill_scripts.utils.is_backfill_completed",
                return_value=is_completed,
            ),
            patch(
                "fides.api.migrations.backfill_scripts.utils.mark_backfill_completed"
            ) as mock_mark,
            patch(
                "fides.api.migrations.backfill_scripts.utils.execute_batch_with_retry"
            ) as mock_execute,
        ):
            # Execute
            result = test_backfill(mock_db)

            # Verify early exit with empty result
            assert result.name == "test-backfill"
            assert result.total_updated == 0
            assert result.total_batches == 0
            assert result.success is True

            # Verify execute_batch_with_retry was never called (no batch processing)
            mock_execute.assert_not_called()

            if exit_reason == "already_completed":
                # When already completed, should not check pending count
                mock_pending_count_fn.assert_not_called()
                mock_mark.assert_not_called()
            else:
                # When no pending rows, should check count then mark as completed
                mock_pending_count_fn.assert_called_once()
                mock_mark.assert_called_once_with(mock_db, "test-backfill")

    def test_batch_processing_completion(self):
        """Verify batch processing continues until completion."""
        mock_db = MagicMock()
        mock_lock = MagicMock()

        # Batch function returns decreasing values: 100, 100, 50 (< batch_size)
        batch_returns = [100, 100, 50]
        call_count = [0]

        def mock_batch_fn(db, batch_size):
            result = batch_returns[call_count[0]]
            call_count[0] += 1
            return result

        @batched_backfill(
            name="test-backfill",
            pending_count_fn=lambda db: 250,
        )
        def test_backfill(db, batch_size):
            return mock_batch_fn(db, batch_size)

        with (
            patch(
                "fides.api.migrations.backfill_scripts.utils.is_backfill_completed",
                return_value=False,
            ),
            patch(
                "fides.api.migrations.backfill_scripts.utils.mark_backfill_completed"
            ) as mock_mark,
            patch(
                "fides.api.migrations.backfill_scripts.utils.execute_batch_with_retry"
            ) as mock_execute,
            patch(
                "fides.api.migrations.backfill_scripts.utils.refresh_backfill_lock"
            ) as mock_refresh,
            patch(
                "fides.api.migrations.backfill_scripts.utils.time.sleep"
            ) as mock_sleep,
        ):
            # Setup execute_batch_with_retry to pass through to our mock function
            mock_execute.side_effect = lambda fn, **kwargs: fn()

            # Execute
            result = test_backfill(
                mock_db, batch_size=100, batch_delay_seconds=0.5, lock=mock_lock
            )

            # Verify BackfillResult tracking
            assert result.name == "test-backfill"
            assert result.total_updated == 250  # 100 + 100 + 50
            assert result.total_batches == 3
            assert result.failed_batches == 0
            assert result.success is True
            assert len(result.errors) == 0

            # Verify batch delay was respected (sleep happens after each batch, but not after the last one
            # when rows_updated < batch_size triggers a break)
            assert mock_sleep.call_count == 2
            for call in mock_sleep.call_args_list:
                assert call[0][0] == 0.5

            # Verify lock refresh was called on the final batch (rows_updated < batch_size triggers refresh)
            # Refresh happens every 10 batches OR on the final batch
            mock_refresh.assert_called_once_with(mock_lock)

            # Verify marked as completed
            mock_mark.assert_called_once_with(mock_db, "test-backfill")

    def test_lock_refresh_timing(self):
        """Verify lock is refreshed every 10 batches."""
        mock_db = MagicMock()
        mock_lock = MagicMock()

        # Create 25 batches to trigger refresh at batch 10 and 20
        batch_returns = [100] * 24 + [50]  # 25 batches total

        @batched_backfill(
            name="test-backfill",
            pending_count_fn=lambda db: 2450,
        )
        def test_backfill(db, batch_size):
            return batch_returns.pop(0)

        with (
            patch(
                "fides.api.migrations.backfill_scripts.utils.is_backfill_completed",
                return_value=False,
            ),
            patch(
                "fides.api.migrations.backfill_scripts.utils.mark_backfill_completed"
            ),
            patch(
                "fides.api.migrations.backfill_scripts.utils.execute_batch_with_retry"
            ) as mock_execute,
            patch(
                "fides.api.migrations.backfill_scripts.utils.refresh_backfill_lock"
            ) as mock_refresh,
            patch("fides.api.migrations.backfill_scripts.utils.time.sleep"),
        ):
            # Setup execute_batch_with_retry to pass through to our function
            call_count = [0]

            def execute_side_effect(fn, **kwargs):
                call_count[0] += 1
                return (
                    batch_returns[call_count[0] - 1]
                    if call_count[0] <= len(batch_returns)
                    else 50
                )

            mock_execute.side_effect = execute_side_effect

            # Execute
            result = test_backfill(mock_db, batch_size=100, lock=mock_lock)

            # Verify lock refresh was called at batches 10, 20, and 25 (final batch)
            # The refresh happens every 10 batches or when rows_updated < batch_size
            assert mock_refresh.call_count >= 2  # At least at batch 10 and 20

    @pytest.mark.parametrize(
        "failure_pattern,expected_stopped_early",
        [
            (
                [1, 3],
                False,
            ),  # Intermittent failures (batches 1 and 3 fail, but completes)
            ([1, 2, 3, 4, 5], True),  # 5 consecutive failures (stops early)
        ],
        ids=["intermittent_failures", "consecutive_failures"],
    )
    def test_failure_handling(self, failure_pattern, expected_stopped_early):
        """Verify failure handling for intermittent and consecutive failures.

        Note: BackfillResult.success is True only if failed_batches == 0,
        so both scenarios result in success=False. The key difference is whether
        the backfill stopped early (consecutive failures) or completed all rows
        (intermittent failures)."""
        mock_db = MagicMock()
        call_count = [0]
        successful_batches = [0]

        @batched_backfill(
            name="test-backfill",
            pending_count_fn=lambda db: 1000,
        )
        def test_backfill(db, batch_size):
            call_count[0] += 1
            if call_count[0] in failure_pattern:
                raise SQLAlchemyError("Batch failed")

            # Track successful batches and return smaller value on last batch to trigger exit
            successful_batches[0] += 1
            if successful_batches[0] >= 10:  # 1000 rows / 100 per batch = 10 batches
                return 50  # Return less than batch_size to trigger exit
            return 100

        with (
            patch(
                "fides.api.migrations.backfill_scripts.utils.is_backfill_completed",
                return_value=False,
            ),
            patch(
                "fides.api.migrations.backfill_scripts.utils.mark_backfill_completed"
            ),
            patch(
                "fides.api.migrations.backfill_scripts.utils.execute_batch_with_retry"
            ) as mock_execute,
            patch("fides.api.migrations.backfill_scripts.utils.time.sleep"),
        ):
            # Setup execute_batch_with_retry to pass through exceptions
            def execute_side_effect(fn, **kwargs):
                return fn()

            mock_execute.side_effect = execute_side_effect

            # Execute
            result = test_backfill(mock_db, batch_size=100)

            # Verify result tracking
            assert result.name == "test-backfill"
            # Both scenarios have failed batches, so success is False
            assert result.success is False
            assert result.failed_batches == len(failure_pattern)
            assert len(result.errors) == len(failure_pattern)

            if not expected_stopped_early:
                # Intermittent failures: should continue processing and complete
                assert result.total_batches > len(failure_pattern)
                assert result.total_updated == 950  # 9 batches * 100 + 1 batch * 50
            else:
                # Consecutive failures: should stop at MAX_CONSECUTIVE_FAILURES (5)
                assert result.total_batches == 5
                assert result.total_updated == 0  # No successful batches
