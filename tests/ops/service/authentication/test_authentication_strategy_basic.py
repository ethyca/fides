import pytest
from requests import PreparedRequest, Request

from fides.api.ops.common_exceptions import ValidationError as FidesopsValidationError
from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.ops.cryptography.cryptographic_util import bytes_to_b64_str


def test_basic_auth_with_username_and_password():
    req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

    username = "admin"
    password = "sufficientlylongpassword"
    secrets = {"username": username, "password": password}

    authenticated_request = AuthenticationStrategy.get_strategy(
        "basic", {"username": "<username>", "password": "<password>"}
    ).add_authentication(req, ConnectionConfig(secrets=secrets))
    assert (
        authenticated_request.headers["Authorization"]
        == f"Basic {bytes_to_b64_str(bytes(f'{username}:{password}', 'UTF-8'))}"
    )


def test_basic_auth_with_username_only():
    req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

    username = "admin"
    secrets = {"username": username}

    authenticated_request = AuthenticationStrategy.get_strategy(
        "basic", {"username": "<username>"}
    ).add_authentication(req, ConnectionConfig(secrets=secrets))
    # The requests library still calls str(password) even if the password is None
    assert (
        authenticated_request.headers["Authorization"]
        == f"Basic {bytes_to_b64_str(bytes(f'{username}:None', 'UTF-8'))}"
    )


def test_basic_auth_with_no_credentials():
    req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

    with pytest.raises(FidesopsValidationError):
        AuthenticationStrategy.get_strategy("basic", {}).add_authentication(
            req, ConnectionConfig(secrets={})
        )
