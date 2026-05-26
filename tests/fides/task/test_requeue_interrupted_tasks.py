import uuid
from datetime import datetime, timedelta
from unittest import mock

import pytest

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.privacy_request.request_task import AsyncTaskType
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.request_service import (
    REQUEUE_INTERRUPTED_TASKS_LOCK,
    requeue_interrupted_tasks,
)
from fides.api.util.cache import (
    cache_task_tracking_key,
    get_cache,
    get_privacy_request_retry_count,
    increment_privacy_request_retry_count,
    reset_privacy_request_retry_count,
)
from fides.config import CONFIG

# Mock target paths — centralised to avoid string duplication
_CANCEL = "fides.api.service.privacy_request.request_service._cancel_interrupted_tasks_and_error_privacy_request"
_REQUEUE = (
    "fides.service.privacy_request.privacy_request_service._requeue_privacy_request"
)
_QUEUE = (
    "fides.api.service.privacy_request.request_service._get_task_ids_from_dsr_queue"
)
_IN_FLIGHT = "fides.api.service.privacy_request.request_service.celery_tasks_in_flight"


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def make_privacy_request(db, policy):
    """Factory: create privacy requests with automatic teardown.

    Usage::
        pr = make_privacy_request()                          # in_processing, cached
        pr = make_privacy_request(status=requires_input)    # different status
        pr = make_privacy_request(cached=False)             # no PR-level cache key
    """
    created = []

    def _make(status=PrivacyRequestStatus.in_processing, cached=True):
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
        if cached:
            cache_task_tracking_key(pr.id, f"pr_task_{pr.id}")
        created.append(pr)
        return pr

    yield _make
    for pr in created:
        pr.delete(db)


@pytest.fixture
def make_request_task(db):
    """Factory: create request tasks with automatic teardown.

    Usage::
        task = make_request_task(pr, ExecutionLogStatus.pending)
        task = make_request_task(pr, ExecutionLogStatus.in_processing,
                                 collection="orders", cached_subtask_id="celery-id-123")
        task = make_request_task(pr, ExecutionLogStatus.pending,
                                 upstream=[other_task.collection_address],
                                 async_type=AsyncTaskType.callback)
    """
    created = []

    def _make(
        privacy_request,
        status,
        collection="customer",
        upstream=None,
        async_type=None,
        cached_subtask_id=None,
        connection_key=None,
    ):
        data = {
            "action_type": ActionType.access,
            "status": status,
            "privacy_request_id": privacy_request.id,
            "collection_address": f"test_dataset:{collection}",
            "dataset_name": "test_dataset",
            "collection_name": collection,
            "upstream_tasks": upstream or [],
            "downstream_tasks": [],
        }
        if async_type is not None:
            data["async_type"] = async_type
        if connection_key is not None:
            data["traversal_details"] = {
                "dataset_connection_key": connection_key,
                "incoming_edges": [],
                "outgoing_edges": [],
                "input_keys": [],
            }
        task = RequestTask.create(db, data=data)
        if cached_subtask_id:
            cache_task_tracking_key(task.id, cached_subtask_id)
        created.append(task)
        return task

    yield _make
    for task in reversed(created):
        task.delete(db)


# Legacy fixtures used by tests that reference specific cache key names in mocks.
@pytest.fixture
def in_progress_privacy_request(db, policy):
    pr = PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{uuid.uuid4()}",
            "started_processing_at": datetime.utcnow(),
            "requested_at": datetime.utcnow() - timedelta(days=1),
            "status": PrivacyRequestStatus.in_processing,
            "origin": "https://example.com/testing",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )
    cache_task_tracking_key(pr.id, "privacy_request_task_id")
    yield pr
    pr.delete(db)


