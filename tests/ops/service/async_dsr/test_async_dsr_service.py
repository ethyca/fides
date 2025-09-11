"""
Tests for async DSR service functionality.
Tests the core service methods that handle asynchronous data subject requests.
"""

from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.privacy_request.request_task import (
    AsyncTaskType,
    RequestTaskRequestData,
)
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.schemas.saas.saas_config import ReadSaaSRequest
from fides.api.service.async_dsr.async_dsr_service import (
    execute_polling_task,
    execute_read_polling_requests,
    execute_result_request,
)
from fides.api.service.async_dsr.async_dsr_strategy_polling_base import (
    PollingAsyncDSRBaseStrategy,
)
from fides.api.service.connectors.query_configs.saas_query_config import SaaSQueryConfig
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.connectors.saas_connector import SaaSConnector


@pytest.mark.integration_saas
class TestAsyncDSRService:
    """Test suite for async DSR service methods"""

    @pytest.fixture
    def param_values(self):
        """Create sample param values"""
        return {
            "request_id": "req_12345",
            "api_token": "test_api_token_123",
            "client_secret": "test_secret",
            "email": "test@example.com",
            "user_id": "123",
            "phone": "+1234567890",
        }

    @pytest.fixture
    def mock_request_task_data(self):
        """Create a mock RequestTaskRequestData with proper attributes"""
        mock_data = Mock(spec=RequestTaskRequestData)
        mock_data.request_data = {
            "request_id": "req_12345",
        }
        return mock_data

    @pytest.fixture
    def mock_request_task(self, in_processing_privacy_request, mock_request_task_data):
        """Create a mock RequestTask with proper attributes"""
        mock_task = Mock(spec=RequestTask)
        mock_task.id = "req_12345"
        mock_task.privacy_request = in_processing_privacy_request
        mock_task.action_type = ActionType.access
        mock_task.status = ExecutionLogStatus.awaiting_processing
        mock_task.collection_address = "test_dataset:users"
        mock_task.dataset_name = "test_dataset"
        mock_task.collection_name = "users"
        mock_task.async_type = AsyncTaskType.polling
        mock_task.access_data = []
        mock_task.callback_succeeded = False
        mock_task.upstream_tasks_objects.return_value = []
        mock_task.save = Mock()
        mock_task.update_status = Mock()
        mock_task.request_data = mock_request_task_data
        return mock_task

    @pytest.fixture
    def mock_connection_config(self):
        """Create a mock ConnectionConfig instance"""
        mock_config = Mock(spec=ConnectionConfig)
        mock_config.id = "conn_12345"
        mock_config.key = "test_connector"
        mock_config.connection_type = "saas"
        mock_config.access = "read"
        return mock_config

    @pytest.fixture
    def mock_saas_connector(self):
        """Create a mock SaaS connector"""
        connector = Mock(spec=SaaSConnector)
        connector.create_client.return_value = Mock(spec=AuthenticatedClient)
        connector.secrets = {"api_key": "test_key"}
        return connector

    @pytest.fixture
    def mock_query_config(self):
        """Create a mock query config with async polling configuration"""
        config = Mock(spec=SaaSQueryConfig)

        # Create a read request with async config
        read_request = Mock(spec=ReadSaaSRequest)
        read_request.async_config = Mock()
        read_request.async_config.strategy = "polling_access_data"
        read_request.async_config.configuration = {
            "status_request": {"method": "GET", "path": "/api/status/<request_id>"},
            "result_request": {"method": "GET", "path": "/api/results/<request_id>"},
            "result_path": "data",
        }

        config.get_read_requests_by_identity.return_value = [read_request]
        return config

    def test_execute_polling_task_invalid_status(
        self, db, in_processing_privacy_request, polling_request_task
    ):
        """Test that execute_polling_task fails with invalid privacy request status"""
        # Change the privacy request status to complete (invalid for polling)
        in_processing_privacy_request.status = PrivacyRequestStatus.complete
        in_processing_privacy_request.save(db)

        with pytest.raises(PrivacyRequestError) as exc_info:
            execute_polling_task(
                in_processing_privacy_request.id, polling_request_task.id
            )

        assert "Cannot execute Polling Task" in str(exc_info.value)
        assert "with status complete" in str(exc_info.value)

    @patch(
        "fides.api.service.async_dsr.async_dsr_service.get_connection_config_from_task"
    )
    @patch("fides.api.service.async_dsr.async_dsr_service.TaskResources")
    @patch("fides.api.service.async_dsr.async_dsr_service.create_graph_task")
    @patch(
        "fides.api.service.async_dsr.async_dsr_service.execute_read_polling_requests"
    )
    def test_execute_polling_task_access_task(
        self,
        mock_execute_read,
        mock_create_graph_task,
        mock_task_resources,
        mock_get_connection,
        db,
        in_processing_privacy_request,
        polling_request_task,
        mock_connection_config,
    ):
        """Test successful execution of access polling request"""
        # Setup mocks
        mock_get_connection.return_value = mock_connection_config
        mock_graph_task = Mock()
        mock_graph_task.connector = Mock(spec=SaaSConnector)
        mock_graph_task.execution_node = Mock(spec=ExecutionNode)
        mock_create_graph_task.return_value = mock_graph_task

        mock_query_config = Mock(spec=SaaSQueryConfig)
        mock_graph_task.connector.query_config.return_value = mock_query_config
        mock_graph_task.connector.set_privacy_request_state = Mock()

        # Mock the task resources context manager
        mock_task_resources.return_value.__enter__.return_value = Mock()

        # Test access task execution
        polling_request_task.action_type = ActionType.access

        execute_polling_task(in_processing_privacy_request.id, polling_request_task.id)

        # Verify the access-specific path was taken
        mock_execute_read.assert_called_once()

    @patch(
        "fides.api.service.async_dsr.async_dsr_service.get_connection_config_from_task"
    )
    @patch("fides.api.service.async_dsr.async_dsr_service.TaskResources")
    @patch("fides.api.service.async_dsr.async_dsr_service.create_graph_task")
    @patch(
        "fides.api.service.async_dsr.async_dsr_service.execute_erasure_polling_requests"
    )
    def test_execute_polling_task_erasure_task(
        self,
        mock_execute_erasure,
        mock_create_graph_task,
        mock_task_resources,
        mock_get_connection,
        db,
        in_processing_privacy_request,
        polling_request_task,
        mock_connection_config,
    ):
        """Test successful execution of erasure polling request"""
        # Setup mocks
        mock_get_connection.return_value = mock_connection_config
        mock_graph_task = Mock()
        mock_graph_task.connector = Mock(spec=SaaSConnector)
        mock_create_graph_task.return_value = mock_graph_task

        mock_query_config = Mock(spec=SaaSQueryConfig)
        mock_graph_task.connector.query_config.return_value = mock_query_config
        mock_graph_task.connector.set_privacy_request_state = Mock()

        # Mock the task resources context manager
        mock_task_resources.return_value.__enter__.return_value = Mock()

        # Test erasure task execution
        polling_request_task.action_type = ActionType.erasure
        polling_request_task.save(db)
        execute_polling_task(in_processing_privacy_request.id, polling_request_task.id)

        # Verify the erasure-specific path was taken
        mock_execute_erasure.assert_called_once()

    @patch(
        "fides.api.service.async_dsr.async_dsr_service.AsyncDSRStrategy.get_strategy"
    )
    def test_execute_read_polling_requests_status_not_ready(
        self,
        mock_get_strategy,
        db,
        mock_request_task,
        mock_query_config,
        mock_saas_connector,
    ):
        """Test execute_read_polling_requests when status is not ready"""
        # Setup strategy mock
        mock_strategy = Mock(spec=PollingAsyncDSRBaseStrategy)
        mock_strategy.get_status_request.return_value = False  # Not ready
        mock_get_strategy.return_value = mock_strategy

        execute_read_polling_requests(
            db, mock_request_task, mock_query_config, mock_saas_connector
        )

        # Verify status was checked but result wasn't fetched
        mock_strategy.get_status_request.assert_called_once()
        mock_strategy.get_result_request.assert_not_called()

    @patch(
        "fides.api.service.async_dsr.async_dsr_service.AsyncDSRStrategy.get_strategy"
    )
    @patch("fides.api.service.async_dsr.async_dsr_service.execute_result_request")
    def test_execute_read_polling_requests_status_ready(
        self,
        mock_execute_result,
        mock_get_strategy,
        db,
        mock_request_task,
        mock_query_config,
        mock_saas_connector,
    ):
        """Test execute_read_polling_requests when status is ready"""
        # Setup strategy mock
        mock_strategy = Mock(spec=PollingAsyncDSRBaseStrategy)
        mock_strategy.get_status_request.return_value = True  # Ready
        mock_get_strategy.return_value = mock_strategy

        execute_read_polling_requests(
            db, mock_request_task, mock_query_config, mock_saas_connector
        )

        # Verify both status check and result fetch were called
        mock_strategy.get_status_request.assert_called_once()
        mock_execute_result.assert_called_once()

    @patch("fides.api.service.async_dsr.async_dsr_service.log_task_queued")
    @patch("fides.api.service.async_dsr.async_dsr_service.queue_request_task")
    def test_execute_read_result_request_with_data(
        self,
        mock_queue_task,
        mock_log_queued,
        db,
        mock_request_task,
        param_values,
    ):
        """Test execute_read_result_request when data is returned"""
        # Setup mocks
        mock_strategy = Mock(spec=PollingAsyncDSRBaseStrategy)
        mock_strategy.get_result_request.return_value = [
            {"id": 1, "name": "John Doe"},
            {"id": 2, "name": "Jane Smith"},
        ]

        mock_client = Mock(spec=AuthenticatedClient)

        execute_result_request(
            db,
            mock_request_task,
            mock_strategy,
            mock_client,
            param_values,
        )

        # Verify result was processed correctly
        mock_strategy.get_result_request.assert_called_once_with(
            mock_client, param_values
        )

        # Verify task was updated
        assert mock_request_task.callback_succeeded is True
        mock_request_task.update_status.assert_called_with(
            db, ExecutionLogStatus.complete
        )
        mock_request_task.save.assert_called_with(db)

        # Verify task was queued for next step
        mock_log_queued.assert_called_once_with(mock_request_task, "polling success")
        mock_queue_task.assert_called_once_with(
            mock_request_task, privacy_request_proceed=True
        )

    @patch("fides.api.service.async_dsr.async_dsr_service.log_task_queued")
    @patch("fides.api.service.async_dsr.async_dsr_service.queue_request_task")
    def test_execute_read_result_request_no_data(
        self,
        mock_queue_task,
        mock_log_queued,
        db,
        mock_request_task,
        param_values,
    ):
        """Test that when no data is returned, the task is not updated"""

        # Setup mocks
        mock_strategy = Mock(spec=PollingAsyncDSRBaseStrategy)
        mock_strategy.get_result_request.return_value = None  # No data

        mock_client = Mock(spec=AuthenticatedClient)

        execute_result_request(
            db,
            mock_request_task,
            mock_strategy,
            mock_client,
            param_values,
        )

        # Verify task was updated
        mock_strategy.get_result_request.assert_called_once()
        assert mock_request_task.callback_succeeded is True
        mock_request_task.update_status.assert_called_with(
            db, ExecutionLogStatus.complete
        )
        mock_request_task.save.assert_called_with(db)
