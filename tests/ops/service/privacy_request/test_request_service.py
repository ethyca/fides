import time
import uuid
from datetime import datetime, timedelta
from unittest import mock

import pytest
from httpx import HTTPStatusError

from fides.api.cryptography.cryptographic_util import str_to_b64_str
from fides.api.db.seed import create_or_update_parent_user
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.request_service import (
    _handle_privacy_request_requeue,
    build_required_privacy_request_kwargs,
    get_cached_task_id,
    poll_for_exited_privacy_request_tasks,
    poll_server_for_completion,
    remove_saved_dsr_data,
    requeue_interrupted_tasks,
)
from fides.api.util.cache import cache_task_tracking_key
from fides.common.api.v1.urn_registry import LOGIN, V1_URL_PREFIX
from fides.config import CONFIG


@pytest.fixture
def parent_user_config():
    original_user = CONFIG.security.parent_server_username
    original_password = CONFIG.security.parent_server_password
    CONFIG.security.parent_server_username = "parent_user"
    CONFIG.security.parent_server_password = "Apassword1!"
    yield
    CONFIG.security.parent_server_username = original_user
    CONFIG.security.parent_server_password = original_password


@pytest.mark.parametrize("status", ["complete", "denied", "canceled", "error"])
@pytest.mark.usefixtures("parent_user_config")
async def test_poll_server_for_completion(status, async_api_client, db, policy):
    create_or_update_parent_user()

    pr = PrivacyRequest.create(
        db=db,
        data={
            "requested_at": None,
            "policy_id": policy.id,
            "status": status,
        },
    )

    login_url = f"{V1_URL_PREFIX}{LOGIN}"
    body = {
        "username": CONFIG.security.parent_server_username,
        "password": str_to_b64_str(CONFIG.security.parent_server_password),
    }

    login_response = await async_api_client.post(login_url, json=body)

    response = await poll_server_for_completion(
        privacy_request_id=pr.id,
        server_url="http://0.0.0.0:8080",
        token=login_response.json()["token_data"]["access_token"],
        client=async_api_client,
        poll_interval_seconds=1,
    )

    assert response.status == status


@pytest.mark.usefixtures("parent_user_config")
async def test_poll_server_for_completion_timeout(async_api_client, db, policy):
    create_or_update_parent_user()

    pr = PrivacyRequest.create(
        db=db,
        data={
            "requested_at": None,
            "policy_id": policy.id,
            "status": "pending",
        },
    )

    login_url = f"{V1_URL_PREFIX}{LOGIN}"
    body = {
        "username": CONFIG.security.parent_server_username,
        "password": str_to_b64_str(CONFIG.security.parent_server_password),
    }

    login_response = await async_api_client.post(login_url, json=body)

    with pytest.raises(TimeoutError):
        await poll_server_for_completion(
            privacy_request_id=pr.id,
            server_url="http://0.0.0.0:8080",
            token=login_response.json()["token_data"]["access_token"],
            client=async_api_client,
            poll_interval_seconds=1,
            timeout_seconds=2,
        )


@pytest.mark.usefixtures("parent_user_config")
async def test_poll_server_for_completion_non_200(async_api_client, db, policy):
    create_or_update_parent_user()

    pr = PrivacyRequest.create(
        db=db,
        data={
            "requested_at": None,
            "policy_id": policy.id,
            "status": "complete",
        },
    )

    with pytest.raises(HTTPStatusError):
        await poll_server_for_completion(
            privacy_request_id=pr.id,
            server_url="http://0.0.0.0:8080",
            token="somebadtoken",
            client=async_api_client,
            poll_interval_seconds=1,
        )


