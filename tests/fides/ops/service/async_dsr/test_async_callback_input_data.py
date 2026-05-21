from unittest.mock import MagicMock

import pytest

from fides.api.common_exceptions import AwaitingAsyncTask
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.privacy_request.request_task import AsyncTaskType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.async_dsr.strategies.async_dsr_strategy_callback import (
    AsyncCallbackStrategy,
)
from tests.fides.ops.graph.graph_test_util import erasure_policy


@pytest.mark.async_dsr
class TestAsyncCallbackInputData:
    def test_async_mask_data_forwards_input_data(self, db):
        """
        Verify that AsyncCallbackStrategy.async_mask_data passes input_data
        through to generate_update_stmt so that connectors with external
        references can resolve placeholders.
        """
        policy = erasure_policy(db)
        privacy_request = PrivacyRequest.create(
            db,
            data={
                "policy_id": policy.id,
                "status": PrivacyRequestStatus.pending,
            },
        )
        request_task = RequestTask.create(
            db,
            data={
                "id": "test_callback_input_data",
                "collection_address": "test_dataset:test_collection",
                "dataset_name": "test_dataset",
                "collection_name": "test_collection",
                "status": "pending",
                "action_type": "erasure",
                "privacy_request_id": privacy_request.id,
            },
        )

        input_data = {"mi_u": ["external_user_id"]}
        rows = [{"user_id": "abc"}]

        masking_request = MagicMock()
        masking_request.async_config = {"strategy": "callback", "configuration": {}}
        masking_request.path = "/api/delete"
        masking_request.skip_missing_param_values = False
        masking_request.ignore_errors = False

        mock_query_config = MagicMock()
        mock_query_config.get_masking_request.return_value = masking_request
        mock_query_config.get_read_requests_by_identity.return_value = []

        mock_client = MagicMock()

        strategy = AsyncCallbackStrategy(session=db)

        with pytest.raises(AwaitingAsyncTask):
            strategy.async_mask_data(
                client=mock_client,
                request_task_id=request_task.id,
                query_config=mock_query_config,
                rows=rows,
                input_data=input_data,
            )

        # Verify input_data was forwarded to generate_update_stmt
        mock_query_config.generate_update_stmt.assert_called_once_with(
            rows[0], policy, privacy_request, input_data
        )

    def test_initial_request_erasure_forwards_input_data_for_multiple_rows(self, db):
        """
        Verify that _initial_request_erasure passes input_data to
        generate_update_stmt for each row in the erasure batch.
        """
        policy = erasure_policy(db)
        privacy_request = PrivacyRequest.create(
            db,
            data={
                "policy_id": policy.id,
                "status": PrivacyRequestStatus.pending,
            },
        )
        request_task = RequestTask.create(
            db,
            data={
                "id": "test_callback_multi_row",
                "collection_address": "test_dataset:test_collection",
                "dataset_name": "test_dataset",
                "collection_name": "test_collection",
                "status": "pending",
                "action_type": "erasure",
                "privacy_request_id": privacy_request.id,
            },
        )

        input_data = {"mi_u": ["ext_123"], "email": ["user@test.com"]}
        rows = [{"user_id": "row1"}, {"user_id": "row2"}, {"user_id": "row3"}]

        masking_request = MagicMock()
        masking_request.async_config = {"strategy": "callback", "configuration": {}}
        masking_request.path = "/api/delete"
        masking_request.skip_missing_param_values = False
        masking_request.ignore_errors = False

        mock_query_config = MagicMock()
        mock_query_config.get_masking_request.return_value = masking_request

        mock_client = MagicMock()

        strategy = AsyncCallbackStrategy(session=db)

        with pytest.raises(AwaitingAsyncTask):
            strategy._initial_request_erasure(
                mock_client, request_task, mock_query_config, rows, input_data
            )

        # All three rows should have input_data forwarded
        assert mock_query_config.generate_update_stmt.call_count == 3
        for call in mock_query_config.generate_update_stmt.call_args_list:
            assert call[0][3] == input_data  # 4th positional arg is input_data

    def test_async_mask_data_works_without_input_data(self, db):
        """
        Verify that async_mask_data still works when input_data is None
        (backwards compatibility for connectors without external references).
        """
        policy = erasure_policy(db)
        privacy_request = PrivacyRequest.create(
            db,
            data={
                "policy_id": policy.id,
                "status": PrivacyRequestStatus.pending,
            },
        )
        request_task = RequestTask.create(
            db,
            data={
                "id": "test_callback_no_input_data",
                "collection_address": "test_dataset:test_collection",
                "dataset_name": "test_dataset",
                "collection_name": "test_collection",
                "status": "pending",
                "action_type": "erasure",
                "privacy_request_id": privacy_request.id,
            },
        )

        rows = [{"user_id": "abc"}]

        masking_request = MagicMock()
        masking_request.async_config = {"strategy": "callback", "configuration": {}}
        masking_request.path = "/api/delete"
        masking_request.skip_missing_param_values = False
        masking_request.ignore_errors = False

        mock_query_config = MagicMock()
        mock_query_config.get_masking_request.return_value = masking_request
        mock_query_config.get_read_requests_by_identity.return_value = []

        mock_client = MagicMock()

        strategy = AsyncCallbackStrategy(session=db)

        with pytest.raises(AwaitingAsyncTask):
            strategy.async_mask_data(
                client=mock_client,
                request_task_id=request_task.id,
                query_config=mock_query_config,
                rows=rows,
                # input_data intentionally omitted
            )

        # input_data should default to None
        mock_query_config.generate_update_stmt.assert_called_once_with(
            rows[0], policy, privacy_request, None
        )
