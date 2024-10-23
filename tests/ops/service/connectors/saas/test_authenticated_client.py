import threading
import time
import unittest.mock as mock
from email.utils import formatdate
from typing import Any, Dict, Generator

import pytest
from loguru import logger
from requests import ConnectionError, Response, Session
from werkzeug.serving import make_server
from werkzeug.wrappers import Response as WerkzeugResponse

from fides.api.common_exceptions import ClientUnsuccessfulException, ConnectionException
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.schemas.saas.saas_config import ClientConfig
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import (
    AuthenticatedClient,
    get_retry_after,
)
from fides.api.util.saas_util import load_config_with_replacement


@pytest.mark.skip(reason="move to plus in progress")
@pytest.fixture
def test_saas_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/segment_config.yml",
        "<instance_fides_key>",
        "test_config",
    )


@pytest.mark.skip(reason="move to plus in progress")
@pytest.fixture
def test_connection_config(test_saas_config) -> ConnectionConfig:
    return ConnectionConfig(
        key="test_config",
        connection_type=ConnectionType.saas,
        saas_config=test_saas_config,
        secrets={"access_token": "test_token"},
    )


@pytest.mark.skip(reason="move to plus in progress")
@pytest.fixture
def test_saas_request() -> SaaSRequestParams:
    return SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/test_path",
        query_params={},
    )


@pytest.mark.skip(reason="move to plus in progress")
@pytest.fixture
def test_client_config() -> ClientConfig:
    return ClientConfig(protocol="https", host="test_host")


@pytest.mark.skip(reason="move to plus in progress")
@pytest.fixture
def test_authenticated_client(
    test_connection_config, test_client_config
) -> AuthenticatedClient:
    return AuthenticatedClient(
        "https://ethyca.com", test_connection_config, test_client_config
    )


@pytest.mark.skip(reason="move to plus in progress")
@pytest.fixture
def test_http_server() -> Generator[str, None, None]:
    """
    Creates a simple HTTP server for testing purposes.

    This fixture sets up a Werkzeug server running on localhost with a
    dynamically assigned port. The server responds to all requests with
    a "Request received" message.

    The server is automatically shut down after the test is complete.
    """

    def simple_app(environ, start_response):
        logger.info("Request received")
        response = WerkzeugResponse("Request received")
        return response(environ, start_response)

    server = make_server("localhost", 0, simple_app)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    yield f"http://{server.server_address[0]}:{server.server_address[1]}"

    server.shutdown()
    server_thread.join()


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.unit_saas
class TestAuthenticatedClient:
    @mock.patch.object(Session, "send")
    def test_client_returns_ok_response(
        self,
        send,
        test_authenticated_client,
        test_saas_request,
        test_config_dev_mode_disabled,
    ):
        test_response = Response()
        test_response.status_code = 200
        send.return_value = test_response
        returned_response = test_authenticated_client.send(test_saas_request)
        assert returned_response == test_response

    @pytest.mark.parametrize(
        "ip_address", ["localhost", "127.0.0.1", "169.254.0.1", "169.254.169.254"]
    )
    def test_client_denied_url(
        self,
        test_authenticated_client: AuthenticatedClient,
        test_saas_request,
        test_config_dev_mode_disabled,
        ip_address,
    ):
        test_authenticated_client.uri = f"https://{ip_address}"
        with pytest.raises(ConnectionException):
            test_authenticated_client.send(test_saas_request)

    @mock.patch.object(Session, "send")
    def test_client_retries_429_and_throws(
        self, send, test_authenticated_client, test_saas_request
    ):
        test_response = Response()
        test_response.status_code = 429
        send.return_value = test_response
        with pytest.raises(ClientUnsuccessfulException):
            test_authenticated_client.send(test_saas_request)
        assert send.call_count == 4

    @mock.patch.object(Session, "send")
    def test_client_retries_429_with_success(
        self, send, test_authenticated_client, test_saas_request
    ):
        test_response_1 = Response()
        test_response_1.status_code = 429
        test_response_2 = Response()
        test_response_2.status_code = 200
        send.side_effect = [test_response_1, test_response_2]
        returned_response = test_authenticated_client.send(test_saas_request)
        returned_response == test_response_2
        assert send.call_count == 2

    @mock.patch.object(Session, "send")
    def test_client_does_not_retry_connection_error(
        self, send, test_authenticated_client, test_saas_request
    ):
        test_side_effect_1 = ConnectionError()
        send.side_effect = [test_side_effect_1]
        with pytest.raises(ConnectionException):
            test_authenticated_client.send(test_saas_request)
        assert send.call_count == 1

    def test_client_ignores_errors(
        self,
        test_authenticated_client,
    ):
        """Test that _should_ignore_errors ignores the correct errors."""
        assert test_authenticated_client._should_ignore_error(
            status_code=400,
            errors_to_ignore=True,
        )
        assert not test_authenticated_client._should_ignore_error(
            status_code=400,
            errors_to_ignore=False,
        )
        assert test_authenticated_client._should_ignore_error(
            status_code=400,
            errors_to_ignore=[400],
        )
        assert not test_authenticated_client._should_ignore_error(
            status_code=400,
            errors_to_ignore=[401],
        )

    def test_sending_special_characters(
        self, test_authenticated_client, test_http_server
    ):
        request_params = SaaSRequestParams(
            method=HTTPMethod.POST,
            path="/",
            body='{"addr": "1234 Peterson’s Farm Rd."}',
            headers={"Content-Type": "application/json"},
        )

        test_authenticated_client.uri = test_http_server
        test_authenticated_client.send(request_params)


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.unit_saas
class TestRetryAfterHeaderParsing:
    def test_retry_after_parses_seconds_response(self):
        test_response = Response()
        test_response.status_code = 429
        test_response.headers = {"Retry-After": "30"}
        retry_after_sleep = get_retry_after(test_response)
        assert retry_after_sleep == 30

    def test_retry_after_parses_timestamp_in_future(self):
        test_response = Response()
        test_response.status_code = 429
        time_in_future = time.time() + 30
        test_response.headers = {"Retry-After": formatdate(timeval=time_in_future)}
        retry_after_sleep = get_retry_after(test_response)
        assert retry_after_sleep > 20

    def test_retry_after_parses_timestamp_in_past(self):
        test_response = Response()
        test_response.status_code = 429
        time_in_past = time.time() - 30
        test_response.headers = {"Retry-After": formatdate(timeval=time_in_past)}
        retry_after_sleep = get_retry_after(test_response)
        assert retry_after_sleep == 0
