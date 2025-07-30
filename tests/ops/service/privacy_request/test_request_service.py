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
    build_required_privacy_request_kwargs,
    poll_for_exited_privacy_request_tasks,
    poll_server_for_completion,
    remove_saved_dsr_data,
)
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
