import json

import pytest
from requests import PreparedRequest, Request

from fides.api.common_exceptions import FidesopsException
from fides.api.common_exceptions import ValidationError as FidesopsValidationError
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)


def test_api_key_auth_header():
    req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

    name = "token"
    api_key = "imakeyblademaster"
    secrets = {"api_key": api_key}

    authenticated_request = AuthenticationStrategy.get_strategy(
        "api_key", {"headers": [{"name": name, "value": "<api_key>"}]}
    ).add_authentication(req, ConnectionConfig(secrets=secrets))
    assert (name, api_key) in authenticated_request.headers.items()

    # mimic scenario having multiple keys to pass
    name_2 = "secret_token"
    secret_key = "imasecretkeyblademaster"
    secrets = {"api_key": api_key, "secret_key": secret_key}

    authenticated_request = AuthenticationStrategy.get_strategy(
        "api_key",
        {
            "headers": [
                {"name": name, "value": "<api_key>"},
                {"name": name_2, "value": "<secret_key>"},
            ]
        },
    ).add_authentication(req, ConnectionConfig(secrets=secrets))
    assert (name, api_key) in authenticated_request.headers.items()
    assert (name_2, secret_key) in authenticated_request.headers.items()


def test_api_key_auth_query_param():
    req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

    name = "token"
    api_key = "imakeyblademaster"
    secrets = {"api_key": api_key}

    authenticated_request = AuthenticationStrategy.get_strategy(
        "api_key", {"query_params": [{"name": name, "value": "<api_key>"}]}
    ).add_authentication(req, ConnectionConfig(secrets=secrets))
    assert authenticated_request.url == f"https://localhost/?{name}={api_key}"

    # mimic scenario having multiple keys to pass
    name_2 = "secret_token"
    secret_key = "imasecretkeyblademaster"
    secrets = {"api_key": api_key, "secret_key": secret_key}

    authenticated_request = AuthenticationStrategy.get_strategy(
        "api_key",
        {
            "query_params": [
                {"name": name, "value": "<api_key>"},
                {"name": name_2, "value": "<secret_key>"},
            ]
        },
    ).add_authentication(req, ConnectionConfig(secrets=secrets))
    assert (
        authenticated_request.url
        == f"https://localhost/?{name}={api_key}&{name_2}={secret_key}"
    )

    # mimic scenario with already existing query param in the request
    req: PreparedRequest = Request(
        method="POST", url="https://localhost?another_query_param=another_param_value"
    ).prepare()
    authenticated_request = AuthenticationStrategy.get_strategy(
        "api_key", {"query_params": [{"name": name, "value": "<api_key>"}]}
    ).add_authentication(req, ConnectionConfig(secrets=secrets))
    assert (
        authenticated_request.url
        == f"https://localhost/?another_query_param=another_param_value&{name}={api_key}"
    )


def test_api_key_auth_body():
    req: PreparedRequest = Request(
        method="POST", url="https://localhost.com", json={"opt_out": True}
    ).prepare()

    api_key = "imakeyblademaster"
    secrets = {"api_key": api_key}

    authenticated_request = AuthenticationStrategy.get_strategy(
        "api_key", {"body": '{\n  "key": "<api_key>"\n}\n'}
    ).add_authentication(req, ConnectionConfig(secrets=secrets))
    assert authenticated_request.url == f"https://localhost.com/"

    assert json.loads(authenticated_request.body) == {
        "opt_out": True,
        "key": "imakeyblademaster",
    }


def test_api_key_auth_header_and_query_param():
    req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

    name = "token"
    api_key = "imakeyblademaster"
    secrets = {"api_key": api_key}

    authenticated_request = AuthenticationStrategy.get_strategy(
        "api_key",
        {
            "query_params": [{"name": name, "value": "<api_key>"}],
            "headers": [{"name": name, "value": "<api_key>"}],
        },
    ).add_authentication(req, ConnectionConfig(secrets=secrets))
    assert authenticated_request.url == f"https://localhost/?{name}={api_key}"
    assert (name, api_key) in authenticated_request.headers.items()

    # mimic scenario having multiple keys to pass
    name_2 = "secret_token"
    secret_key = "imasecretkeyblademaster"
    secrets = {"api_key": api_key, "secret_key": secret_key}

    authenticated_request = AuthenticationStrategy.get_strategy(
        "api_key",
        {
            "headers": [
                {"name": name, "value": "<api_key>"},
                {"name": name_2, "value": "<secret_key>"},
            ],
            "query_params": [
                {"name": name, "value": "<api_key>"},
            ],
        },
    ).add_authentication(req, ConnectionConfig(secrets=secrets))
    assert (name, api_key) in authenticated_request.headers.items()
    assert (name_2, secret_key) in authenticated_request.headers.items()
    assert authenticated_request.url == f"https://localhost/?{name}={api_key}"


