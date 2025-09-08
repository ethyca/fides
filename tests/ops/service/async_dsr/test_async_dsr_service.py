"""
Tests for async DSR service functionality.
Tests the core service methods that handle asynchronous data subject requests.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.privacy_request.request_task import AsyncTaskType
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.schemas.saas.saas_config import SaaSRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod
from fides.api.schemas.saas.strategy_configuration import PollingAsyncDSRConfiguration
from fides.api.service.async_dsr.async_dsr_service import (
    execute_erasure_polling_requests,
    execute_read_polling_requests,
    execute_read_result_request,
    get_connection_config_from_task,
    execute_polling_task,
)
from fides.api.service.async_dsr.async_dsr_strategy_polling import (
    PollingAsyncDSRStrategy,
)
from fides.api.service.connectors.query_configs.saas_query_config import SaaSQueryConfig
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.connectors.saas_connector import SaaSConnector


@pytest.mark.integration_saas
class TestAsyncDSRService:
    """Test suite for async DSR service methods"""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_privacy_request(self):
        """Create a mock privacy request"""
        request = Mock(spec=PrivacyRequest)
        request.id = "pr_12345"
        request.status = PrivacyRequestStatus.in_processing
        request.policy = Mock(spec=Policy)
        request.get_persisted_identity.return_value.labeled_dict.return_value = {
            "email": "test@example.com",
            "user_id": "123",
        }
        request.get_cached_identity_data.return_value = {"phone": "+1234567890"}
        return request

    @pytest.fixture
    def mock_request_task(self, mock_privacy_request):
        """Create a mock request task"""
        task = Mock(spec=RequestTask)
        task.id = "req_12345"
        task.dataset_name = "test_dataset"
        task.collection_address = "test_dataset:users"
        task.action_type = ActionType.access
        task.async_type = AsyncTaskType.polling
        task.privacy_request = mock_privacy_request
        task.get_access_data.return_value = []
        task.access_data = []
        task.callback_succeeded = False
        task.update_status = Mock()
        task.save = Mock()
        return task

    @pytest.fixture
    def mock_connection_config(self):
        """Create a mock connection config"""
        config = Mock(spec=ConnectionConfig)
        config.id = "conn_12345"
        config.key = "test_connector"
        return config

    @pytest.fixture
    def mock_dataset_config(self, mock_connection_config):
        """Create a mock dataset config"""
        config = Mock(spec=DatasetConfig)
        config.fides_key = "test_dataset"
        config.connection_config_id = mock_connection_config.id
        return config

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
        read_request = Mock()
        read_request.async_config = Mock()
        read_request.async_config.strategy = "polling"
        read_request.async_config.configuration = {
            "status_request": {"method": "GET", "path": "/api/status/<request_id>"},
            "result_request": {"method": "GET", "path": "/api/results/<request_id>"},
            "result_path": "data",
        }

        config.get_read_requests_by_identity.return_value = [read_request]
        return config

    def test_execute_polling_task_invalid_status(
        self, mock_db_session, mock_request_task, mock_privacy_request
    ):
        """Test that requeue fails with invalid privacy request status"""
        mock_privacy_request.status = PrivacyRequestStatus.complete

        with pytest.raises(PrivacyRequestError) as exc_info:
            execute_polling_task(mock_db_session, mock_request_task)

        assert "Cannot re-queue privacy request" in str(exc_info.value)
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
        mock_db_session,
        mock_request_task,
        mock_connection_config,
    ):
        """Test successful requeue of access polling request"""
        # Setup mocks
        mock_get_connection.return_value = mock_connection_config
        mock_graph_task = Mock()
        mock_graph_task.connector = Mock(spec=SaaSConnector)
        mock_graph_task.execution_node = Mock(spec=ExecutionNode)
        mock_create_graph_task.return_value = mock_graph_task

        mock_query_config = Mock(spec=SaaSQueryConfig)
        mock_graph_task.connector.query_config.return_value = mock_query_config
        mock_graph_task.connector.set_privacy_request_state = Mock()

        # Test access task requeue
        mock_request_task.action_type = ActionType.access
        mock_request_task.upstream_tasks_objects.return_value = []

        execute_polling_task(mock_db_session, mock_request_task)

        # Verify the access-specific path was taken
        mock_execute_read.assert_called_once_with(
            mock_db_session,
            mock_request_task,
            mock_query_config,
            mock_graph_task.connector,
        )

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
        mock_db_session,
        mock_request_task,
        mock_connection_config,
    ):
        """Test successful requeue of erasure polling request"""
        # Setup mocks
        mock_get_connection.return_value = mock_connection_config
        mock_graph_task = Mock()
        mock_graph_task.connector = Mock(spec=SaaSConnector)
        mock_create_graph_task.return_value = mock_graph_task

        mock_query_config = Mock(spec=SaaSQueryConfig)
        mock_graph_task.connector.query_config.return_value = mock_query_config
        mock_graph_task.connector.set_privacy_request_state = Mock()

        # Test erasure task requeue
        mock_request_task.action_type = ActionType.erasure

        execute_polling_task(mock_db_session, mock_request_task)

        # Verify the erasure-specific path was taken
        mock_execute_erasure.assert_called_once_with(
            mock_db_session, mock_request_task, mock_query_config
        )

    @patch(
        "fides.api.service.async_dsr.async_dsr_service.AsyncDSRStrategy.get_strategy"
    )
    def test_execute_read_polling_requests_status_not_ready(
        self,
        mock_get_strategy,
        mock_db_session,
        mock_request_task,
        mock_query_config,
        mock_saas_connector,
    ):
        """Test execute_read_polling_requests when status is not ready"""
        # Setup strategy mock
        mock_strategy = Mock(spec=PollingAsyncDSRStrategy)
        mock_strategy.get_status_request.return_value = False  # Not ready
        mock_get_strategy.return_value = mock_strategy

        execute_read_polling_requests(
            mock_db_session, mock_request_task, mock_query_config, mock_saas_connector
        )

        # Verify status was checked but result wasn't fetched
        mock_strategy.get_status_request.assert_called_once()
        mock_strategy.get_result_request.assert_not_called()

    @patch(
        "fides.api.service.async_dsr.async_dsr_service.AsyncDSRStrategy.get_strategy"
    )
    @patch("fides.api.service.async_dsr.async_dsr_service.execute_read_result_request")
    def test_execute_read_polling_requests_status_ready(
        self,
        mock_execute_result,
        mock_get_strategy,
        mock_db_session,
        mock_request_task,
        mock_query_config,
        mock_saas_connector,
    ):
        """Test execute_read_polling_requests when status is ready"""
        # Setup strategy mock
        mock_strategy = Mock(spec=PollingAsyncDSRStrategy)
        mock_strategy.get_status_request.return_value = True  # Ready
        mock_get_strategy.return_value = mock_strategy

        execute_read_polling_requests(
            mock_db_session, mock_request_task, mock_query_config, mock_saas_connector
        )

        # Verify both status check and result fetch were called
        mock_strategy.get_status_request.assert_called_once()
        mock_execute_result.assert_called_once_with(
            mock_db_session,
            mock_request_task,
            mock_strategy,
            mock_saas_connector.create_client.return_value,
            mock_saas_connector.secrets,
            mock_request_task.privacy_request.get_persisted_identity.return_value.labeled_dict.return_value
            | mock_request_task.privacy_request.get_cached_identity_data.return_value,
        )

    @patch("fides.api.service.async_dsr.async_dsr_service.log_task_queued")
    @patch("fides.api.service.async_dsr.async_dsr_service.queue_request_task")
    def test_execute_read_result_request_with_data(
        self,
        mock_queue_task,
        mock_log_queued,
        mock_db_session,
        mock_request_task,
    ):
        """Test execute_read_result_request when data is returned"""
        # Setup mocks
        mock_strategy = Mock(spec=PollingAsyncDSRStrategy)
        mock_strategy.get_result_request.return_value = [
            {"id": 1, "name": "John Doe"},
            {"id": 2, "name": "Jane Smith"},
        ]

        mock_client = Mock(spec=AuthenticatedClient)
        secrets = {"api_key": "test"}
        identity_data = {"email": "test@example.com"}

        execute_read_result_request(
            mock_db_session,
            mock_request_task,
            mock_strategy,
            mock_client,
            secrets,
            identity_data,
        )

        # Verify result was processed correctly
        mock_strategy.get_result_request.assert_called_once_with(
            mock_client, secrets, identity_data
        )

        # Verify task was updated
        assert mock_request_task.callback_succeeded is True
        mock_request_task.update_status.assert_called_with(
            mock_db_session, ExecutionLogStatus.pending
        )
        mock_request_task.save.assert_called_with(mock_db_session)

        # Verify task was queued for next step
        mock_log_queued.assert_called_once_with(mock_request_task, "callback")
        mock_queue_task.assert_called_once_with(
            mock_request_task, privacy_request_proceed=True
        )

    @patch("fides.api.service.async_dsr.async_dsr_service.log_task_queued")
    @patch("fides.api.service.async_dsr.async_dsr_service.queue_request_task")
    def test_execute_read_result_request_no_data(
        self,
        mock_db_session,
        mock_request_task,
    ):
        """Test that when no data is returned, the task is not updated"""

        # Setup mocks
        mock_strategy = Mock(spec=PollingAsyncDSRStrategy)
        mock_strategy.get_result_request.return_value = None  # No data

        mock_client = Mock(spec=AuthenticatedClient)
        secrets = {"api_key": "test"}
        identity_data = {"email": "test@example.com"}

        execute_read_result_request(
            mock_db_session,
            mock_request_task,
            mock_strategy,
            mock_client,
            secrets,
            identity_data,
        )

        # Verify task was updated
        mock_strategy.get_result_request.assert_called_once()
        assert mock_request_task.callback_succeeded is True
        mock_request_task.update_status.assert_called_with(
            mock_db_session, ExecutionLogStatus.pending
        )
        mock_request_task.save.assert_called_with(mock_db_session)
