"""Tests for derive_privacy_request_status helper (ENG-3835).

The helper derives the correct PR status from the aggregate state of all
active RequestTasks.  User-actionable statuses always surface:
    requires_input > pending_external > in_processing

Only statuses in the "derivable" set (in_processing, requires_input,
pending_external) are ever modified — all others pass through untouched.
"""

import uuid
from datetime import datetime, timedelta

import pytest

from fides.api.models.connectionconfig import AccessLevel, ConnectionConfig, ConnectionType
from fides.api.models.manual_task.manual_task import ManualTask, ManualTaskType
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
        dataset="test_dataset",
        async_type=None,
    ):
        data = {
            "action_type": ActionType.access,
            "status": status,
            "privacy_request_id": privacy_request.id,
            "collection_address": f"{dataset}:{collection}",
            "dataset_name": dataset,
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


@pytest.fixture
def make_manual_task_connection(db):
    """Factory: create ConnectionConfig + ManualTask pair with automatic teardown.

    Returns (connection_config, manual_task).  Use connection_config.key as
    the ``dataset`` parameter to make_request_task so that the RequestTask's
    collection_address matches the ManualTask's parent connection.
    """
    created_tasks: list[ManualTask] = []
    created_configs: list[ConnectionConfig] = []

    def _make(
        task_type: ManualTaskType = ManualTaskType.privacy_request,
        key: str | None = None,
    ) -> tuple[ConnectionConfig, ManualTask]:
        if key is None:
            key = f"manual_{uuid.uuid4().hex[:8]}"
        config = ConnectionConfig.create(
            db=db,
            data={
                "name": f"Manual Task Connection {key}",
                "key": key,
                "connection_type": ConnectionType.manual_task,
                "access": AccessLevel.write,
            },
        )
        created_configs.append(config)

        task = ManualTask.create(
            db=db,
            data={
                "task_type": task_type,
                "parent_entity_id": config.id,
                "parent_entity_type": "connection_config",
            },
        )
        created_tasks.append(task)
        return config, task

    yield _make
    for task in reversed(created_tasks):
        task.delete(db)
    for config in reversed(created_configs):
        config.delete(db)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDerivePrivacyRequestStatus:
    """Test the derive_privacy_request_status helper."""

    # -- User-input manual tasks → requires_input --------------------------

    def test_manual_task_awaiting_returns_requires_input(
        self,
        db,
        make_privacy_request,
        make_request_task,
        make_manual_task_connection,
    ):
        """A user-input manual task in awaiting_processing → requires_input."""
        pr = make_privacy_request(status=PrivacyRequestStatus.in_processing)
        config, _ = make_manual_task_connection(
            task_type=ManualTaskType.privacy_request,
        )
        make_request_task(
            pr,
            ExecutionLogStatus.awaiting_processing,
            collection="manual_data",
            dataset=config.key,
        )
        result = derive_privacy_request_status(db, pr)
        assert result == PrivacyRequestStatus.requires_input

    # -- Jira tasks → pending_external -------------------------------------

    def test_jira_task_awaiting_returns_pending_external(
        self,
        db,
        make_privacy_request,
        make_request_task,
        make_manual_task_connection,
    ):
        """A Jira manual task in awaiting_processing → pending_external.

        Both Jira and user-input tasks use collection="manual_data".
        The derive function must join to ManualTask.task_type to tell them apart.
        """
        pr = make_privacy_request(status=PrivacyRequestStatus.in_processing)
        config, _ = make_manual_task_connection(
            task_type=ManualTaskType.jira_ticket,
        )
        make_request_task(
            pr,
            ExecutionLogStatus.awaiting_processing,
            collection="manual_data",
            dataset=config.key,
        )
        result = derive_privacy_request_status(db, pr)
        assert result == PrivacyRequestStatus.pending_external

    # -- Mixed: user-input wins over Jira ----------------------------------

    def test_manual_task_wins_over_jira_task(
        self,
        db,
        make_privacy_request,
        make_request_task,
        make_manual_task_connection,
    ):
        """Both user-input and Jira tasks awaiting → requires_input wins."""
        pr = make_privacy_request(status=PrivacyRequestStatus.in_processing)
        user_config, _ = make_manual_task_connection(
            task_type=ManualTaskType.privacy_request,
        )
        jira_config, _ = make_manual_task_connection(
            task_type=ManualTaskType.jira_ticket,
        )
        make_request_task(
            pr,
            ExecutionLogStatus.awaiting_processing,
            collection="manual_data",
            dataset=user_config.key,
        )
        make_request_task(
            pr,
            ExecutionLogStatus.awaiting_processing,
            collection="manual_data",
            dataset=jira_config.key,
        )
        result = derive_privacy_request_status(db, pr)
        assert result == PrivacyRequestStatus.requires_input

    # -- Async connector tasks → pending_external --------------------------

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

    # -- No awaiting tasks → in_processing ---------------------------------

    def test_no_awaiting_tasks_returns_in_processing(
        self, db, make_privacy_request, make_request_task
    ):
        """All tasks running or complete, no one waiting → in_processing."""
        pr = make_privacy_request(status=PrivacyRequestStatus.in_processing)
        make_request_task(pr, ExecutionLogStatus.in_processing, collection="api_task")
        make_request_task(pr, ExecutionLogStatus.complete, collection="other_task")
        result = derive_privacy_request_status(db, pr)
        assert result == PrivacyRequestStatus.in_processing

    def test_completed_manual_task_does_not_trigger_requires_input(
        self, db, make_privacy_request, make_request_task
    ):
        """A completed manual task should not cause requires_input."""
        pr = make_privacy_request(status=PrivacyRequestStatus.in_processing)
        make_request_task(pr, ExecutionLogStatus.complete, collection="manual_data")
        make_request_task(pr, ExecutionLogStatus.in_processing, collection="other_task")
        result = derive_privacy_request_status(db, pr)
        assert result == PrivacyRequestStatus.in_processing

    def test_requires_input_transitions_to_in_processing_after_completion(
        self, db, make_privacy_request, make_request_task
    ):
        """After all manual tasks complete, PR should transition to in_processing."""
        pr = make_privacy_request(status=PrivacyRequestStatus.requires_input)
        make_request_task(pr, ExecutionLogStatus.complete, collection="manual_data")
        make_request_task(pr, ExecutionLogStatus.in_processing, collection="other_task")
        result = derive_privacy_request_status(db, pr)
        assert result == PrivacyRequestStatus.in_processing

    def test_no_request_tasks_returns_current_status(self, db, make_privacy_request):
        """No request tasks at all → keep current status."""
        pr = make_privacy_request(status=PrivacyRequestStatus.in_processing)
        result = derive_privacy_request_status(db, pr)
        assert result == PrivacyRequestStatus.in_processing

    # -- Multi-manual-task scenarios ---------------------------------------

    def test_one_manual_done_another_still_awaiting(
        self,
        db,
        make_privacy_request,
        make_request_task,
        make_manual_task_connection,
    ):
        """One manual task done, another still awaiting → requires_input."""
        pr = make_privacy_request(status=PrivacyRequestStatus.requires_input)
        make_request_task(pr, ExecutionLogStatus.complete, collection="manual_data")
        # Second manual task on a different connection, still awaiting
        config2, _ = make_manual_task_connection(
            task_type=ManualTaskType.privacy_request,
        )
        make_request_task(
            pr,
            ExecutionLogStatus.awaiting_processing,
            collection="manual_data",
            dataset=config2.key,
        )
        result = derive_privacy_request_status(db, pr)
        assert result == PrivacyRequestStatus.requires_input

    # -- Status guard: terminal statuses never overwritten -----------------

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

    # -- Status guard: non-derivable statuses never overwritten ------------

    @pytest.mark.parametrize(
        "protected_status",
        [
            pytest.param(PrivacyRequestStatus.paused, id="paused"),
            pytest.param(
                PrivacyRequestStatus.awaiting_email_send, id="awaiting_email_send"
            ),
            pytest.param(
                PrivacyRequestStatus.requires_manual_finalization,
                id="requires_manual_finalization",
            ),
            pytest.param(PrivacyRequestStatus.pending, id="pending"),
            pytest.param(
                PrivacyRequestStatus.identity_unverified, id="identity_unverified"
            ),
            pytest.param(
                PrivacyRequestStatus.awaiting_pre_approval, id="awaiting_pre_approval"
            ),
        ],
    )
    def test_non_derivable_status_not_overwritten(
        self, db, make_privacy_request, make_request_task, protected_status
    ):
        """Non-processing statuses (paused, awaiting_email_send, etc.) must
        not be overwritten by derive, even if tasks are awaiting."""
        pr = make_privacy_request(status=protected_status)
        make_request_task(
            pr,
            ExecutionLogStatus.awaiting_processing,
            collection="manual_data",
        )
        result = derive_privacy_request_status(db, pr)
        assert result == protected_status
