from collections.abc import Generator

import pytest
import requests_mock
from attr import dataclass

from fides.api.common_exceptions import ClientUnsuccessfulException
from fides.api.service.connectors import HTTPSConnector


@dataclass
class HeaderTestCase:
    name: str
    secret: dict[str, str] | None = {}
    additional: dict[str, str] = {}
    expected: dict[str, str] = {}


def name_of_test(test_case):
    if isinstance(test_case, HeaderTestCase):
        return test_case.name


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

    user_agent_header: dict[str, str] = {"User-Agent": "fides"}
    forwards_secret_headers = HeaderTestCase(
        "Forwards headers in stored in secret",
        secret=user_agent_header,
        expected=user_agent_header,
    )

    forwards_additional_headers = HeaderTestCase(
        "Forwards headers in additional_headers param",
        additional=user_agent_header,
        expected=user_agent_header,
    )

    merges_header_sets_additional_override_existing = HeaderTestCase(
        "Overwrites headers in secrets with additional_headers param",
        additional=user_agent_header | {"override": "value2"},
        secret={"override": "value1"},
        expected=user_agent_header | {"override": "value2"},
    )

    handles_none_secret_headers = HeaderTestCase(
        "None header secrets succeeds", additional={}, secret=None, expected={}
    )

    @pytest.mark.parametrize(
        "test_case",
        [
            forwards_secret_headers,
            forwards_additional_headers,
            merges_header_sets_additional_override_existing,
            handles_none_secret_headers,
        ],
        ids=name_of_test,
    )
    def test_expected_header_secrets(
        self, https_connection_config, test_case: HeaderTestCase
    ):
        https_connection_config.secrets["headers"] = test_case.secret
        connector: HTTPSConnector = HTTPSConnector(https_connection_config)
        with requests_mock.Mocker() as mock_response:
            mock_response.register_uri(
                "POST",
                connector.build_uri(),
                json={"property": "value"},
                request_headers=test_case.expected,
            )

            assert {"property": "value"} == connector.execute(
                {"property": "value"},
                response_expected=True,
                additional_headers=test_case.additional,
            )
