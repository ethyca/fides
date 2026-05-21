"""Tests for requires_input/pending_external guards in requeue_interrupted_tasks.

The watchdog incorrectly cancels/requeues DSRs that are intentionally
paused for manual webhook data or manual task input. These tests verify that all
four unguarded paths in the watchdog correctly skip paused DSRs.

External boundaries (Redis lock, Celery queue, task cache) are mocked because
they require infrastructure. DB state uses real fixtures.
"""

from unittest import mock

import pytest

from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.request_service import (
    requeue_interrupted_tasks,
)

_M = "fides.api.service.privacy_request.request_service"

_PAUSED_STATUSES = [
    pytest.param(PrivacyRequestStatus.requires_input, id="requires_input"),
    pytest.param(PrivacyRequestStatus.pending_external, id="pending_external"),
]


def _run_watchdog(db):
    """Run requeue_interrupted_tasks with the given db session."""
    with mock.patch.object(
        requeue_interrupted_tasks, "get_new_session"
    ) as mock_session:
        mock_session.return_value.__enter__.return_value = db
        requeue_interrupted_tasks.apply().get()


class TestWatchdogSkipsPausedRequests:
    """All four unguarded watchdog paths should skip requires_input/pending_external DSRs."""

    @pytest.mark.parametrize("status", _PAUSED_STATUSES)
    @mock.patch(f"{_M}.redis_lock")
    @mock.patch(f"{_M}._get_task_ids_from_dsr_queue", return_value=[])
    @mock.patch(f"{_M}.get_cached_task_id", return_value=None)
    def test_no_task_id_skips_cancel(
        self, _, __, mock_redis_lock, db, privacy_request, status
    ):
        """Path: line 623. No cached task ID is normal for paused DSRs."""
        privacy_request.status = status
        privacy_request.save(db)
        mock_redis_lock.return_value.__enter__.return_value = True

        _run_watchdog(db)

        db.refresh(privacy_request)
        assert privacy_request.status == status

    @pytest.mark.parametrize("status", _PAUSED_STATUSES)
    @mock.patch(f"{_M}.redis_lock")
    @mock.patch(f"{_M}._get_task_ids_from_dsr_queue", return_value=[])
    @mock.patch(f"{_M}.get_cached_task_id", side_effect=Exception("Redis timeout"))
    def test_cache_exception_skips_cancel(
        self, _, __, mock_redis_lock, db, privacy_request, status
    ):
        """Path: line 611. Transient Redis failure should not error paused DSRs."""
        privacy_request.status = status
        privacy_request.save(db)
        mock_redis_lock.return_value.__enter__.return_value = True

        _run_watchdog(db)

        db.refresh(privacy_request)
        assert privacy_request.status == status

    @pytest.mark.parametrize("status", _PAUSED_STATUSES)
    @mock.patch(f"{_M}.redis_lock")
    @mock.patch(f"{_M}._get_task_ids_from_dsr_queue", return_value=[])
    @mock.patch(f"{_M}.get_cached_task_id", return_value="main_task_id")
    @mock.patch(f"{_M}.celery_tasks_in_flight", return_value=False)
    def test_zero_request_tasks_skips_requeue(
        self, _, __, ___, mock_redis_lock, db, privacy_request, status
    ):
        """Path: line 641. Zero RequestTasks is normal for manual_webhook DSRs."""
        privacy_request.status = status
        privacy_request.save(db)
        mock_redis_lock.return_value.__enter__.return_value = True

        _run_watchdog(db)

        db.refresh(privacy_request)
        assert privacy_request.status == status

    @pytest.mark.parametrize("status", _PAUSED_STATUSES)
    @mock.patch(f"{_M}.redis_lock")
    @mock.patch(f"{_M}._get_task_ids_from_dsr_queue", return_value=[])
    @mock.patch(f"{_M}.celery_tasks_in_flight", return_value=False)
    @mock.patch(f"{_M}._get_request_task_ids_in_progress")
    def test_subtask_cache_exception_skips_cancel(
        self,
        mock_get_request_task_ids,
        _,
        __,
        mock_redis_lock,
        db,
        privacy_request,
        status,
    ):
        """Path: line 659. Subtask cache failure should not error paused DSRs."""
        privacy_request.status = status
        privacy_request.save(db)
        mock_redis_lock.return_value.__enter__.return_value = True
        mock_get_request_task_ids.return_value = [
            ("request_task_id_1", ExecutionLogStatus.in_processing, False)
        ]

        with mock.patch(
            f"{_M}.get_cached_task_id",
            side_effect=["main_task_id", Exception("Redis timeout")],
        ):
            _run_watchdog(db)

        db.refresh(privacy_request)
        assert privacy_request.status == status


class TestWatchdogStillCancelsActiveRequests:
    """Existing behavior: in_processing DSRs should still be canceled/requeued."""

    @mock.patch(f"{_M}.redis_lock")
    @mock.patch(f"{_M}._get_task_ids_from_dsr_queue", return_value=[])
    @mock.patch(f"{_M}.get_cached_task_id", return_value=None)
    def test_in_processing_no_task_id_still_canceled(
        self, _, __, mock_redis_lock, db, privacy_request
    ):
        """in_processing DSR with no cached task ID should still be canceled."""
        privacy_request.status = PrivacyRequestStatus.in_processing
        privacy_request.save(db)
        mock_redis_lock.return_value.__enter__.return_value = True

        _run_watchdog(db)

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.error
