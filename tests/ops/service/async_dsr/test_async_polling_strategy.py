from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time

from fides.api.common_exceptions import AwaitingAsyncProcessing, PrivacyRequestError
from fides.api.models.privacy_request.request_task import (
    RequestTask,
    RequestTaskSubRequest,
)
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.saas.async_polling_configuration import (
    AsyncPollingConfiguration,
    PollingResultRequest,
    PollingStatusRequest,
)
from fides.api.service.async_dsr.strategies.async_dsr_strategy_factory import (
    get_strategy,
)
from fides.api.service.async_dsr.strategies.async_dsr_strategy_polling import (
    AsyncPollingStrategy,
)
from fides.config import CONFIG


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
        sub_requests = request_task.sub_requests.all()
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

        # Mock the access data to be returned
        request_task.access_data = [{"id": 1, "name": "test"}]
        db.commit()

        result = async_polling_strategy.async_retrieve_data(
            client=mock_client,
            request_task_id=request_task.id,
            query_config=mock_query_config,
            input_data=MagicMock(),
        )

        assert result == [{"id": 1, "name": "test"}]

    def test_polling_completion_with_mixed_sub_request_statuses(
        self, multi_sub_request_task, async_polling_strategy, db
    ):
        """Test polling completion logic with various sub-request statuses"""
        request_task = multi_sub_request_task

        # Mock client and query_config
        mock_client = MagicMock()
        mock_query_config = MagicMock()

        # Test with mixed statuses: complete, error, pending
        sub_requests = request_task.sub_requests.all()
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

        # Mock the access data to be returned
        request_task.access_data = [{"id": 1, "name": "test"}]
        db.commit()

        result = async_polling_strategy.async_retrieve_data(
            client=mock_client,
            request_task_id=request_task.id,
            query_config=mock_query_config,
            input_data=MagicMock(),
        )

        assert result == [{"id": 1, "name": "test"}]

    def test_polling_completion_with_no_sub_requests(
        self, access_request_task, async_polling_strategy, db
    ):
        """Test polling completion when there are no sub-requests"""
        request_task = access_request_task

        # Remove the existing sub-request by deleting each one individually
        for sub_request in request_task.sub_requests.all():
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
