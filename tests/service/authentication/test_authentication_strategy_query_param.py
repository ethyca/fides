import pytest
from requests import PreparedRequest, Request

from fidesops.common_exceptions import ValidationError as FidesopsValidationError
from fidesops.models.connectionconfig import ConnectionConfig
from fidesops.service.authentication.authentication_strategy_factory import get_strategy


def test_query_param_auth():
    req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

    name = "account"
    api_key = "imakeyblademaster"
    secrets = {"api_key": api_key}

    authenticated_request = get_strategy(
        "query_param", {"name": "account", "value": "<api_key>"}
    ).add_authentication(req, ConnectionConfig(secrets=secrets))
    assert authenticated_request.url == f"https://localhost/?{name}={api_key}"


def test_query_param_auth_without_config():
    req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

    with pytest.raises(FidesopsValidationError):
        get_strategy("query_param", {}).add_authentication(
            req, ConnectionConfig(secrets={})
        )