@pytest.fixture
def in_progress_request_task(db, in_progress_privacy_request):
    task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.in_processing,
            "privacy_request_id": in_progress_privacy_request.id,
            "collection_address": "test_dataset:customer",
            "dataset_name": "test_dataset",
            "collection_name": "customer",
            "upstream_tasks": [],
            "downstream_tasks": [],
        },
    )
    cache_task_tracking_key(task.id, "request_task_id")
    yield task
    task.delete(db)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRequeueInterruptedTasks:
    @pytest.mark.usefixtures("in_progress_privacy_request", "in_progress_request_task")
    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=True)
    def test_active_request_task_is_not_requeued(
        self, mock_in_flight, mock_queue, mock_requeue
    ):
        """Active (in-flight) subtask — privacy request must not be requeued."""
        requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_not_called()

    @pytest.mark.usefixtures("in_progress_privacy_request")
    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_interrupted_privacy_request_with_no_request_tasks_is_requeued(
        self, mock_in_flight, mock_queue, mock_requeue
    ):
        """Privacy request with a cached PR-level task ID but no subtasks is requeued."""
        requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_called_once()

    @pytest.mark.usefixtures("in_progress_privacy_request", "in_progress_request_task")
    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=["request_task_id"])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_interrupted_privacy_request_with_active_request_tasks_is_not_requeued(
        self, mock_in_flight, mock_queue, mock_requeue
    ):
        """Subtask still in the queue — privacy request must not be requeued."""
        requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_not_called()

    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_interrupted_privacy_request_with_inactive_request_tasks_is_requeued(
        self,
        mock_in_flight,
        mock_queue,
        mock_requeue,
        make_privacy_request,
        make_request_task,
    ):
        """Subtask found neither in queue nor in-flight — privacy request is requeued."""
        pr = make_privacy_request()
        make_request_task(
            pr, ExecutionLogStatus.pending, cached_subtask_id="subtask_id"
        )
        requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_called_once()

    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_privacy_request_with_no_cached_task_id_is_skipped(
        self,
        mock_in_flight,
        mock_queue,
        mock_requeue,
        mock_cancel,
        make_privacy_request,
    ):
        """No PR-level cached task ID — watchdog cancels the privacy request."""
        make_privacy_request(cached=False)
        requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_not_called()
        mock_cancel.assert_called_once()

    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_requires_input_privacy_request_with_stuck_subtask_is_not_canceled(
        self,
        mock_in_flight,
        mock_requeue,
        mock_cancel,
        make_privacy_request,
        make_request_task,
    ):
        """requires_input status — watchdog leaves it alone (intentionally waiting for input)."""
        pr = make_privacy_request(status=PrivacyRequestStatus.requires_input)
        make_request_task(pr, ExecutionLogStatus.in_processing)  # no subtask_id
        requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_not_called()
        mock_cancel.assert_not_called()

    @pytest.mark.parametrize(
        "async_type",
        [
            pytest.param(AsyncTaskType.callback, id="callback"),
            pytest.param(AsyncTaskType.polling, id="polling"),
        ],
    )
    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_task_with_async_type_and_stuck_subtask_is_not_canceled(
        self,
        mock_in_flight,
        mock_queue,
        mock_requeue,
        mock_cancel,
        make_privacy_request,
        make_request_task,
        async_type,
    ):
        """Async task (callback/polling) present — watchdog skips the whole request."""
        pr = make_privacy_request()
        make_request_task(pr, ExecutionLogStatus.pending, async_type=async_type)
        requeue_interrupted_tasks.apply().get()
        mock_queue.assert_called_once()
        mock_requeue.assert_not_called()
        mock_cancel.assert_not_called()

    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_in_processing_task_with_no_cache_key_and_async_task_is_not_canceled(
        self,
        mock_in_flight,
        mock_requeue,
        mock_cancel,
        make_privacy_request,
        make_request_task,
    ):
        """in_processing+no_cache alongside an async callback task — async guard wins, skips."""
        pr = make_privacy_request()
        make_request_task(pr, ExecutionLogStatus.in_processing)  # no subtask_id
        make_request_task(
            pr,
            ExecutionLogStatus.pending,
            collection="gateway_api",
            async_type=AsyncTaskType.callback,
        )
        requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_not_called()
        mock_cancel.assert_not_called()

    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_async_check_db_error_skips_request(
        self,
        mock_in_flight,
        mock_requeue,
        mock_cancel,
        make_privacy_request,
        make_request_task,
    ):
        """DB error in async-task check — watchdog fails safe and skips the request."""
        pr = make_privacy_request()
        make_request_task(pr, ExecutionLogStatus.in_processing)  # no subtask_id
        with mock.patch(
            "fides.api.service.privacy_request.request_service._has_async_tasks_awaiting_external_completion",
            side_effect=Exception("db error"),
        ):
            requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_not_called()
        mock_cancel.assert_not_called()

    @pytest.mark.usefixtures("in_progress_privacy_request", "in_progress_request_task")
    @mock.patch(_REQUEUE)
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_task_in_queue_is_not_requeued(self, mock_in_flight, mock_requeue):
        """Subtask found in the queue — not requeued."""
        with mock.patch(_QUEUE, return_value=["privacy_request_task_id"]):
            requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_not_called()

    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_pending_task_awaiting_upstream_is_not_canceled(
        self,
        mock_in_flight,
        mock_requeue,
        mock_cancel,
        make_privacy_request,
        make_request_task,
    ):
        """Pending task still waiting on upstream deps — not stuck, watchdog skips it."""
        pr = make_privacy_request()
        upstream = make_request_task(
            pr,
            ExecutionLogStatus.in_processing,
            collection="upstream",
            cached_subtask_id="upstream_celery_id",
        )
        make_request_task(
            pr,
            ExecutionLogStatus.pending,
            collection="downstream",
            upstream=[upstream.collection_address],
        )
        with mock.patch(_QUEUE, return_value=["upstream_celery_id"]):
            requeue_interrupted_tasks.apply().get()
        mock_cancel.assert_not_called()
        mock_requeue.assert_not_called()

    @pytest.mark.parametrize(
        "has_upstream",
        [
            pytest.param(True, id="complete_upstream"),
            pytest.param(False, id="root_task_no_upstream"),
        ],
    )
    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_pending_task_with_no_cache_key_is_requeued(
        self,
        mock_in_flight,
        mock_queue,
        mock_requeue,
        mock_cancel,
        make_privacy_request,
        make_request_task,
        has_upstream,
    ):
        """Pending task with no subtask_id is requeued — parent died before dispatch."""
        pr = make_privacy_request()
        upstream = (
            make_request_task(pr, ExecutionLogStatus.complete, collection="upstream")
            if has_upstream
            else None
        )
        make_request_task(
            pr,
            ExecutionLogStatus.pending,
            collection="undispatched",
            upstream=[upstream.collection_address] if upstream else [],
        )
        requeue_interrupted_tasks.apply().get()
        mock_cancel.assert_not_called()
        mock_requeue.assert_called_once()

    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_in_processing_task_with_no_cache_key_is_requeued(
        self,
        mock_in_flight,
        mock_queue,
        mock_requeue,
        mock_cancel,
        make_privacy_request,
        make_request_task,
    ):
        """in_processing+no_cache routes through retry mechanism — requeues at retry_count=0."""
        pr = make_privacy_request()
        make_request_task(pr, ExecutionLogStatus.in_processing)  # no subtask_id
        requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_called_once()
        mock_cancel.assert_not_called()

    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_in_processing_task_with_no_cache_key_over_retry_limit_is_canceled(
        self,
        mock_in_flight,
        mock_queue,
        mock_requeue,
        mock_cancel,
        make_privacy_request,
        make_request_task,
    ):
        """in_processing+no_cache cancels once retry_count exceeds the configured limit."""
        pr = make_privacy_request()
        for _ in range(4):  # default limit is 3
            increment_privacy_request_retry_count(pr.id)
        make_request_task(pr, ExecutionLogStatus.in_processing)  # no subtask_id
        requeue_interrupted_tasks.apply().get()
        mock_cancel.assert_called_once()
        mock_requeue.assert_not_called()

    def test_acquired_locks_prevent_duplicate_runs(self, loguru_caplog):
        """Concurrent watchdog invocations are serialised via Redis lock."""
        redis_conn = get_cache()
        lock = redis_conn.lock(REQUEUE_INTERRUPTED_TASKS_LOCK, timeout=600)
        lock.acquire(blocking=False)
        requeue_interrupted_tasks.apply().get()
        assert (
            "Another process is already running for lock 'requeue_interrupted_tasks_lock'. Skipping this execution."
            in loguru_caplog.text
        )
        if lock.owned():
            lock.release()

    def test_lock_is_released_after_execution(self):
        """Lock is always released after a watchdog run completes."""
        redis_conn = get_cache()
        lock = redis_conn.lock(REQUEUE_INTERRUPTED_TASKS_LOCK, timeout=600)
        requeue_interrupted_tasks.apply().get()
        assert not lock.owned()

    # ------------------------------------------------------------------
    # Retry limit behaviour
    # ------------------------------------------------------------------

    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_privacy_request_near_retry_limit_is_requeued(
        self, mock_in_flight, mock_queue, mock_requeue, make_privacy_request
    ):
        """Request at retry_count=2 (below default limit of 3) is still requeued."""
        pr = make_privacy_request()
        for _ in range(2):
            increment_privacy_request_retry_count(pr.id)
        requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_called_once()

    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_privacy_request_over_retry_limit_is_canceled(
        self,
        mock_in_flight,
        mock_queue,
        mock_requeue,
        mock_cancel,
        make_privacy_request,
    ):
        """Request at retry_count=4 (above default limit of 3) is cancelled, not requeued."""
        pr = make_privacy_request()
        for _ in range(4):
            increment_privacy_request_retry_count(pr.id)
        requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_not_called()
        mock_cancel.assert_called_once()

    def test_retry_limit_configuration(self):
        """privacy_request_requeue_retry_count config is mutable and respected."""
        original = CONFIG.execution.privacy_request_requeue_retry_count
        assert original == 3
        try:
            CONFIG.execution.privacy_request_requeue_retry_count = 5
            assert CONFIG.execution.privacy_request_requeue_retry_count == 5
            CONFIG.execution.privacy_request_requeue_retry_count = 1
            assert CONFIG.execution.privacy_request_requeue_retry_count == 1
        finally:
            CONFIG.execution.privacy_request_requeue_retry_count = original

    def test_integration_privacy_request_retry_workflow(self, make_privacy_request):
        """Retry counter increments, reads back correctly, and resets to zero."""
        pr = make_privacy_request()
        assert get_privacy_request_retry_count(pr.id) == 0

        count = increment_privacy_request_retry_count(pr.id)
        assert count == 1
        assert get_privacy_request_retry_count(pr.id) == 1

        for i in range(2, 4):
            count = increment_privacy_request_retry_count(pr.id)
            assert count == i

        reset_privacy_request_retry_count(pr.id)
        assert get_privacy_request_retry_count(pr.id) == 0


