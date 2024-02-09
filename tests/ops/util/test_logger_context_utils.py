import pytest
from requests import PreparedRequest, Request, Response

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.service.connectors.saas_connector import SaaSConnector
from fides.api.util.logger_context_utils import (
    ErrorGroup,
    request_details,
    saas_connector_details,
)


class TestLoggerContestUtils:
    @pytest.fixture
    def prepared_request(self) -> PreparedRequest:
        return Request(
            method="POST",
            url="https://test/users",
            headers={"Content-type": "application/json"},
            params={"a": "b"},
            data={"name": "test"},
        ).prepare()

    def test_saas_connector_details(self, saas_example_connection_config, system):
        saas_example_connection_config.system_id = system.id
        connector = SaaSConnector(saas_example_connection_config)
        connector.current_collection_name = "customer"
        connector.current_privacy_request = PrivacyRequest(id="123")
        assert saas_connector_details(connector, action_type=ActionType.access) == {
            "system_key": system.fides_key,
            "connection_key": "saas_connector_example",
            "action_type": "access",
            "collection": "customer",
            "privacy_request_id": "123",
        }

    def test_request_details(self, prepared_request):
        response = Response()
        response.status_code = 200
        response._content = "test response".encode()

        assert request_details(prepared_request, response) == {
            "method": "POST",
            "url": "https://test/users?a=b",
            "body": "name=test",
            "response": "test response",
            "status_code": 200,
        }

    @pytest.mark.usefixtures("test_config_dev_mode_disabled")
    def test_request_details_dev_mode_disabled(self, prepared_request):
        response = Response()
        response.status_code = 200
        response._content = "test response".encode()

        assert request_details(prepared_request, response) == {
            "method": "POST",
            "url": "https://test/users?a=b",
            "status_code": 200,
        }

    @pytest.mark.parametrize(
        "ignore_error, status_code, error_group",
        [
            (True, 401, ErrorGroup.authentication_error.value),
            (True, 403, ErrorGroup.authentication_error.value),
            (True, 400, ErrorGroup.client_error.value),
            (True, 500, ErrorGroup.server_error.value),
            (False, 401, ErrorGroup.authentication_error.value),
            (False, 403, ErrorGroup.authentication_error.value),
            (False, 400, ErrorGroup.client_error.value),
            (False, 500, ErrorGroup.server_error.value),
        ],
    )
    def test_request_details_with_errors(
        self, ignore_error, status_code, error_group, prepared_request
    ):
        response = Response()
        response.status_code = status_code
        response._content = "test response".encode()

        expected_detail = {
            "method": "POST",
            "url": "https://test/users?a=b",
            "body": "name=test",
            "response": "test response",
            "status_code": status_code,
        }
        if not ignore_error:
            expected_detail["error_group"] = error_group

        assert (
            request_details(prepared_request, response, ignore_error) == expected_detail
        )

    @pytest.mark.parametrize(
        "ignore_error, status_code, error_group",
        [
            (True, 401, ErrorGroup.authentication_error.value),
            (True, 403, ErrorGroup.authentication_error.value),
            (True, 400, ErrorGroup.client_error.value),
            (True, 500, ErrorGroup.server_error.value),
            (False, 401, ErrorGroup.authentication_error.value),
            (False, 403, ErrorGroup.authentication_error.value),
            (False, 400, ErrorGroup.client_error.value),
            (False, 500, ErrorGroup.server_error.value),
        ],
    )
    @pytest.mark.usefixtures("test_config_dev_mode_disabled")
    def test_request_details_with_errors_dev_mode_disabled(
        self, ignore_error, status_code, error_group, prepared_request
    ):
        response = Response()
        response.status_code = status_code
        response._content = "test response".encode()

        expected_detail = {
            "method": "POST",
            "url": "https://test/users?a=b",
            "status_code": status_code,
        }
        if not ignore_error:
            expected_detail["error_group"] = error_group

        assert (
            request_details(prepared_request, response, ignore_error) == expected_detail
        )