class TestPollForExitedPrivacyRequests:
    def test_no_request_tasks(self, db, privacy_request):
        errored_prs = poll_for_exited_privacy_request_tasks.delay().get()
        assert errored_prs == set()

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.in_processing

    @pytest.mark.usefixtures("request_task")
    def test_request_tasks_still_in_progress(self, db, privacy_request):
        errored_prs = poll_for_exited_privacy_request_tasks.delay().get()
        assert errored_prs == set()

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.in_processing

    def test_request_tasks_all_exited_and_some_errored(
        self, db, privacy_request, request_task
    ):
        # Put all tasks in an exited state - completed, errored, or skipped
        root_task = privacy_request.get_root_task_by_action(ActionType.access)
        assert root_task.status == ExecutionLogStatus.complete
        request_task.update_status(db, ExecutionLogStatus.skipped)
        terminator_task = privacy_request.get_terminate_task_by_action(
            ActionType.access
        )
        terminator_task.update_status(db, ExecutionLogStatus.error)

        errored_prs = poll_for_exited_privacy_request_tasks.delay().get()
        assert errored_prs == {privacy_request.id}

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.error

    def test_approved_privacy_request_task_with_errored_tasks(
        self, db, privacy_request, request_task
    ):
        """Approved privacy requests remain in approved status while they are processing,
        so if there's an error, they will be in this state.

        The "poll_for_exited_privacy_request_tasks" task looks for Privacy Requests in both
        "approved" and "in_processing" states.
        """

        privacy_request.status = PrivacyRequestStatus.approved
        privacy_request.save(db)

        # Put all tasks in an exited state - completed, errored, or skipped
        root_task = privacy_request.get_root_task_by_action(ActionType.access)
        assert root_task.status == ExecutionLogStatus.complete
        request_task.update_status(db, ExecutionLogStatus.error)
        terminator_task = privacy_request.get_terminate_task_by_action(
            ActionType.access
        )
        terminator_task.update_status(db, ExecutionLogStatus.error)

        errored_prs = poll_for_exited_privacy_request_tasks.delay().get()
        assert errored_prs == {privacy_request.id}

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.error

    def test_requires_input_privacy_request_task_with_errored_tasks(
        self, db, privacy_request_requires_input
    ):
        """Privacy requests in requires_input status should be monitored for task errors
        and marked as errored if tasks fail.

        The "poll_for_exited_privacy_request_tasks" task looks for Privacy Requests in
        "approved", "in_processing", and "requires_input" states.
        """

        # Create the necessary tasks for this privacy request (similar to request_task fixture)
        root_task = RequestTask.create(
            db,
            data={
                "action_type": ActionType.access,
                "status": "complete",
                "privacy_request_id": privacy_request_requires_input.id,
                "collection_address": "__ROOT__:__ROOT__",
                "dataset_name": "__ROOT__",
                "collection_name": "__ROOT__",
                "upstream_tasks": [],
                "downstream_tasks": ["test_dataset:test_collection"],
                "all_descendant_tasks": [
                    "test_dataset:test_collection",
                    "__TERMINATE__:__TERMINATE__",
                ],
            },
        )

        request_task = RequestTask.create(
            db,
            data={
                "action_type": ActionType.access,
                "status": "pending",
                "privacy_request_id": privacy_request_requires_input.id,
                "collection_address": "test_dataset:test_collection",
                "dataset_name": "test_dataset",
                "collection_name": "test_collection",
                "upstream_tasks": ["__ROOT__:__ROOT__"],
                "downstream_tasks": ["__TERMINATE__:__TERMINATE__"],
                "all_descendant_tasks": ["__TERMINATE__:__TERMINATE__"],
            },
        )

        terminator_task = RequestTask.create(
            db,
            data={
                "action_type": ActionType.access,
                "status": "pending",
                "privacy_request_id": privacy_request_requires_input.id,
                "collection_address": "__TERMINATE__:__TERMINATE__",
                "dataset_name": "__TERMINATE__",
                "collection_name": "__TERMINATE__",
                "upstream_tasks": ["test_dataset:test_collection"],
                "downstream_tasks": [],
                "all_descendant_tasks": [],
            },
        )

        # Put all tasks in an exited state - completed, errored, or skipped
        assert root_task.status == ExecutionLogStatus.complete
        request_task.update_status(db, ExecutionLogStatus.error)
        terminator_task.update_status(db, ExecutionLogStatus.error)

        errored_prs = poll_for_exited_privacy_request_tasks.delay().get()
        assert errored_prs == {privacy_request_requires_input.id}

        db.refresh(privacy_request_requires_input)
        assert privacy_request_requires_input.status == PrivacyRequestStatus.error

        # Clean up created tasks
        try:
            root_task.delete(db)
            request_task.delete(db)
            terminator_task.delete(db)
        except Exception:
            pass

    def test_request_tasks_all_exited_none_errored(
        self, db, privacy_request, request_task
    ):
        # Put all tasks in an exited state - but none are errored.
        # This task does not flip the status of the overall privacy request in that case
        root_task = privacy_request.get_root_task_by_action(ActionType.access)
        assert root_task.status == ExecutionLogStatus.complete
        request_task.update_status(db, ExecutionLogStatus.skipped)
        terminator_task = privacy_request.get_terminate_task_by_action(
            ActionType.access
        )
        terminator_task.update_status(db, ExecutionLogStatus.complete)

        errored_prs = poll_for_exited_privacy_request_tasks.delay().get()
        assert errored_prs == set()

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.in_processing

    def test_access_tasks_errored_erasure_tasks_pending(
        self, db, privacy_request, request_task, erasure_request_task
    ):
        """Request tasks of different action types are considered separately.
        If access tasks have errored but erasure tasks are pending, the access step itself
        causes the privacy request as whole to get marked as error.
        """
        # Erasure tasks still pending - these were created at the same time as the
        # access tasks but can't run until the access section is finished
        assert erasure_request_task.status == ExecutionLogStatus.pending

        # Access tasks have errored
        root_task = privacy_request.get_root_task_by_action(ActionType.access)
        assert root_task.status == ExecutionLogStatus.complete
        request_task.update_status(db, ExecutionLogStatus.error)
        terminator_task = privacy_request.get_terminate_task_by_action(
            ActionType.access
        )
        terminator_task.update_status(db, ExecutionLogStatus.error)

        errored_prs = poll_for_exited_privacy_request_tasks.delay().get()
        assert errored_prs == {privacy_request.id}

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.error

    @pytest.mark.usefixtures("request_task")
    def test_access_tasks_complete_erasure_tasks_errored(
        self, db, privacy_request, erasure_request_task
    ):
        """Tasks of different action types are considered separately.  If all access tasks
        have completed, but erasure tasks have an error, the entire privacy request will be marked as error
        """
        for rq in privacy_request.request_tasks:
            rq.update_status(db, ExecutionLogStatus.complete)

        erasure_request_task.update_status(db, ExecutionLogStatus.error)

        errored_prs = poll_for_exited_privacy_request_tasks.delay().get()
        assert errored_prs == {privacy_request.id}

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.error