# ---------------------------------------------------------------------------
# Orphaned task tests (ENG-3834)
#
# These tests document the behavior of the watchdog when async tasks have
# deleted or disabled connections.  Tests marked xfail demonstrate the
# current bug — they will pass once the fix is applied.
# ---------------------------------------------------------------------------


@pytest.fixture
def make_connection_config(db):
    """Factory: create ConnectionConfig instances with automatic teardown."""
    created = []

    def _make(key=None, disabled=False):
        key = key or f"test_conn_{uuid.uuid4().hex[:8]}"
        cc = ConnectionConfig.create(
            db=db,
            data={
                "key": key,
                "name": key,
                "connection_type": ConnectionType.postgres,
                "access": AccessLevel.read,
                "disabled": disabled,
            },
        )
        created.append(cc)
        return cc

    yield _make
    for cc in reversed(created):
        try:
            cc.delete(db)
        except Exception:
            pass


class TestOrphanedAsyncTasks:
    """ENG-3834: Watchdog behavior when async tasks have deleted/disabled connections."""

    # -- Fixed: orphaned callback tasks are now detected and requeued --

    @pytest.mark.parametrize(
        "conn_state",
        [
            pytest.param("deleted", id="deleted"),
            pytest.param("disabled", id="disabled"),
        ],
    )
    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_callback_task_unavailable_connection_should_requeue(
        self,
        mock_in_flight,
        mock_queue,
        mock_requeue,
        mock_cancel,
        make_privacy_request,
        make_request_task,
        make_connection_config,
        conn_state,
    ):
        """Callback task whose connection is deleted or disabled — the PR
        should be requeued so the task can be re-executed and skipped.
        Currently the watchdog cannot see awaiting_processing tasks at all."""
        conn_key = f"{conn_state}_conn"
        if conn_state == "disabled":
            make_connection_config(key=conn_key, disabled=True)
        # "deleted" case: no ConnectionConfig created → key doesn't exist

        pr = make_privacy_request()
        make_request_task(
            pr,
            ExecutionLogStatus.awaiting_processing,
            async_type=AsyncTaskType.callback,
            connection_key=conn_key,
            cached_subtask_id="old-celery-id",
        )
        requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_called_once()

    # -- Current behavior: should remain unchanged --

    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_callback_task_valid_connection_not_requeued(
        self,
        mock_in_flight,
        mock_queue,
        mock_requeue,
        mock_cancel,
        make_privacy_request,
        make_request_task,
        make_connection_config,
    ):
        """Callback task with a valid, enabled connection — legitimately
        waiting for external callback.  Watchdog must NOT requeue."""
        cc = make_connection_config(key="live_conn")
        pr = make_privacy_request()
        make_request_task(
            pr,
            ExecutionLogStatus.awaiting_processing,
            async_type=AsyncTaskType.callback,
            connection_key=cc.key,
            cached_subtask_id="old-celery-id",
        )
        requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_not_called()
        mock_cancel.assert_not_called()

    # -- Fixed: exited async tasks no longer blind the watchdog --

    @pytest.mark.parametrize(
        "exited_status",
        [
            pytest.param(ExecutionLogStatus.complete, id="complete"),
            pytest.param(ExecutionLogStatus.error, id="error"),
            pytest.param(ExecutionLogStatus.skipped, id="skipped"),
        ],
    )
    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_exited_async_task_does_not_blind_watchdog(
        self,
        mock_in_flight,
        mock_queue,
        mock_requeue,
        mock_cancel,
        make_privacy_request,
        make_request_task,
        exited_status,
    ):
        """An async task in any exited status (complete, error, skipped)
        should not prevent the watchdog from detecting stuck non-async tasks
        in the same PR.  Currently _has_async_tasks_awaiting_external_completion
        has no status filter, so any PR that ever had an async task is
        permanently invisible to the watchdog."""
        pr = make_privacy_request()
        # Exited async task — should not blind the watchdog
        make_request_task(
            pr,
            exited_status,
            collection="async_coll",
            async_type=AsyncTaskType.callback,
        )
        # Stuck non-async task — no subtask_id, should trigger requeue
        make_request_task(
            pr,
            ExecutionLogStatus.in_processing,
            collection="stuck_coll",
        )
        requeue_interrupted_tasks.apply().get()
        # The stuck non-async task should cause a requeue
        mock_requeue.assert_called_once()

    # -- pending_external PR with orphaned async task should requeue, not cancel --

    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_pending_external_pr_with_orphaned_task_requeued(
        self,
        mock_in_flight,
        mock_queue,
        mock_requeue,
        mock_cancel,
        make_privacy_request,
        make_request_task,
    ):
        """A PR in pending_external (e.g. waiting for Jira) that also has an
        orphaned async callback task should be requeued — not canceled.

        On requeue, the orphaned task will be re-executed and skipped
        (CollectionDisabled), while the Jira task re-pauses idempotently."""
        pr = make_privacy_request(status=PrivacyRequestStatus.pending_external)
        make_request_task(
            pr,
            ExecutionLogStatus.awaiting_processing,
            async_type=AsyncTaskType.callback,
            connection_key="deleted_conn",
            cached_subtask_id="old-celery-id",
        )
        requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_called_once()
        mock_cancel.assert_not_called()

    # -- Edge case: missing connection_key in traversal_details --

    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_missing_connection_key_not_treated_as_orphaned(
        self,
        mock_in_flight,
        mock_queue,
        mock_requeue,
        mock_cancel,
        make_privacy_request,
        make_request_task,
    ):
        """An awaiting_processing task whose traversal_details lacks
        dataset_connection_key should NOT be treated as orphaned.  The
        conservative default (return False) keeps the task in its current
        state rather than incorrectly requeueing."""
        pr = make_privacy_request()
        # No connection_key → traversal_details won't have dataset_connection_key
        make_request_task(
            pr,
            ExecutionLogStatus.awaiting_processing,
            async_type=AsyncTaskType.callback,
            cached_subtask_id="old-celery-id",
        )
        requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_not_called()
        mock_cancel.assert_not_called()


