"""Tests for requires_input/pending_external guards in requeue_interrupted_tasks.

The watchdog incorrectly cancels/requeues DSRs that are intentionally
paused for manual webhook data or manual task input. These tests verify
that the early guard in the watchdog loop skips paused DSRs.

External boundaries (Redis lock, Celery queue, task cache) are mocked because
they require infrastructure. DB state uses real fixtures.
"""

from unittest import mock

import pytest

from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.request_service import (
    requeue_interrupted_tasks,
)

_REQUEST_SERVICE_MODULE = "fides.api.service.privacy_request.request_service"

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
    """The early guard should skip requires_input/pending_external DSRs
    before any cancellation or requeue logic runs."""

    @pytest.mark.parametrize("status", _PAUSED_STATUSES)
    @mock.patch(f"{_REQUEST_SERVICE_MODULE}.redis_lock")
    @mock.patch(
        f"{_REQUEST_SERVICE_MODULE}._get_task_ids_from_dsr_queue", return_value=[]
    )
    def test_paused_dsr_skipped_by_watchdog(
        self, _, mock_redis_lock, db, privacy_request, status
    ):
        """Paused DSRs should remain in their current status after the watchdog runs."""
        privacy_request.status = status
        privacy_request.save(db)
        mock_redis_lock.return_value.__enter__.return_value = True

        _run_watchdog(db)

        db.refresh(privacy_request)
        assert privacy_request.status == status


class TestWatchdogStillCancelsActiveRequests:
    """Existing behavior: in_processing DSRs should still be canceled/requeued."""

    @mock.patch(f"{_REQUEST_SERVICE_MODULE}.redis_lock")
    @mock.patch(
        f"{_REQUEST_SERVICE_MODULE}._get_task_ids_from_dsr_queue", return_value=[]
    )
    @mock.patch(f"{_REQUEST_SERVICE_MODULE}.get_cached_task_id", return_value=None)
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