@pytest.fixture(scope="function")
def very_short_request_task_expiration():
    original_value: float = CONFIG.execution.request_task_ttl
    CONFIG.execution.request_task_ttl = (
        0.01  # Set redis cache to expire very quickly for testing purposes
    )
    yield CONFIG
    CONFIG.execution.request_task_ttl = original_value


@pytest.fixture(scope="function")
def very_short_redis_cache_expiration():
    original_value: float = CONFIG.redis.default_ttl_seconds
    CONFIG.redis.default_ttl_seconds = (
        0.01  # Set redis cache to expire very quickly for testing purposes
    )
    yield CONFIG
    CONFIG.redis.default_ttl_seconds = original_value


class TestRemoveSavedCustomerData:
    @pytest.mark.usefixtures(
        "very_short_redis_cache_expiration", "very_short_request_task_expiration"
    )
    def test_no_request_tasks(self, db, privacy_request):
        assert not privacy_request.request_tasks.count()
        time.sleep(1)

        # Mainly asserting this runs without error
        remove_saved_dsr_data.delay().get()

        db.refresh(privacy_request)
        assert not privacy_request.request_tasks.count()

    @pytest.mark.usefixtures(
        "very_short_redis_cache_expiration",
        "very_short_request_task_expiration",
        "request_task",
    )
    def test_privacy_request_incomplete(self, db, privacy_request):
        """Incomplete Privacy Requests are not cleaned up"""
        assert privacy_request.status == PrivacyRequestStatus.in_processing
        privacy_request.save(db)

        privacy_request.filtered_final_upload = (
            {"rule_key": {"test_dataset:test_collection": [{"id": 1, "name": "Jane"}]}},
        )

        privacy_request.access_result_urls = {"access_result_urls": ["www.example.com"]}
        privacy_request.save(db)

        assert privacy_request.request_tasks.count()
        time.sleep(1)

        remove_saved_dsr_data.delay().get()

        db.refresh(privacy_request)
        assert privacy_request.filtered_final_upload is not None
        assert privacy_request.access_result_urls is not None
        assert privacy_request.request_tasks.count()

    @pytest.mark.usefixtures(
        "very_short_redis_cache_expiration",
        "very_short_request_task_expiration",
        "request_task",
    )
    def test_customer_data_removed_from_old_request_tasks_and_privacy_requests(
        self, db, privacy_request, loguru_caplog
    ):
        privacy_request.status = PrivacyRequestStatus.complete
        privacy_request.save(db)

        privacy_request.filtered_final_upload = (
            {"rule_key": {"test_dataset:test_collection": [{"id": 1, "name": "Jane"}]}},
        )

        privacy_request.access_result_urls = {"access_result_urls": ["www.example.com"]}
        privacy_request.save(db)

        assert privacy_request.request_tasks.count()
        time.sleep(1)

        remove_saved_dsr_data.delay().get()

        db.refresh(privacy_request)
        assert privacy_request.filtered_final_upload is None
        assert privacy_request.access_result_urls is None
        assert not privacy_request.request_tasks.count()

        assert (
            "Deleted 3 expired request tasks via DSR Data Removal Task."
            in loguru_caplog.text
        )