# ---------------------------------------------------------------------------
# Watchdog blind spot: missing erasure tasks (ENG-3950)
# ---------------------------------------------------------------------------


class TestWatchdogDetectsMissingErasureTasks:
    """The watchdog should detect when access tasks exist but erasure tasks
    are missing, and requeue the privacy request."""

    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_requeues_when_access_tasks_but_no_erasure_tasks(
        self,
        mock_in_flight,
        mock_queue,
        mock_requeue,
        mock_cancel,
        db,
        make_privacy_request,
        make_request_task,
        policy,
    ):
        """If access tasks exist but zero erasure tasks and the policy has
        erasure rules, the watchdog should requeue."""
        from fides.api.models.policy import Rule as PolicyRule

        PolicyRule.create(
            db=db,
            data={
                "action_type": "erasure",
                "name": "watchdog_erasure_rule",
                "policy_id": policy.id,
                "masking_strategy": {
                    "strategy": "null_rewrite",
                    "configuration": {},
                },
            },
        )

        pr = make_privacy_request()
        make_request_task(pr, ExecutionLogStatus.complete, collection="users")
        requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_called_once()

    @mock.patch(_CANCEL)
    @mock.patch(_REQUEUE)
    @mock.patch(_QUEUE, return_value=[])
    @mock.patch(_IN_FLIGHT, return_value=False)
    def test_does_not_requeue_when_policy_has_no_erasure_rules(
        self,
        mock_in_flight,
        mock_queue,
        mock_requeue,
        mock_cancel,
        make_privacy_request,
        make_request_task,
    ):
        """If the policy has no erasure rules, zero erasure tasks is expected.
        The watchdog should not requeue."""
        pr = make_privacy_request()
        make_request_task(pr, ExecutionLogStatus.complete, collection="users")
        requeue_interrupted_tasks.apply().get()
        mock_requeue.assert_not_called()

    # Note: a negative test for "erasure tasks exist, no requeue" is omitted
    # because the watchdog has multiple requeue paths that fire for
    # in_processing requests with complete tasks (task ID not in queue,
    # etc.), making it difficult to isolate just the erasure count check
    # without mocking the entire watchdog internals.
