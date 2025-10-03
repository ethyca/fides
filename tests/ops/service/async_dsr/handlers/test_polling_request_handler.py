import pytest
from starlette.status import HTTP_200_OK

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.schemas.saas.async_polling_configuration import (
    PollingResultRequest,
    PollingStatusRequest,
)
from fides.api.schemas.saas.shared_schemas import HTTPMethod
from fides.api.service.async_dsr.handlers.polling_request_handler import (
    PollingRequestHandler,
)
from tests.ops.test_helpers.saas_test_utils import MockAuthenticatedClient


@pytest.mark.async_dsr
class TestPollingRequestHandler:

    def test_get_status_response_success(self):
        client = MockAuthenticatedClient()
        client.add_response(
            "GET",
            "/api/status/req_12345",
            {"status": "completed"},
            status_code=200,
        )
        polling_request_handler = PollingRequestHandler(
            status_request=PollingStatusRequest(
                method=HTTPMethod.GET,
                path="/api/status/<request_id>",
                status_path="status",
                status_completed_value="completed",
            ),
            result_request=PollingResultRequest(
                method=HTTPMethod.GET,
                path="/api/result/<request_id>",
            ),
        )
        param_values = {
            "request_id": "req_12345",
        }
        response = polling_request_handler.get_status_response(client, param_values)
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"status": "completed"}

    def test_get_status_response_error_raises(self):
        client = MockAuthenticatedClient()
        client.add_response(
            "GET",
            "/api/status/req_12345",
            {"status": "error"},
            status_code=500,
        )
        polling_request_handler = PollingRequestHandler(
            status_request=PollingStatusRequest(
                method=HTTPMethod.GET,
                path="/api/status/<request_id>",
                status_path="status",
                status_completed_value="completed",
            ),
            result_request=PollingResultRequest(
                method=HTTPMethod.GET,
                path="/api/result/<request_id>",
            ),
        )
        param_values = {
            "request_id": "req_12345",
        }
        with pytest.raises(PrivacyRequestError):
            polling_request_handler.get_status_response(client, param_values)

    def test_get_result_response_success(self):
        client = MockAuthenticatedClient()
        client.add_response(
            "GET",
            "/api/result/req_12345",
            {
                "data": {
                    "results": [
                        {"id": 1, "name": "John Doe", "email": "john@example.com"}
                    ]
                }
            },
            status_code=200,
        )
        polling_request_handler = PollingRequestHandler(
            status_request=PollingStatusRequest(
                method=HTTPMethod.GET,
                path="/api/status/<request_id>",
                status_path="status",
                status_completed_value="completed",
            ),
            result_request=PollingResultRequest(
                method=HTTPMethod.GET,
                path="/api/result/<request_id>",
            ),
        )
        param_values = {
            "request_id": "req_12345",
        }
        response = polling_request_handler.get_result_response(client, param_values)
        assert response.status_code == HTTP_200_OK
        assert response.json() == {
            "data": {
                "results": [{"id": 1, "name": "John Doe", "email": "john@example.com"}]
            }
        }

    def test_get_result_response_error_raises(self):
        client = MockAuthenticatedClient()
        client.add_response(
            "GET",
            "/api/result/req_12345",
            {
                "data": {
                    "results": [
                        {"id": 1, "name": "John Doe", "email": "john@example.com"}
                    ]
                }
            },
            status_code=500,
        )
        polling_request_handler = PollingRequestHandler(
            status_request=PollingStatusRequest(
                method=HTTPMethod.GET,
                path="/api/status/<request_id>",
                status_path="status",
                status_completed_value="completed",
            ),
            result_request=PollingResultRequest(
                method=HTTPMethod.GET,
                path="/api/result/<request_id>",
            ),
        )
        param_values = {
            "request_id": "req_12345",
        }
        with pytest.raises(PrivacyRequestError):
            polling_request_handler.get_result_response(client, param_values)