class TestBuildPrivacyRequestRequiredKwargs:
    def test_build_required_privacy_request_kwargs_authenticated(self):
        resp = build_required_privacy_request_kwargs(
            requested_at=datetime.now(),
            policy_id="test_id",
            verification_required=True,
            authenticated=True,
        )
        assert resp["requested_at"] is not None
        assert resp["policy_id"] == "test_id"
        assert resp["status"] == PrivacyRequestStatus.pending

    def test_build_required_privacy_request_kwargs_not_authenticated(self):
        resp = build_required_privacy_request_kwargs(
            requested_at=datetime.now(),
            policy_id="test_id",
            verification_required=True,
            authenticated=False,
        )
        assert resp["requested_at"] is not None
        assert resp["policy_id"] == "test_id"
        assert resp["status"] == PrivacyRequestStatus.identity_unverified

    def test_build_required_privacy_request_kwargs_identity_verification_not_required(
        self,
    ):
        resp = build_required_privacy_request_kwargs(
            requested_at=datetime.now(),
            policy_id="test_id",
            verification_required=False,
            authenticated=False,
        )
        assert resp["requested_at"] is not None
        assert resp["policy_id"] == "test_id"
        assert resp["status"] == PrivacyRequestStatus.pending


class TestCancelInterruptedTasksAndErrorPrivacyRequest:
    """Test the _cancel_interrupted_tasks_and_error_privacy_request function."""

    @pytest.fixture
    def privacy_request_with_tasks(self, db, policy):
        """Create a privacy request with associated request tasks."""
        from fides.api.models.privacy_request import PrivacyRequest, RequestTask
        from fides.api.models.worker_task import ExecutionLogStatus
        from fides.api.schemas.policy import ActionType
        from fides.api.util.cache import cache_task_tracking_key

        # Create the privacy request
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "external_id": f"ext-{str(uuid.uuid4())}",
                "started_processing_at": datetime.utcnow(),
                "requested_at": datetime.utcnow() - timedelta(days=1),
                "status": PrivacyRequestStatus.in_processing,
                "origin": "https://example.com/testing",
                "policy_id": policy.id,
                "client_id": policy.client_id,
            },
        )

        # Create request tasks
        request_task = RequestTask.create(
            db,
            data={
                "action_type": ActionType.access,
                "status": ExecutionLogStatus.in_processing,
                "privacy_request_id": privacy_request.id,
                "collection_address": "test_dataset:customer",
                "dataset_name": "test_dataset",
                "collection_name": "customer",
                "upstream_tasks": [],
                "downstream_tasks": [],
            },
        )

        # Cache task IDs
        cache_task_tracking_key(privacy_request.id, "main_task_123")
        cache_task_tracking_key(request_task.id, "sub_task_456")

        yield privacy_request

        # Clean up
        request_task.delete(db)
        privacy_request.delete(db)

    @mock.patch("fides.api.service.privacy_request.request_service.logger")
    def test_cancel_interrupted_tasks_and_error_privacy_request_success(
        self, mock_logger, db, privacy_request_with_tasks
    ):
        """Test successful cancellation and error state setting."""
        from fides.api.service.privacy_request.request_service import (
            _cancel_interrupted_tasks_and_error_privacy_request,
        )

        privacy_request = privacy_request_with_tasks

        # Mock the cancel_celery_tasks method
        with mock.patch.object(privacy_request, "cancel_celery_tasks") as mock_cancel:
            with mock.patch.object(privacy_request, "error_processing") as mock_error:
                _cancel_interrupted_tasks_and_error_privacy_request(db, privacy_request)

                # Verify cancel_celery_tasks was called
                mock_cancel.assert_called_once()

                # Verify error_processing was called with db
                mock_error.assert_called_once_with(db)

                # Verify logging - now uses error level instead of warning
                mock_logger.error.assert_called_once()
                mock_logger.info.assert_called_once()

    @mock.patch("fides.api.service.privacy_request.request_service.logger")
    def test_cancel_interrupted_tasks_and_error_privacy_request_error_processing_fails(
        self, mock_logger, db, privacy_request_with_tasks
    ):
        """Test handling when error_processing fails."""
        from fides.api.service.privacy_request.request_service import (
            _cancel_interrupted_tasks_and_error_privacy_request,
        )

        privacy_request = privacy_request_with_tasks

        # Mock the cancel_celery_tasks method and error_processing to raise exception
        with mock.patch.object(privacy_request, "cancel_celery_tasks"):
            with mock.patch.object(
                privacy_request, "error_processing", side_effect=Exception("DB Error")
            ):
                _cancel_interrupted_tasks_and_error_privacy_request(db, privacy_request)

                # Verify error logging - now called twice:
                # 1. For the default error message
                # 2. For the error_processing failure
                assert mock_logger.error.call_count == 2

                # First call: default cancellation message
                first_call = mock_logger.error.call_args_list[0][0][0]
                assert (
                    "Canceling interrupted tasks and marking privacy request"
                    in first_call
                )

                # Second call: error_processing failure
                second_call = mock_logger.error.call_args_list[1][0][0]
                assert "Failed to mark privacy request" in second_call
                assert "DB Error" in second_call


