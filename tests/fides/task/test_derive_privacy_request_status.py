"""Tests for derive_privacy_request_status helper (ENG-3835).

The helper derives the correct PR status from the aggregate state of all
active RequestTasks.  User-actionable statuses always surface:
    requires_input > pending_external > in_processing
Terminal statuses (error, complete, canceled) are never overwritten.
"""

import uuid
from datetime import datetime, timedelta

import pytest

from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.privacy_request.request_task import AsyncTaskType
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.request_service import (
    derive_privacy_request_status,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def make_privacy_request(db, policy):
    """Factory: create privacy requests with automatic teardown."""
    created = []

    def _make(status=PrivacyRequestStatus.in_processing):
        pr = PrivacyRequest.create(
            db=db,
            data={
                "external_id": f"ext-{uuid.uuid4()}",
                "started_processing_at": datetime.utcnow(),
                "requested_at": datetime.utcnow() - timedelta(days=1),
                "status": status,
                "origin": "https://example.com/testing",
                "policy_id": policy.id,
                "client_id": policy.client_id,
            },
        )
        created.append(pr)
        return pr

    yield _make
    for pr in created:
        pr.delete(db)


@pytest.fixture
def make_request_task(db):
    """Factory: create request tasks with automatic teardown."""
    created = []

    def _make(
        privacy_request,
        status,
        collection="customer",
        async_type=None,
    ):
        data = {
            "action_type": ActionType.access,
            "status": status,
            "privacy_request_id": privacy_request.id,
            "collection_address": f"test_dataset:{collection}",
            "dataset_name": "test_dataset",
            "collection_name": collection,
            "upstream_tasks": [],
            "downstream_tasks": [],
        }
        if async_type is not None:
            data["async_type"] = async_type
        task = RequestTask.create(db, data=data)
        created.append(task)
        return task

    yield _make
    for task in reversed(created):
        task.delete(db)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDerivePrivacyRequestStatus:
    """Test the derive_privacy_request_status helper."""

    def test_manual_task_awaiting_returns_requires_input(
        self, db, make_privacy_request, make_request_task
    ):
        """A manual task in awaiting_processing → PR should be requires_input."""
        pr = make_privacy_request(status=PrivacyRequestStatus.in_processing)
        # Manual task awaiting user input (collection_address contains "manual_data")
        make_request_task(
            pr,
            ExecutionLogStatus.awaiting_processing,
            collection="manual_data",
        )
        result = derive_privacy_request_status(db, pr)
        assert result == PrivacyRequestStatus.requires_input

    def test_jira_task_awaiting_returns_pending_external(
        self, db, make_privacy_request, make_request_task
    ):
        """A Jira-type task in awaiting_processing with no manual tasks → pending_external."""
        pr = make_privacy_request(status=PrivacyRequestStatus.in_processing)
        # Non-manual async task awaiting external completion
        make_request_task(
            pr,
            ExecutionLogStatus.awaiting_processing,
            collection="jira_connector",
            async_type=AsyncTaskType.callback,
        )
        result = derive_privacy_request_status(db, pr)
        assert result == PrivacyRequestStatus.pending_external

    def test_manual_task_wins_over_jira_task(
        self, db, make_privacy_request, make_request_task
    ):
        """Both manual and Jira tasks awaiting → requires_input wins (user-actionable)."""
        pr = make_privacy_request(status=PrivacyRequestStatus.in_processing)
        make_request_task(
            pr,
            ExecutionLogStatus.awaiting_processing,
            collection="manual_data",
        )
        make_request_task(
            pr,
            ExecutionLogStatus.awaiting_processing,
            collection="jira_connector",
            async_type=AsyncTaskType.callback,
        )
        result = derive_privacy_request_status(db, pr)
        assert result == PrivacyRequestStatus.requires_input

    def test_no_awaiting_tasks_returns_in_processing(
        self, db, make_privacy_request, make_request_task
    ):
        """All tasks running or complete, no one waiting → in_processing."""
        pr = make_privacy_request(status=PrivacyRequestStatus.in_processing)
        make_request_task(pr, ExecutionLogStatus.in_processing, collection="api_task")
        make_request_task(pr, ExecutionLogStatus.complete, collection="other_task")
        result = derive_privacy_request_status(db, pr)
        assert result == PrivacyRequestStatus.in_processing

    @pytest.mark.parametrize(
        "terminal_status",
        [
            pytest.param(PrivacyRequestStatus.error, id="error"),
            pytest.param(PrivacyRequestStatus.complete, id="complete"),
            pytest.param(PrivacyRequestStatus.canceled, id="canceled"),
            pytest.param(PrivacyRequestStatus.denied, id="denied"),
        ],
    )
    def test_terminal_status_never_overwritten(
        self, db, make_privacy_request, make_request_task, terminal_status
    ):
        """Terminal statuses are never changed, even if tasks are awaiting."""
        pr = make_privacy_request(status=terminal_status)
        make_request_task(
            pr,
            ExecutionLogStatus.awaiting_processing,
            collection="manual_data",
        )
        result = derive_privacy_request_status(db, pr)
        assert result == terminal_status

    def test_polling_task_awaiting_returns_pending_external(
        self, db, make_privacy_request, make_request_task
    ):
        """A polling async task in awaiting_processing → pending_external."""
        pr = make_privacy_request(status=PrivacyRequestStatus.in_processing)
        make_request_task(
            pr,
            ExecutionLogStatus.awaiting_processing,
            collection="polling_api",
            async_type=AsyncTaskType.polling,
        )
        result = derive_privacy_request_status(db, pr)
        assert result == PrivacyRequestStatus.pending_external

    def test_completed_manual_task_does_not_trigger_requires_input(
        self, db, make_privacy_request, make_request_task
    ):
        """A completed manual task should not cause requires_input."""
        pr = make_privacy_request(status=PrivacyRequestStatus.in_processing)
        make_request_task(pr, ExecutionLogStatus.complete, collection="manual_data")
        make_request_task(pr, ExecutionLogStatus.in_processing, collection="other_task")
        result = derive_privacy_request_status(db, pr)
        assert result == PrivacyRequestStatus.in_processing

    def test_no_request_tasks_returns_current_status(self, db, make_privacy_request):
        """No request tasks at all → keep current status."""
        pr = make_privacy_request(status=PrivacyRequestStatus.in_processing)
        result = derive_privacy_request_status(db, pr)
        assert result == PrivacyRequestStatus.in_processing
