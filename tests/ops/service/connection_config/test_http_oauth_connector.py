from collections.abc import Generator

import pytest
import requests_mock
from requests import Request

from fides.api.common_exceptions import ClientUnsuccessfulException
from fides.api.service.connectors import HTTPSConnector


class TestHttpOAuth2ConnectorMethods:
    @pytest.fixture(scope="function")
    def connector(self, https_connection_config_with_oauth) -> Generator:
        return HTTPSConnector(configuration=https_connection_config_with_oauth)

    def test_https_connector_build_uri(
        self, connector, https_connection_config_with_oauth
    ):
        assert (
            connector.build_uri() == https_connection_config_with_oauth.secrets["url"]
        )

    @pytest.mark.parametrize(
        "response_expected, response_data",
        [(False, {}), (True, {"test": "response"})],
        ids=["no_response", "response"],
    )
    def test_execute_request(self, response_expected, response_data, connector):
        request_body = {"test": "response"}

        # Validate that the connector uses the Bearer token in the request to the endpoint
        def request_contains_oauth_bearer_token(request):
            assert request.headers["Authorization"] == f"Bearer test_token"
            return True

        # Validate that the connector uses the OAuth2 token URL to fetch a token
        def request_contains_oauth_token_request(request: Request):
            assert "Basic " in request.headers["Authorization"]
            assert "Content-Type" in request.headers
            assert (
                request.headers["Content-Type"] == "application/x-www-form-urlencoded"
            )
            return True

        with requests_mock.Mocker() as mock_response:

            mock_response.post(
                connector.configuration.oauth_config.token_url,
                json={"access_token": "test_token", "token_type": "Bearer"},
                status_code=200,
                headers={"Content-Type": "application/json"},
                additional_matcher=request_contains_oauth_token_request,
            )

            mock_response.post(
                connector.build_uri(),
                json={"test": "response"},
                status_code=200,
                additional_matcher=request_contains_oauth_bearer_token,
            )

            assert response_data == connector.execute(
                request_body, response_expected=response_expected
            )

    def test_execute_error(self, connector):
        request_body = {"test": "response"}

        with requests_mock.Mocker() as mock_response:
            mock_response.post(connector.build_uri(), status_code=500, text="Error")

            with pytest.raises(ClientUnsuccessfulException) as exc:
                connector.execute(request_body, response_expected=True)

            assert exc.value.args[0] == "Client call failed with status code '500'"
