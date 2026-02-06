"""Tests for post_upgrade_backfill module."""

from unittest.mock import MagicMock, patch

import pytest

from fides.api.migrations.backfill_scripts.utils import BackfillResult
from fides.api.migrations.post_upgrade_backfill import (
    post_upgrade_backfill_task,
    run_backfill_manually,
)


class TestPostUpgradeBackfillTask:
    """Tests for post_upgrade_backfill_task() function."""

    @pytest.mark.parametrize(
        "lock_acquired",
        [True, False],
        ids=["lock_acquired", "lock_unavailable"],
    )
    def test_lock_acquisition(self, lock_acquired):
        """Verify lock acquisition behavior and graceful skip when unavailable."""
        mock_lock = MagicMock() if lock_acquired else None

        with patch(
            "fides.api.migrations.post_upgrade_backfill.acquire_backfill_lock",
            return_value=mock_lock,
        ) as mock_acquire, patch(
            "fides.api.migrations.post_upgrade_backfill.get_db_session"
        ) as mock_get_db, patch(
            "fides.api.migrations.post_upgrade_backfill.run_all_backfills"
        ) as mock_run_backfills, patch(
            "fides.api.migrations.post_upgrade_backfill.release_backfill_lock"
        ) as mock_release:
            # Setup
            mock_run_backfills.return_value = [
                BackfillResult(name="test", total_updated=10)
            ]

            # Execute
            post_upgrade_backfill_task()

            # Verify
            mock_acquire.assert_called_once()

            if lock_acquired:
                # Should run backfills when lock is acquired
                mock_get_db.assert_called_once()
                mock_run_backfills.assert_called_once()
                mock_release.assert_called_once_with(mock_lock)
            else:
                # Should skip when lock unavailable
                mock_get_db.assert_not_called()
                mock_run_backfills.assert_not_called()
                mock_release.assert_not_called()

    @pytest.mark.parametrize(
        "should_fail",
        [False, True],
        ids=["success", "exception"],
    )
    def test_lock_always_released(self, should_fail):
        """Verify lock is released in finally block regardless of outcome."""
        mock_lock = MagicMock()

        with patch(
            "fides.api.migrations.post_upgrade_backfill.acquire_backfill_lock",
            return_value=mock_lock,
        ), patch(
            "fides.api.migrations.post_upgrade_backfill.get_db_session"
        ) as mock_get_db, patch(
            "fides.api.migrations.post_upgrade_backfill.run_all_backfills"
        ) as mock_run_backfills, patch(
            "fides.api.migrations.post_upgrade_backfill.release_backfill_lock"
        ) as mock_release:
            # Setup
            if should_fail:
                mock_run_backfills.side_effect = Exception("Test error")
            else:
                mock_run_backfills.return_value = [
                    BackfillResult(name="test", total_updated=10)
                ]

            mock_db = MagicMock()
            mock_get_db.return_value.return_value.__enter__.return_value = mock_db

            # Execute
            if should_fail:
                with pytest.raises(Exception, match="Test error"):
                    post_upgrade_backfill_task()
            else:
                post_upgrade_backfill_task()

            # Verify lock is always released
            mock_release.assert_called_once_with(mock_lock)


class TestRunBackfillManually:
    """Tests for run_backfill_manually() function."""

    def test_passes_parameters_and_returns_results(self):
        """Verify parameters are passed through and results are returned."""
        mock_lock = MagicMock()
        batch_size = 2500
        batch_delay = 0.5
        expected_results = [
            BackfillResult(name="test1", total_updated=10),
            BackfillResult(name="test2", total_updated=20),
        ]

        with patch(
            "fides.api.migrations.post_upgrade_backfill.get_db_session"
        ) as mock_get_db, patch(
            "fides.api.migrations.post_upgrade_backfill.run_all_backfills",
            return_value=expected_results,
        ) as mock_run_backfills, patch(
            "fides.api.migrations.post_upgrade_backfill.release_backfill_lock"
        ):
            # Setup
            mock_db = MagicMock()
            mock_get_db.return_value.return_value.__enter__.return_value = mock_db

            # Execute
            results = run_backfill_manually(mock_lock, batch_size, batch_delay)

            # Verify parameters were passed through
            mock_run_backfills.assert_called_once_with(
                mock_db, batch_size, batch_delay, lock=mock_lock
            )

            # Verify results are returned
            assert results == expected_results

    @pytest.mark.parametrize(
        "should_fail",
        [False, True],
        ids=["success", "exception"],
    )
    def test_lock_always_released(self, should_fail):
        """Verify lock is released in finally block regardless of outcome."""
        mock_lock = MagicMock()

        with patch(
            "fides.api.migrations.post_upgrade_backfill.get_db_session"
        ) as mock_get_db, patch(
            "fides.api.migrations.post_upgrade_backfill.run_all_backfills"
        ) as mock_run_backfills, patch(
            "fides.api.migrations.post_upgrade_backfill.release_backfill_lock"
        ) as mock_release:
            # Setup
            if should_fail:
                mock_run_backfills.side_effect = Exception("Test error")
            else:
                mock_run_backfills.return_value = [
                    BackfillResult(name="test", total_updated=10)
                ]

            mock_db = MagicMock()
            mock_get_db.return_value.return_value.__enter__.return_value = mock_db

            # Execute
            if should_fail:
                with pytest.raises(Exception, match="Test error"):
                    run_backfill_manually(mock_lock)
            else:
                run_backfill_manually(mock_lock)

            # Verify lock is always released
            mock_release.assert_called_once_with(mock_lock)