class TestGetCachedTaskId:
    """Test the standalone get_cached_task_id function."""

    def test_get_cached_task_id_success(self, privacy_request):
        """Test successful retrieval of cached task ID."""
        # Cache a task ID
        cache_task_tracking_key(privacy_request.id, "test_task_id_123")

        # Function should return the cached ID
        result = get_cached_task_id(privacy_request.id)
        assert result == "test_task_id_123"

    def test_get_cached_task_id_none_when_not_cached(self, privacy_request):
        """Test that function returns None when no task ID is cached."""
        result = get_cached_task_id(privacy_request.id)
        assert result is None

    @mock.patch("fides.api.service.privacy_request.request_service.get_cache")
    @mock.patch("fides.api.service.privacy_request.request_service.logger")
    def test_get_cached_task_id_cache_exception(
        self, mock_logger, mock_get_cache, privacy_request
    ):
        """Test that function logs error and re-raises exceptions from cache operations."""
        # Mock cache to raise exception
        mock_cache = mock.Mock()
        mock_cache.get.side_effect = Exception("Redis connection failed")
        mock_get_cache.return_value = mock_cache

        # Function should log error and re-raise exception
        with pytest.raises(Exception, match="Redis connection failed"):
            get_cached_task_id(privacy_request.id)

        # Verify error was logged
        mock_logger.error.assert_called_once()
        log_message = mock_logger.error.call_args[0][0]
        assert "Failed to get cached task ID" in log_message
        assert privacy_request.id in log_message


