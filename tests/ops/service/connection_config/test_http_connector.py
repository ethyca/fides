from collections.abc import Generator

import pytest
import requests_mock
from fidesops.ops.common_exceptions import ClientUnsuccessfulException
from fidesops.ops.service.connectors import HTTPSConnector


class TestHttpConnectorMethods:
    @pytest.fixture(scope="function")
    def connector(self, https_connection_config) -> Generator:
        return HTTPSConnector(configuration=https_connection_config)

    def test_https_connector_build_uri(self, connector, https_connection_config):
        assert connector.build_uri() == https_connection_config.secrets["url"]

    def test_build_authorization_header(self, connector):
        assert connector.build_authorization_header() == {
            "Authorization": "test_authorization"
        }

    def test_execute_response_not_expected(self, connector):
        request_body = {"test": "response"}

        with requests_mock.Mocker() as mock_response:
            mock_response.post(
                connector.build_uri(),
                json={"test": "response"},
                status_code=200,
            )
            assert {} == connector.execute(request_body, response_expected=False)

    def test_execute_response_expected(self, connector):
        request_body = {"test": "response"}

        with requests_mock.Mocker() as mock_response:
            mock_response.post(
                connector.build_uri(),
                json={"test": "response"},
                status_code=200,
            )
            assert {"test": "response"} == connector.execute(
                request_body, response_expected=True
            )

    def test_execute_error(self, connector):
        request_body = {"test": "response"}

        with requests_mock.Mocker() as mock_response:
            mock_response.post(connector.build_uri(), status_code=500, text="Error")

            with pytest.raises(ClientUnsuccessfulException) as exc:
                connector.execute(request_body, response_expected=True)

            assert exc.value.args[0] == "Client call failed with status code '500'"
