import json
from unittest.mock import Mock, patch

import pydash
import pytest
from requests import Response

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.schemas.saas.saas_config import SaaSRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod
from fides.api.schemas.saas.strategy_configuration import PollingAsyncDSRConfiguration
from fides.api.service.async_dsr.async_dsr_strategy_polling import (
    PollingAsyncDSRStrategy,
)
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient


class TestPollingAsyncDSRStrategy:
    STATUS_PATH = "ready"
    RESULT_PATH = "data.results"

    @pytest.fixture
    def polling_strategy(self):
        """Create a PollingAsyncDSRStrategy with basic configuration"""
        config = PollingAsyncDSRConfiguration(
            status_request=SaaSRequest(
                method=HTTPMethod.GET,
                path="/api/status/<request_id>",
            ),
            status_path=self.STATUS_PATH,
            result_request=SaaSRequest(
                method=HTTPMethod.GET,
                path="/api/result/<request_id>",
            ),
            result_path=self.RESULT_PATH,
        )
        return PollingAsyncDSRStrategy(configuration=config)

    @pytest.fixture
    def mock_client(self):
        """Create a mock authenticated client"""
        return Mock(spec=AuthenticatedClient)

    @pytest.fixture
    def secrets(self):
        """Create sample secrets"""
        return {
            "api_token": "test_api_token_123",
            "request_id": "req_12345",
            "client_secret": "test_secret",
        }

    @pytest.fixture
    def identity_data(self):
        """Create sample identity data"""
        return {
            "email": "test@example.com",
            "user_id": "123",
            "phone": "+1234567890",
        }

    @pytest.fixture
    def status_response_ready(self):
        """Create a mock response indicating the request is ready"""
        response = Mock(spec=Response)
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"status": "completed", self.STATUS_PATH: True}
        return response

    @pytest.fixture
    def status_response_not_ready(self):
        """Create a mock response indicating the request is not ready"""
        response = Mock(spec=Response)
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"status": "processing", self.STATUS_PATH: False}
        return response

    @pytest.fixture
    def status_response_error(self):
        """Create a mock response indicating an error"""
        response = Mock(spec=Response)
        response.ok = False
        response.status_code = 500
        response.json.return_value = {"error": "Internal server error"}
        return response

    @pytest.fixture
    def result_response(self):
        """Create a mock response with result data"""
        response = Mock(spec=Response)
        response.ok = True
        response.status_code = 200
        response.json.return_value = {
            "data": {
                "results": [
                    {"id": 1, "name": "John Doe", "email": "john@example.com"},
                    {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
                ]
            },
            "metadata": {"total": 2, "processed_at": "2023-01-01T12:00:00Z"},
        }
        return response

    def test_get_status_request_ready(
        self,
        polling_strategy,
        mock_client,
        secrets,
        identity_data,
        status_response_ready,
    ):
        """Test get_status_request when the request is ready"""
        mock_client.send.return_value = status_response_ready

        result = polling_strategy.get_status_request(
            client=mock_client, secrets=secrets, identity_data=identity_data
        )

        # Should return True when status indicates ready
        assert result is True
        mock_client.send.assert_called_once()

    def test_get_status_request_not_ready(
        self,
        polling_strategy,
        mock_client,
        secrets,
        identity_data,
        status_response_not_ready,
    ):
        """Test get_status_request when the request is not ready"""
        mock_client.send.return_value = status_response_not_ready

        result = polling_strategy.get_status_request(
            client=mock_client, secrets=secrets, identity_data=identity_data
        )

        # Should return False when status indicates not ready
        assert result is False
        mock_client.send.assert_called_once()

    def test_get_status_request_error_response(
        self,
        polling_strategy,
        mock_client,
        secrets,
        identity_data,
        status_response_error,
    ):
        """Test get_status_request when there's an error response"""
        mock_client.send.return_value = status_response_error
        with pytest.raises(PrivacyRequestError):
            polling_strategy.get_status_request(
                client=mock_client, secrets=secrets, identity_data=identity_data
            )

    def test_get_result_request_success(
        self, polling_strategy, mock_client, secrets, identity_data, result_response
    ):
        """Test get_result_request when data is successfully retrieved"""
        mock_client.send.return_value = result_response

        result = polling_strategy.get_result_request(
            client=mock_client, secrets=secrets, identity_data=identity_data
        )

        # Should extract data using the result_path
        expected_data = [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
        ]
        assert result == expected_data
        mock_client.send.assert_called_once()

    def test_get_result_request_no_data_at_path(
        self, polling_strategy, mock_client, secrets, identity_data
    ):
        """Test get_result_request when no data exists at the specified path"""
        response = Mock(spec=Response)
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"other_field": "some_value"}
        mock_client.send.return_value = response

        result = polling_strategy.get_result_request(
            client=mock_client, secrets=secrets, identity_data=identity_data
        )

        # Should return None when no data found at path
        assert result is None

    def test_get_result_request_error_response(
        self, polling_strategy, mock_client, secrets, identity_data
    ):
        """Test get_result_request when there's an error response"""
        error_response = Mock(spec=Response)
        error_response.ok = False
        error_response.status_code = 404
        mock_client.send.return_value = error_response
        with pytest.raises(PrivacyRequestError):
            polling_strategy.get_result_request(
                client=mock_client, secrets=secrets, identity_data=identity_data
            )