class TestHandlePrivacyRequestRequeue:
    """Test the _handle_privacy_request_requeue function."""

    @mock.patch(
        "fides.api.service.privacy_request.request_service.get_privacy_request_retry_count"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service.increment_privacy_request_retry_count"
    )
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service._requeue_privacy_request"
    )
    @mock.patch("fides.api.service.privacy_request.request_service.logger")
    def test_requeue_within_retry_limit_success(
        self,
        mock_logger,
        mock_requeue,
        mock_increment,
        mock_get_count,
        db,
        privacy_request,
    ):
        """Test successful requeue when under retry limit."""
        # Mock retry count under limit
        mock_get_count.return_value = 2
        mock_increment.return_value = 3

        _handle_privacy_request_requeue(db, privacy_request)

        # Should increment retry count and requeue
        mock_increment.assert_called_once_with(privacy_request.id)
        mock_requeue.assert_called_once_with(db, privacy_request)

        # Should log requeue attempt
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "Requeuing privacy request" in log_message
        assert "attempt 3/3" in log_message

    @mock.patch(
        "fides.api.service.privacy_request.request_service.get_privacy_request_retry_count"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service.increment_privacy_request_retry_count"
    )
    @mock.patch(
        "fides.service.privacy_request.privacy_request_service._requeue_privacy_request"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service._cancel_interrupted_tasks_and_error_privacy_request"
    )
    def test_requeue_failure_causes_cancellation(
        self,
        mock_cancel,
        mock_requeue,
        mock_increment,
        mock_get_count,
        db,
        privacy_request,
    ):
        """Test that requeue failure causes task cancellation."""
        from fides.service.privacy_request.privacy_request_service import (
            PrivacyRequestError,
        )

        # Mock retry count under limit but requeue fails
        mock_get_count.return_value = 2
        mock_increment.return_value = 3
        mock_requeue.side_effect = PrivacyRequestError("Requeue failed")

        _handle_privacy_request_requeue(db, privacy_request)

        # Should attempt requeue but then cancel due to failure
        mock_requeue.assert_called_once_with(db, privacy_request)
        mock_cancel.assert_called_once_with(db, privacy_request, "Requeue failed")

    @mock.patch(
        "fides.api.service.privacy_request.request_service.get_privacy_request_retry_count"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service.reset_privacy_request_retry_count"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service._cancel_interrupted_tasks_and_error_privacy_request"
    )
    def test_retry_limit_exceeded_causes_cancellation(
        self, mock_cancel, mock_reset, mock_get_count, db, privacy_request
    ):
        """Test that exceeding retry limit causes cancellation."""
        # Mock retry count at limit
        mock_get_count.return_value = 3  # At limit (default is 3)

        _handle_privacy_request_requeue(db, privacy_request)

        # Should cancel and reset retry count
        mock_cancel.assert_called_once()
        cancel_call_args = mock_cancel.call_args[0]
        assert cancel_call_args[0] == db
        assert cancel_call_args[1] == privacy_request
        assert "exceeded max retry attempts" in cancel_call_args[2]

        mock_reset.assert_called_once_with(privacy_request.id)

    @mock.patch(
        "fides.api.service.privacy_request.request_service.get_privacy_request_retry_count"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service._cancel_interrupted_tasks_and_error_privacy_request"
    )
    def test_cache_exception_causes_cancellation(
        self, mock_cancel, mock_get_count, db, privacy_request
    ):
        """Test that cache exceptions cause cancellation."""
        # Mock cache operation to fail
        mock_get_count.side_effect = Exception("Cache error")

        _handle_privacy_request_requeue(db, privacy_request)

        # Should cancel due to cache failure
        mock_cancel.assert_called_once()
        cancel_call_args = mock_cancel.call_args[0]
        assert cancel_call_args[0] == db
        assert cancel_call_args[1] == privacy_request
        assert "Cache operation failed" in cancel_call_args[2]
        assert "Cache error" in cancel_call_args[2]


