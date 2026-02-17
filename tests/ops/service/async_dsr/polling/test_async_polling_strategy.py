from datetime import timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from freezegun import freeze_time
from requests import Response

from fides.api.common_exceptions import (
    AwaitingAsyncProcessing,
    FidesopsException,
    PrivacyRequestError,
)
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import RequestTask
from fides.api.models.privacy_request.request_task import RequestTaskSubRequest
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.saas.async_polling_configuration import (
    AsyncPollingConfiguration,
    PollingResultRequest,
    PollingStatusRequest,
)
from fides.api.schemas.saas.saas_config import ReadSaaSRequest
from fides.api.schemas.saas.shared_schemas import PollingStatusResult
from fides.api.service.async_dsr.strategies.async_dsr_strategy_factory import (
    get_strategy,
)
from fides.api.service.async_dsr.strategies.async_dsr_strategy_polling import (
    AsyncPollingStrategy,
)
from fides.api.service.connectors.saas.authenticated_client import (
    RequestFailureResponseException,
)
from fides.config import CONFIG
from tests.ops.graph.graph_test_util import erasure_policy


@pytest.mark.async_dsr
class TestAsyncPollingStrategy:
    @pytest.fixture(scope="function")
    def access_request_task(self, db):
        access_request_task = RequestTask.create(
            db,
            data={
                "id": "123",
                "collection_address": "test_dataset:test_collection",
                "dataset_name": "test_dataset",
                "collection_name": "test_collection",
                "status": "polling",
                "action_type": "access",
                "async_type": "polling",
            },
        )
        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": access_request_task.id,
                "param_values": {"correlation_id": "123"},
                "status": "pending",
            },
        )
        return access_request_task

    @pytest.fixture(scope="function")
    def erasure_request_task(self, db):
        erasure_request_task = RequestTask.create(
            db,
            data={
                "id": "123",
                "collection_address": "test_dataset:test_collection",
                "dataset_name": "test_dataset",
                "collection_name": "test_collection",
                "status": "polling",
                "action_type": "erasure",
                "async_type": "polling",
            },
        )
        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": erasure_request_task.id,
                "param_values": {"correlation_id": "123"},
                "status": "pending",
            },
        )
        return erasure_request_task

    @pytest.fixture(scope="function")
    def multi_sub_request_task(self, db):
        """Create a polling task with multiple sub-requests for testing completion logic"""
        multi_task = RequestTask.create(
            db,
            data={
                "id": "multi_123",
                "collection_address": "test_dataset:test_collection",
                "dataset_name": "test_dataset",
                "collection_name": "test_collection",
                "status": "polling",
                "action_type": "access",
                "async_type": "polling",
            },
        )

        # Create 3 sub-requests with different statuses
        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": multi_task.id,
                "param_values": {"correlation_id": "req_1"},
                "status": "pending",
            },
        )
        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": multi_task.id,
                "param_values": {"correlation_id": "req_2"},
                "status": "pending",
            },
        )
        RequestTaskSubRequest.create(
            db,
            data={
                "request_task_id": multi_task.id,
                "param_values": {"correlation_id": "req_3"},
                "status": "pending",
            },
        )
        return multi_task

    @pytest.fixture(scope="function")
    def async_polling_strategy(self, db, request_task):
        return get_strategy(
            AsyncPollingStrategy.type.value,
            db,
            configuration=AsyncPollingConfiguration(
                status_request=PollingStatusRequest(
                    method="GET",
                    path="/status/<correlation_id>",
                    status_path="status",
                    status_completed_value="completed",
                ),
                result_request=PollingResultRequest(
                    method="GET",
                    path="/result/<correlation_id>",
                ),
            ).model_dump(),
        )

    def test_async_retrieve_data_retry_limit_reached(
        self, access_request_task, async_polling_strategy
    ):
        request_task = access_request_task

        # Set the sub-request's created_at to be past the timeout period
        expired_time = request_task.created_at + timedelta(
            days=CONFIG.execution.async_polling_request_timeout_days + 1
        )

        with freeze_time(expired_time):
            with pytest.raises(PrivacyRequestError) as exc:
                async_polling_strategy.async_retrieve_data(
                    client=MagicMock(),
                    request_task_id=request_task.id,
                    query_config=MagicMock(),
                    input_data=MagicMock(),
                )
            assert "Polling timeout exceeded" in str(exc.value)

    def test_async_mask_data_retry_limit_reached(
        self, erasure_request_task, async_polling_strategy
    ):
        request_task = erasure_request_task

        # Set the sub-request's created_at to be past the timeout period
        expired_time = request_task.created_at + timedelta(
            days=CONFIG.execution.async_polling_request_timeout_days + 1
        )

        with freeze_time(expired_time):
            with pytest.raises(PrivacyRequestError) as exc:
                async_polling_strategy.async_mask_data(
                    client=MagicMock(),
                    request_task_id=request_task.id,
                    query_config=MagicMock(),
                    rows=MagicMock(),
                )
            assert "Polling timeout exceeded" in str(exc.value)

    def test_polling_continuation_waits_for_all_sub_requests_to_complete(
        self, multi_sub_request_task, async_polling_strategy, db
    ):
        """Test that polling continuation waits for all sub-requests before returning data"""
        request_task = multi_sub_request_task

        # Mock client and query_config
        mock_client = MagicMock()
        mock_query_config = MagicMock()

        # Initially all sub-requests are pending, so should raise AwaitingAsyncProcessing
        with pytest.raises(AwaitingAsyncProcessing) as exc:
            async_polling_strategy.async_retrieve_data(
                client=mock_client,
                request_task_id=request_task.id,
                query_config=mock_query_config,
                input_data=MagicMock(),
            )
        assert "Waiting for next scheduled check" in str(exc.value)

        # Mark 2 out of 3 sub-requests as complete - should still wait
        sub_requests = request_task.sub_requests
        sub_requests[0].update_status(db, ExecutionLogStatus.complete.value)
        sub_requests[1].update_status(db, ExecutionLogStatus.complete.value)
        db.commit()

        with pytest.raises(AwaitingAsyncProcessing) as exc:
            async_polling_strategy.async_retrieve_data(
                client=mock_client,
                request_task_id=request_task.id,
                query_config=mock_query_config,
                input_data=MagicMock(),
            )
        assert "Waiting for next scheduled check" in str(exc.value)

        # Mark the last sub-request as complete - should now return data
        sub_requests[2].update_status(db, ExecutionLogStatus.complete.value)
        db.commit()

        # Mock the access data on sub-requests (now aggregated from sub-requests)
        sub_requests[0].access_data = [{"id": 1, "name": "test1"}]
        sub_requests[1].access_data = [{"id": 2, "name": "test2"}]
        sub_requests[2].access_data = [{"id": 3, "name": "test3"}]
        db.commit()

        result = async_polling_strategy.async_retrieve_data(
            client=mock_client,
            request_task_id=request_task.id,
            query_config=mock_query_config,
            input_data=MagicMock(),
        )

        # Should aggregate all sub-request data
        assert result == [
            {"id": 1, "name": "test1"},
            {"id": 2, "name": "test2"},
            {"id": 3, "name": "test3"},
        ]

    def test_polling_completion_with_mixed_sub_request_statuses(
        self, multi_sub_request_task, async_polling_strategy, db
    ):
        """Test polling completion logic with various sub-request statuses"""
        request_task = multi_sub_request_task

        # Mock client and query_config
        mock_client = MagicMock()
        mock_query_config = MagicMock()

        # Test with mixed statuses: complete, error, pending
        sub_requests = request_task.sub_requests
        sub_requests[0].update_status(db, ExecutionLogStatus.complete.value)
        sub_requests[1].update_status(db, ExecutionLogStatus.error.value)
        # sub_requests[2] remains pending
        db.commit()

        # Should still wait because not all sub-requests are complete (only successful completions count)
        with pytest.raises(AwaitingAsyncProcessing) as exc:
            async_polling_strategy.async_retrieve_data(
                client=mock_client,
                request_task_id=request_task.id,
                query_config=mock_query_config,
                input_data=MagicMock(),
            )
        assert "Waiting for next scheduled check" in str(exc.value)

        # Mark the pending sub-request as complete and also fix the failed one
        sub_requests[1].update_status(
            db, ExecutionLogStatus.complete.value
        )  # Fix the failed one
        sub_requests[2].update_status(
            db, ExecutionLogStatus.complete.value
        )  # Complete the pending one
        db.commit()

        # Mock the access data on sub-requests
        sub_requests[0].access_data = [{"id": 1, "name": "test1"}]
        sub_requests[1].access_data = [{"id": 2, "name": "test2"}]
        sub_requests[2].access_data = [{"id": 3, "name": "test3"}]
        db.commit()

        result = async_polling_strategy.async_retrieve_data(
            client=mock_client,
            request_task_id=request_task.id,
            query_config=mock_query_config,
            input_data=MagicMock(),
        )

        # Should aggregate all sub-request data
        assert result == [
            {"id": 1, "name": "test1"},
            {"id": 2, "name": "test2"},
            {"id": 3, "name": "test3"},
        ]

    def test_polling_completion_with_no_sub_requests(
        self, access_request_task, async_polling_strategy, db
    ):
        """Test polling completion when there are no sub-requests"""
        request_task = access_request_task

        # Remove the existing sub-request by deleting each one individually
        for sub_request in request_task.sub_requests:
            db.delete(sub_request)
        db.commit()

        # Mock client and query_config
        mock_client = MagicMock()
        mock_query_config = MagicMock()

        # When there are no sub-requests, the async phase becomes 'sync' and returns empty list
        result = async_polling_strategy.async_retrieve_data(
            client=mock_client,
            request_task_id=request_task.id,
            query_config=mock_query_config,
            input_data=MagicMock(),
        )

        # Should return empty list since there are no sub-requests to process
        assert result == []

    @pytest.mark.parametrize(
        "action_type,policy_factory",
        [
            ("access", lambda db: Policy()),  # Basic access policy object
            (
                "erasure",
                lambda db: erasure_policy(db),
            ),  # Proper erasure policy with masking strategy
        ],
    )
    def test_handle_polling_initial_request_failure_not_in_ignore_list(
        self, db, async_polling_strategy, action_type, policy_factory
    ):
        """
        Test that _handle_polling_initial_request raises RequestFailureResponseException
        when initial request fails with a status code NOT in the ignore_errors list,
        with both access and erasure policy flows.
        """
        # Create a mock request task
        request_task = RequestTask.create(
            db,
            data={
                "id": f"test_task_{action_type}_not_ignored",
                "collection_address": "test_dataset:test_collection",
                "dataset_name": "test_dataset",
                "collection_name": "test_collection",
                "status": "polling",
                "action_type": action_type,
                "async_type": "polling",
            },
        )

        # Create mock objects
        mock_query_config = MagicMock()
        mock_query_config.generate_requests.return_value = [
            (MagicMock(), {"param": "value"})  # (request_params, param_value_map)
        ]

        # Create a read request with ignore_errors as list of common errors (404, 409)
        # but NOT including 500
        read_request = ReadSaaSRequest(
            method="GET",
            path="/api/start-request",
            correlation_id_path="request_id",
            ignore_errors=[404, 409],  # Common errors to ignore, but not 500
        )

        # Mock client that raises RequestFailureResponseException on send for 500 error
        mock_client = MagicMock()
        mock_response = Mock(spec=Response)
        mock_response.status_code = 500  # Server error NOT in ignore list
        mock_response.text = "Internal Server Error"
        mock_response.ok = False

        # Since 500 is NOT in ignore_errors list, client.send should raise RequestFailureResponseException
        mock_client.send.side_effect = RequestFailureResponseException(
            response=mock_response
        )

        input_data = {"email": "test@example.com"}
        policy = policy_factory(db)

        # The RequestFailureResponseException should bubble up since 500 is not ignored
        with pytest.raises(RequestFailureResponseException) as exc_info:
            async_polling_strategy._handle_polling_initial_request(
                request_task=request_task,
                query_config=mock_query_config,
                read_request=read_request,
                input_data=input_data,
                policy=policy,
                client=mock_client,
            )

        # Verify the response details are preserved in the exception
        assert exc_info.value.response.status_code == 500
        assert exc_info.value.response.text == "Internal Server Error"

    @pytest.mark.parametrize(
        "action_type,policy_factory",
        [
            ("access", lambda db: Policy()),
            ("erasure", lambda db: erasure_policy(db)),
        ],
    )
    def test_handle_polling_initial_request_failure_in_ignore_list(
        self, db, async_polling_strategy, action_type, policy_factory
    ):
        """
        Test that _handle_polling_initial_request skips sub-request creation
        when initial request fails with a status code IN the ignore_errors list.
        The client.send returns the failed response, but the ignore_errors guard
        causes the loop to continue without raising or creating a sub-request.
        """
        # Create a mock request task
        request_task = RequestTask.create(
            db,
            data={
                "id": f"test_task_{action_type}_ignored",
                "collection_address": "test_dataset:test_collection",
                "dataset_name": "test_dataset",
                "collection_name": "test_collection",
                "status": "polling",
                "action_type": action_type,
                "async_type": "polling",
            },
        )

        # Create mock objects
        mock_query_config = MagicMock()
        mock_query_config.generate_requests.return_value = [
            (MagicMock(), {"param": "value"})  # (request_params, param_value_map)
        ]

        # Create a read request with ignore_errors list that includes 404
        read_request = ReadSaaSRequest(
            method="GET",
            path="/api/start-request",
            correlation_id_path="request_id",
            ignore_errors=[404, 409],  # List includes 404 which we'll test with
        )

        # Mock client that returns a 404 response (which is in ignore list)
        mock_client = MagicMock()
        mock_response = Mock(spec=Response)
        mock_response.status_code = 404  # This is IN the ignore_errors list
        mock_response.text = "Not Found"
        mock_response.ok = False

        # Since 404 is in ignore_errors list, client.send returns the response without raising
        mock_client.send.return_value = mock_response

        input_data = {"email": "test@example.com"}
        policy = policy_factory(db)

        # Method should return without raising — the ignored error is skipped
        async_polling_strategy._handle_polling_initial_request(
            request_task=request_task,
            query_config=mock_query_config,
            read_request=read_request,
            input_data=input_data,
            policy=policy,
            client=mock_client,
        )

        # Verify the request was still sent
        mock_client.send.assert_called_once()

        # Verify no sub-requests were created (ignored response has no correlation ID)
        assert len(request_task.sub_requests) == 0

    def test_check_sub_request_status_wraps_bool_true_to_polling_status_result(
        self, db, async_polling_strategy
    ):
        """
        Test that _check_sub_request_status wraps a legacy bool True return
        into PollingStatusResult(is_complete=True, skip_result_request=False)
        """
        mock_client = MagicMock()

        # Mock the override function to return True (legacy bool)
        with MagicMock() as mock_override:
            mock_override.return_value = True

            with patch.object(
                async_polling_strategy,
                "status_request",
                MagicMock(request_override="test_override"),
            ):
                with patch(
                    "fides.api.service.async_dsr.strategies.async_dsr_strategy_polling.SaaSRequestOverrideFactory.get_override",
                    return_value=mock_override,
                ):
                    result = async_polling_strategy._check_sub_request_status(
                        mock_client, {"correlation_id": "123"}
                    )

                    assert isinstance(result, PollingStatusResult)
                    assert result.is_complete is True
                    assert result.skip_result_request is False

    def test_check_sub_request_status_wraps_bool_false_to_polling_status_result(
        self, db, async_polling_strategy
    ):
        """
        Test that _check_sub_request_status wraps a legacy bool False return
        into PollingStatusResult(is_complete=False, skip_result_request=False)
        """
        mock_client = MagicMock()

        # Mock the override function to return False (legacy bool)
        with MagicMock() as mock_override:
            mock_override.return_value = False

            from unittest.mock import patch

            with patch.object(
                async_polling_strategy,
                "status_request",
                MagicMock(request_override="test_override"),
            ):
                with patch(
                    "fides.api.service.async_dsr.strategies.async_dsr_strategy_polling.SaaSRequestOverrideFactory.get_override",
                    return_value=mock_override,
                ):
                    result = async_polling_strategy._check_sub_request_status(
                        mock_client, {"correlation_id": "123"}
                    )

                    assert isinstance(result, PollingStatusResult)
                    assert result.is_complete is False
                    assert result.skip_result_request is False

    def test_check_sub_request_status_passes_through_polling_status_result(
        self, db, async_polling_strategy
    ):
        """
        Test that _check_sub_request_status passes through a PollingStatusResult as-is
        """
        mock_client = MagicMock()

        # Mock the override function to return PollingStatusResult with skip=True
        expected_result = PollingStatusResult(
            is_complete=True, skip_result_request=True
        )
        with MagicMock() as mock_override:
            mock_override.return_value = expected_result

            from unittest.mock import patch

            with patch.object(
                async_polling_strategy,
                "status_request",
                MagicMock(request_override="test_override"),
            ):
                with patch(
                    "fides.api.service.async_dsr.strategies.async_dsr_strategy_polling.SaaSRequestOverrideFactory.get_override",
                    return_value=mock_override,
                ):
                    result = async_polling_strategy._check_sub_request_status(
                        mock_client, {"correlation_id": "123"}
                    )

                    assert result is expected_result
                    assert result.is_complete is True
                    assert result.skip_result_request is True

    def test_skip_result_request_marks_skipped_without_fetching(
        self, access_request_task, async_polling_strategy, db
    ):
        """
        Test that when skip_result_request=True, the sub-request is marked skipped
        without calling _process_completed_sub_request (no result fetching)
        """
        request_task = access_request_task
        sub_request = request_task.sub_requests[0]

        mock_client = MagicMock()

        # Mock _check_sub_request_status to return skip_result_request=True
        from unittest.mock import patch

        with patch.object(
            async_polling_strategy,
            "_check_sub_request_status",
            return_value=PollingStatusResult(
                is_complete=True, skip_result_request=True
            ),
        ):
            with patch.object(
                async_polling_strategy,
                "_process_completed_sub_request",
            ) as mock_process_completed:
                # Mock _get_requests_for_action to return a request with async_config
                mock_request = MagicMock()
                mock_request.async_config = True

                with patch.object(
                    async_polling_strategy,
                    "_get_requests_for_action",
                    return_value=[mock_request],
                ):
                    async_polling_strategy._process_sub_requests_for_request(
                        mock_client, mock_request, request_task
                    )

                    # Should NOT have called _process_completed_sub_request
                    mock_process_completed.assert_not_called()

                    # Refresh from DB and check status
                    db.refresh(sub_request)
                    assert sub_request.status == ExecutionLogStatus.skipped.value
                    assert sub_request.access_data == []

    def test_initial_request_access_all_ignored_returns_empty(
        self, db, async_polling_strategy
    ):
        """
        Integration test: when all initial access requests return an ignored error
        (e.g. 409), _initial_request_access should return [] instead of raising
        AwaitingAsyncProcessing. This prevents the task from looping back into the
        initial_async phase indefinitely.
        """
        # Create a fresh task with no async_type and no sub-requests
        request_task = RequestTask.create(
            db,
            data={
                "id": "test_access_all_ignored",
                "collection_address": "test_dataset:test_collection",
                "dataset_name": "test_dataset",
                "collection_name": "test_collection",
                "status": "pending",
                "action_type": "access",
            },
        )

        # Mock the privacy_request.policy relationship
        mock_privacy_request = MagicMock()
        mock_privacy_request.policy = Policy()
        request_task.privacy_request = mock_privacy_request

        # Create a read request with async_config and ignore_errors including 409
        read_request = ReadSaaSRequest(
            method="GET",
            path="/api/start-request",
            correlation_id_path="request_id",
            ignore_errors=[409],
            async_config={"strategy": "polling", "configuration": {
                "status_request": {
                    "method": "GET",
                    "path": "/status/<correlation_id>",
                    "status_path": "status",
                    "status_completed_value": "completed",
                },
            }},
        )

        # Mock query_config to return our read request with async_config
        mock_query_config = MagicMock()
        mock_query_config.get_read_requests_by_identity.return_value = [read_request]
        mock_query_config.generate_requests.return_value = [
            (MagicMock(), {"email": "test@example.com"})
        ]

        # Mock client returning 409 (ignored error)
        mock_client = MagicMock()
        mock_response = Mock(spec=Response)
        mock_response.status_code = 409
        mock_response.text = '{"error": "A request with this identifier is already pending"}'
        mock_response.ok = False
        mock_client.send.return_value = mock_response

        # Should return [] instead of raising AwaitingAsyncProcessing
        result = async_polling_strategy._initial_request_access(
            mock_client, request_task, mock_query_config, {"email": ["test@example.com"]}
        )

        assert result == []
        assert len(request_task.sub_requests) == 0
        mock_client.send.assert_called_once()

    def test_initial_request_access_mixed_ignored_and_success(
        self, db, async_polling_strategy
    ):
        """
        Integration test: when some initial requests succeed (creating sub-requests)
        and others are ignored (409), _initial_request_access should raise
        AwaitingAsyncProcessing for the successful ones.
        """
        request_task = RequestTask.create(
            db,
            data={
                "id": "test_access_mixed",
                "collection_address": "test_dataset:test_collection",
                "dataset_name": "test_dataset",
                "collection_name": "test_collection",
                "status": "pending",
                "action_type": "access",
            },
        )

        mock_privacy_request = MagicMock()
        mock_privacy_request.policy = Policy()
        request_task.privacy_request = mock_privacy_request

        read_request = ReadSaaSRequest(
            method="GET",
            path="/api/start-request",
            correlation_id_path="request_id",
            ignore_errors=[409],
            async_config={"strategy": "polling", "configuration": {
                "status_request": {
                    "method": "GET",
                    "path": "/status/<correlation_id>",
                    "status_path": "status",
                    "status_completed_value": "completed",
                },
            }},
        )

        mock_query_config = MagicMock()
        mock_query_config.get_read_requests_by_identity.return_value = [read_request]

        # Two prepared requests: first succeeds, second gets 409
        success_response = Mock(spec=Response)
        success_response.status_code = 200
        success_response.ok = True
        success_response.json.return_value = {"request_id": "corr_123"}

        ignored_response = Mock(spec=Response)
        ignored_response.status_code = 409
        ignored_response.text = "Already pending"
        ignored_response.ok = False

        mock_client = MagicMock()
        mock_client.send.side_effect = [success_response, ignored_response]

        mock_query_config.generate_requests.return_value = [
            (MagicMock(), {"email": "user1@example.com"}),
            (MagicMock(), {"email": "user2@example.com"}),
        ]

        # Should raise AwaitingAsyncProcessing because one sub-request was created
        with pytest.raises(AwaitingAsyncProcessing):
            async_polling_strategy._initial_request_access(
                mock_client, request_task, mock_query_config, {"email": ["user1@example.com", "user2@example.com"]}
            )

        # Only one sub-request created (the successful one), the 409 was skipped
        assert len(request_task.sub_requests) == 1
        assert mock_client.send.call_count == 2

    def test_initial_request_erasure_all_ignored_returns_zero(
        self, db, async_polling_strategy
    ):
        """
        Integration test: when all initial erasure requests return an ignored error
        (e.g. 409), _initial_request_erasure should return 0 instead of raising
        AwaitingAsyncProcessing.
        """
        request_task = RequestTask.create(
            db,
            data={
                "id": "test_erasure_all_ignored",
                "collection_address": "test_dataset:test_collection",
                "dataset_name": "test_dataset",
                "collection_name": "test_collection",
                "status": "pending",
                "action_type": "erasure",
            },
        )

        mock_privacy_request = MagicMock()
        mock_privacy_request.policy = erasure_policy(db)
        request_task.privacy_request = mock_privacy_request

        # Create a masking request with async_config and ignore_errors including 409
        masking_request = MagicMock()
        masking_request.async_config = {"strategy": "polling", "configuration": {}}
        masking_request.ignore_errors = [409]
        masking_request.path = "/api/delete"
        masking_request.skip_missing_param_values = False

        mock_query_config = MagicMock()
        mock_query_config.get_masking_request.return_value = masking_request
        mock_query_config.generate_update_param_values.return_value = {"user_id": "123"}
        mock_query_config.generate_update_stmt.return_value = MagicMock()

        # Mock client returning 409
        mock_client = MagicMock()
        mock_response = Mock(spec=Response)
        mock_response.status_code = 409
        mock_response.text = "Already pending"
        mock_response.ok = False
        mock_client.send.return_value = mock_response

        # Should return 0 instead of raising AwaitingAsyncProcessing
        result = async_polling_strategy._initial_request_erasure(
            mock_client, request_task, mock_query_config, [{"user_id": "123"}]
        )

        assert result == 0
        assert len(request_task.sub_requests) == 0
        mock_client.send.assert_called_once()