class TestPollingAsyncDSRStrategyStatusPathTypes:
    """Test different status path value types that the polling strategy handles"""

    @pytest.fixture
    def polling_strategy_with_string_status(self):
        """Create a strategy that expects string status values"""
        config = PollingAsyncDSRConfiguration(
            status_request=SaaSRequest(
                method=HTTPMethod.GET,
                path="/api/status/<request_id>",
            ),
            status_path="status",
            status_completed_value="completed",  # String value to match
            result_request=SaaSRequest(
                method=HTTPMethod.GET,
                path="/api/result/<request_id>",
            ),
            result_path="data.results",
        )
        return PollingAsyncDSRStrategy(configuration=config)

    @pytest.fixture
    def polling_strategy_with_list_status(self):
        """Create a strategy that expects list status values"""
        config = PollingAsyncDSRConfiguration(
            status_request=SaaSRequest(
                method=HTTPMethod.GET,
                path="/api/status/<request_id>",
            ),
            status_path="status_array",
            status_completed_value="done",  # Value to match in list
            result_request=SaaSRequest(
                method=HTTPMethod.GET,
                path="/api/result/<request_id>",
            ),
            result_path="data.results",
        )
        return PollingAsyncDSRStrategy(configuration=config)

    @pytest.fixture
    def mock_client(self):
        """Create a mock authenticated client"""
        return Mock(spec=AuthenticatedClient)

    @pytest.fixture
    def secrets(self):
        """Create sample secrets"""
        return {"api_token": "test_token", "request_id": "123"}

    @pytest.fixture
    def identity_data(self):
        """Create sample identity data"""
        return {"email": "test@example.com"}

    def test_status_path_boolean_true(
        self, polling_strategy_with_string_status, mock_client, secrets, identity_data
    ):
        """Test status path returns boolean True"""
        response = Mock(spec=Response)
        response.ok = True
        response.json.return_value = {"status": True}  # Boolean True
        mock_client.send.return_value = response

        result = polling_strategy_with_string_status.get_status_request(
            client=mock_client, secrets=secrets, identity_data=identity_data
        )

        assert result is True

    def test_status_path_boolean_false(
        self, polling_strategy_with_string_status, mock_client, secrets, identity_data
    ):
        """Test status path returns boolean False"""
        response = Mock(spec=Response)
        response.ok = True
        response.json.return_value = {"status": False}  # Boolean False
        mock_client.send.return_value = response

        result = polling_strategy_with_string_status.get_status_request(
            client=mock_client, secrets=secrets, identity_data=identity_data
        )

        assert result is False

    def test_status_path_string_completed(
        self, polling_strategy_with_string_status, mock_client, secrets, identity_data
    ):
        """Test status path returns string that matches completed value"""
        response = Mock(spec=Response)
        response.ok = True
        response.json.return_value = {"status": "completed"}  # Matches status_completed_value
        mock_client.send.return_value = response

        result = polling_strategy_with_string_status.get_status_request(
            client=mock_client, secrets=secrets, identity_data=identity_data
        )

        assert result is True

    def test_status_path_string_pending(
        self, polling_strategy_with_string_status, mock_client, secrets, identity_data
    ):
        """Test status path returns string that doesn't match completed value"""
        response = Mock(spec=Response)
        response.ok = True
        response.json.return_value = {"status": "pending"}  # Doesn't match status_completed_value
        mock_client.send.return_value = response

        result = polling_strategy_with_string_status.get_status_request(
            client=mock_client, secrets=secrets, identity_data=identity_data
        )

        assert result is False

    def test_status_path_string_processing(
        self, polling_strategy_with_string_status, mock_client, secrets, identity_data
    ):
        """Test status path returns different string value"""
        response = Mock(spec=Response)
        response.ok = True
        response.json.return_value = {"status": "processing"}  # Doesn't match
        mock_client.send.return_value = response

        result = polling_strategy_with_string_status.get_status_request(
            client=mock_client, secrets=secrets, identity_data=identity_data
        )

        assert result is False

    def test_status_path_list_first_element_matches(
        self, polling_strategy_with_list_status, mock_client, secrets, identity_data
    ):
        """Test status path returns list where first element matches"""
        response = Mock(spec=Response)
        response.ok = True
        response.json.return_value = {
            "status_array": ["done", "processed", "validated"]  # First element matches
        }
        mock_client.send.return_value = response

        result = polling_strategy_with_list_status.get_status_request(
            client=mock_client, secrets=secrets, identity_data=identity_data
        )

        assert result is True

    def test_status_path_list_first_element_no_match(
        self, polling_strategy_with_list_status, mock_client, secrets, identity_data
    ):
        """Test status path returns list where first element doesn't match"""
        response = Mock(spec=Response)
        response.ok = True
        response.json.return_value = {
            "status_array": ["pending", "done", "validated"]  # First element doesn't match
        }
        mock_client.send.return_value = response

        result = polling_strategy_with_list_status.get_status_request(
            client=mock_client, secrets=secrets, identity_data=identity_data
        )

        assert result is False

    def test_status_path_list_empty(
        self, polling_strategy_with_list_status, mock_client, secrets, identity_data
    ):
        """Test status path returns empty list"""
        response = Mock(spec=Response)
        response.ok = True
        response.json.return_value = {"status_array": []}  # Empty list
        mock_client.send.return_value = response

        with pytest.raises(IndexError):
            polling_strategy_with_list_status.get_status_request(
                client=mock_client, secrets=secrets, identity_data=identity_data
            )

    def test_status_path_unexpected_type_integer(
        self, polling_strategy_with_string_status, mock_client, secrets, identity_data
    ):
        """Test status path returns unexpected type (integer)"""
        response = Mock(spec=Response)
        response.ok = True
        response.json.return_value = {"status": 123}  # Integer - unexpected type
        mock_client.send.return_value = response

        with pytest.raises(PrivacyRequestError) as exc_info:
            polling_strategy_with_string_status.get_status_request(
                client=mock_client, secrets=secrets, identity_data=identity_data
            )

        assert "Status request returned an unexpected value: 123" in str(exc_info.value)

    def test_status_path_unexpected_type_dict(
        self, polling_strategy_with_string_status, mock_client, secrets, identity_data
    ):
        """Test status path returns unexpected type (dictionary)"""
        response = Mock(spec=Response)
        response.ok = True
        response.json.return_value = {"status": {"nested": "value"}}  # Dict - unexpected type
        mock_client.send.return_value = response

        with pytest.raises(PrivacyRequestError) as exc_info:
            polling_strategy_with_string_status.get_status_request(
                client=mock_client, secrets=secrets, identity_data=identity_data
            )

        assert "Status request returned an unexpected value:" in str(exc_info.value)

    def test_status_path_none_value(
        self, polling_strategy_with_string_status, mock_client, secrets, identity_data
    ):
        """Test status path returns None"""
        response = Mock(spec=Response)
        response.ok = True
        response.json.return_value = {"status": None}  # None value
        mock_client.send.return_value = response

        with pytest.raises(PrivacyRequestError) as exc_info:
            polling_strategy_with_string_status.get_status_request(
                client=mock_client, secrets=secrets, identity_data=identity_data
            )

        assert "Status request returned an unexpected value: None" in str(exc_info.value)