def test_api_key_auth_bad_config():
    req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

    with pytest.raises(FidesopsValidationError) as exc:
        AuthenticationStrategy.get_strategy("api_key", {}).add_authentication(
            req, ConnectionConfig(secrets={})
        )
    assert (
        "At least one 'header', 'query_param', or 'body' object must be defined in an 'api_key' auth configuration"
        in str(exc.value)
    )

    with pytest.raises(FidesopsValidationError) as exc:
        AuthenticationStrategy.get_strategy(
            "api_key", {"headers": []}
        ).add_authentication(req, ConnectionConfig(secrets={}))
    assert (
        "At least one 'header', 'query_param', or 'body' object must be defined in an 'api_key' auth configuration"
        in str(exc.value)
    )

    with pytest.raises(FidesopsValidationError) as exc:
        AuthenticationStrategy.get_strategy(
            "api_key", {"headers": ""}
        ).add_authentication(req, ConnectionConfig(secrets={}))
    assert (
        "At least one 'header', 'query_param', or 'body' object must be defined in an 'api_key' auth configuration"
        in str(exc.value)
    )

    with pytest.raises(FidesopsValidationError) as exc:
        AuthenticationStrategy.get_strategy(
            "api_key", {"headers": "foo"}
        ).add_authentication(req, ConnectionConfig(secrets={}))
    assert "Input should be a valid list" in str(exc.value)

    with pytest.raises(FidesopsValidationError) as exc:
        AuthenticationStrategy.get_strategy(
            "api_key", {"headers": ["foo"]}
        ).add_authentication(req, ConnectionConfig(secrets={}))
    assert "Input should be a valid dictionary or instance of Header" in str(exc.value)

    with pytest.raises(FidesopsValidationError) as exc:
        AuthenticationStrategy.get_strategy(
            "api_key", {"headers": {"name": "token"}}
        ).add_authentication(req, ConnectionConfig())
    assert "Input should be a valid list" in str(exc.value)

    with pytest.raises(FidesopsValidationError) as exc:
        AuthenticationStrategy.get_strategy(
            "api_key", {"headers": [{"name": "token"}]}
        ).add_authentication(req, ConnectionConfig())
        assert "Field required" in str(exc.value)

    with pytest.raises(FidesopsValidationError) as exc:
        AuthenticationStrategy.get_strategy(
            "api_key", {"headers": [{"value": "<api_key>"}]}
        ).add_authentication(req, ConnectionConfig(secrets={}))
    assert "Field required" in str(exc.value)

    with pytest.raises(FidesopsValidationError) as exc:
        AuthenticationStrategy.get_strategy(
            "api_key",
            {
                "headers": [
                    {"name": "token", "value": "<api_key>"},
                    {"value": "<api_key>"},
                ]
            },
        ).add_authentication(req, ConnectionConfig(secrets={}))
    assert "Field required" in str(exc.value)

    with pytest.raises(FidesopsValidationError) as exc:
        AuthenticationStrategy.get_strategy(
            "api_key",
            {
                "headers": {"name": "token", "value": "<api_key>"},
                "query_params": {"name": "token"},
            },
        ).add_authentication(req, ConnectionConfig(secrets={}))
    assert "Input should be a valid list" in str(exc.value)


def test_api_key_auth_bad_param_value():
    req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

    name = "token"
    api_key = "imakeyblademaster"
    secrets = {"api_key": api_key}

    with pytest.raises(FidesopsException) as exc:
        AuthenticationStrategy.get_strategy(
            "api_key", {"query_params": [{"name": name, "value": "<not_api_key>"}]}
        ).add_authentication(req, ConnectionConfig(secrets=secrets))
        assert "Value for API key param '<not_api_key>' not found" == str(exc.value)