class TestRequeueInterruptedTasksAdditionalCoverage:
    """Test additional coverage paths for requeue_interrupted_tasks function."""

    @mock.patch("fides.api.service.privacy_request.request_service.redis_lock")
    def test_lock_not_acquired_returns_early(self, mock_redis_lock):
        """Test that function returns early when lock cannot be acquired."""
        # Mock lock context manager to return False (lock not acquired)
        mock_redis_lock.return_value.__enter__.return_value = False

        # Function should return early without doing anything
        result = requeue_interrupted_tasks.apply().get()
        assert result is None

    @mock.patch("fides.api.service.privacy_request.request_service.redis_lock")
    @mock.patch("fides.api.service.privacy_request.request_service.logger")
    def test_no_in_progress_requests_logs_and_returns(
        self, mock_logger, mock_redis_lock, db
    ):
        """Test that function logs and returns when no in-progress requests exist."""
        # Mock successful lock acquisition
        mock_redis_lock.return_value.__enter__.return_value = True

        # Mock database task to use our db session
        with mock.patch.object(
            requeue_interrupted_tasks, "get_new_session"
        ) as mock_session:
            mock_session.return_value.__enter__.return_value = db

            requeue_interrupted_tasks.apply().get()

        # Should log that no requests were found
        debug_calls = [call.args[0] for call in mock_logger.debug.call_args_list]
        assert any(
            "No in-progress privacy requests to check" in call for call in debug_calls
        )

    @mock.patch("fides.api.service.privacy_request.request_service.redis_lock")
    @mock.patch(
        "fides.api.service.privacy_request.request_service._get_task_ids_from_dsr_queue"
    )
    @mock.patch("fides.api.service.privacy_request.request_service.logger")
    def test_queue_exception_logs_and_returns(
        self, mock_logger, mock_get_queue_tasks, mock_redis_lock, db, privacy_request
    ):
        """Test that queue exceptions are handled gracefully."""
        # Set up privacy request as in-progress
        privacy_request.status = PrivacyRequestStatus.in_processing
        privacy_request.save(db)

        # Mock successful lock acquisition
        mock_redis_lock.return_value.__enter__.return_value = True

        # Mock queue operation to fail
        mock_get_queue_tasks.side_effect = Exception("Queue error")

        with mock.patch.object(
            requeue_interrupted_tasks, "get_new_session"
        ) as mock_session:
            mock_session.return_value.__enter__.return_value = db

            requeue_interrupted_tasks.apply().get()

        # Should log warning about queue failure
        mock_logger.warning.assert_called_once()
        warning_message = mock_logger.warning.call_args[0][0]
        assert "Failed to get task IDs from queue" in warning_message
        assert "Queue error" in warning_message

    @mock.patch("fides.api.service.privacy_request.request_service.redis_lock")
    @mock.patch(
        "fides.api.service.privacy_request.request_service._get_task_ids_from_dsr_queue"
    )
    @mock.patch("fides.api.service.privacy_request.request_service.get_cached_task_id")
    @mock.patch(
        "fides.api.service.privacy_request.request_service._cancel_interrupted_tasks_and_error_privacy_request"
    )
    def test_cache_exception_when_getting_main_task_id(
        self,
        mock_cancel,
        mock_get_cached_task_id,
        mock_get_queue_tasks,
        mock_redis_lock,
        db,
        privacy_request,
    ):
        """Test cache exception when getting main privacy request task ID."""
        # Set up privacy request as in-progress
        privacy_request.status = PrivacyRequestStatus.in_processing
        privacy_request.save(db)

        # Mock successful setup
        mock_redis_lock.return_value.__enter__.return_value = True
        mock_get_queue_tasks.return_value = []

        # Mock cache exception when getting task ID
        mock_get_cached_task_id.side_effect = Exception("Cache failure")

        with mock.patch.object(
            requeue_interrupted_tasks, "get_new_session"
        ) as mock_session:
            mock_session.return_value.__enter__.return_value = db

            requeue_interrupted_tasks.apply().get()

        # Should cancel the privacy request due to cache failure
        mock_cancel.assert_called_once()
        cancel_call_args = mock_cancel.call_args[0]
        assert cancel_call_args[0] == db
        assert cancel_call_args[1] == privacy_request
        assert "Cache failure when getting task ID" in cancel_call_args[2]

    @mock.patch("fides.api.service.privacy_request.request_service.redis_lock")
    @mock.patch(
        "fides.api.service.privacy_request.request_service._get_task_ids_from_dsr_queue"
    )
    @mock.patch("fides.api.service.privacy_request.request_service.get_cached_task_id")
    @mock.patch(
        "fides.api.service.privacy_request.request_service.celery_tasks_in_flight"
    )
    @mock.patch("fides.api.service.privacy_request.request_service.logger")
    def test_no_request_tasks_triggers_requeue(
        self,
        mock_logger,
        mock_tasks_in_flight,
        mock_get_cached_task_id,
        mock_get_queue_tasks,
        mock_redis_lock,
        db,
        privacy_request,
    ):
        """Test that privacy request with no request tasks and inactive main task gets requeued."""
        # Set up privacy request as in-progress
        privacy_request.status = PrivacyRequestStatus.in_processing
        privacy_request.save(db)

        # Mock successful setup
        mock_redis_lock.return_value.__enter__.return_value = True
        mock_get_queue_tasks.return_value = []  # Task not in queue
        mock_get_cached_task_id.return_value = "main_task_id"
        mock_tasks_in_flight.return_value = False  # Task not running

        with mock.patch.object(
            requeue_interrupted_tasks, "get_new_session"
        ) as mock_session:
            mock_session.return_value.__enter__.return_value = db
            with mock.patch(
                "fides.api.service.privacy_request.request_service._handle_privacy_request_requeue"
            ) as mock_handle_requeue:

                requeue_interrupted_tasks.apply().get()

                # Should log warning and requeue
                warning_calls = [
                    call.args[0] for call in mock_logger.warning.call_args_list
                ]
                assert any(
                    "was terminated before it could schedule any request tasks" in call
                    for call in warning_calls
                )
                mock_handle_requeue.assert_called_once_with(db, privacy_request)

    @mock.patch("fides.api.service.privacy_request.request_service.redis_lock")
    @mock.patch(
        "fides.api.service.privacy_request.request_service._get_task_ids_from_dsr_queue"
    )
    @mock.patch("fides.api.service.privacy_request.request_service.get_cached_task_id")
    @mock.patch(
        "fides.api.service.privacy_request.request_service.celery_tasks_in_flight"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service._get_request_task_ids_in_progress"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service._cancel_interrupted_tasks_and_error_privacy_request"
    )
    def test_request_task_cache_exception_causes_cancellation(
        self,
        mock_cancel,
        mock_get_request_task_ids,
        mock_tasks_in_flight,
        mock_get_cached_task_id,
        mock_get_queue_tasks,
        mock_redis_lock,
        db,
        privacy_request,
    ):
        """Test cache exception when getting request task ID causes cancellation."""
        # Set up privacy request as in-progress
        privacy_request.status = PrivacyRequestStatus.in_processing
        privacy_request.save(db)

        # Mock successful setup
        mock_redis_lock.return_value.__enter__.return_value = True
        mock_get_queue_tasks.return_value = []
        mock_tasks_in_flight.return_value = False
        mock_get_request_task_ids.return_value = ["request_task_id_1"]

        # Mock main task ID success, then cache exception for request task
        mock_get_cached_task_id.side_effect = [
            "main_task_id",
            Exception("Cache failure"),
        ]

        with mock.patch.object(
            requeue_interrupted_tasks, "get_new_session"
        ) as mock_session:
            mock_session.return_value.__enter__.return_value = db

            requeue_interrupted_tasks.apply().get()

        # Should cancel due to cache failure when getting subtask ID
        mock_cancel.assert_called_once()
        cancel_call_args = mock_cancel.call_args[0]
        assert "Cache failure when getting subtask ID" in cancel_call_args[2]

    @mock.patch("fides.api.service.privacy_request.request_service.redis_lock")
    @mock.patch(
        "fides.api.service.privacy_request.request_service._get_task_ids_from_dsr_queue"
    )
    @mock.patch("fides.api.service.privacy_request.request_service.get_cached_task_id")
    @mock.patch(
        "fides.api.service.privacy_request.request_service.celery_tasks_in_flight"
    )
    @mock.patch(
        "fides.api.service.privacy_request.request_service._get_request_task_ids_in_progress"
    )
    @mock.patch("fides.api.service.privacy_request.request_service.logger")
    def test_interrupted_request_task_triggers_requeue(
        self,
        mock_logger,
        mock_get_request_task_ids,
        mock_tasks_in_flight,
        mock_get_cached_task_id,
        mock_get_queue_tasks,
        mock_redis_lock,
        db,
        privacy_request,
    ):
        """Test that interrupted request task triggers requeue."""
        # Set up privacy request as in-progress
        privacy_request.status = PrivacyRequestStatus.in_processing
        privacy_request.save(db)

        # Mock successful setup
        mock_redis_lock.return_value.__enter__.return_value = True
        mock_get_queue_tasks.return_value = []  # Tasks not in queue
        mock_tasks_in_flight.return_value = False  # Tasks not running
        mock_get_request_task_ids.return_value = ["request_task_id_1"]
        mock_get_cached_task_id.side_effect = ["main_task_id", "subtask_id"]

        with mock.patch.object(
            requeue_interrupted_tasks, "get_new_session"
        ) as mock_session:
            mock_session.return_value.__enter__.return_value = db
            with mock.patch(
                "fides.api.service.privacy_request.request_service._handle_privacy_request_requeue"
            ) as mock_handle_requeue:

                requeue_interrupted_tasks.apply().get()

                # Should log warning and requeue
                warning_calls = [
                    call.args[0] for call in mock_logger.warning.call_args_list
                ]
                assert any(
                    "is not in the queue or running" in call for call in warning_calls
                )
                mock_handle_requeue.assert_called_once_with(db, privacy_request)
