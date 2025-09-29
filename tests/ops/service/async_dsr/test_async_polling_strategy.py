from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time

from fides.api.common_exceptions import PrivacyRequestError
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
