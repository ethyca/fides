# pylint: disable=duplicate-code, missing-function-docstring, redefined-outer-name

import json
from datetime import datetime

import pytest
from fastapi.security import SecurityScopes

from fides.api.ops.util.oauth_util import verify_oauth_client
from fides.lib.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fides.lib.exceptions import AuthorizationError
from fides.lib.oauth.jwt import generate_jwe
from fides.lib.oauth.oauth_util import (
    extract_payload,
    is_token_expired,
)
from fides.lib.oauth.scopes import USER_DELETE, USER_READ


@pytest.fixture
def encryption_key():
    yield "d9a74e98829dbf57c4ca36e1788a48d2"


def test_jwe_create_and_extract(encryption_key) -> None:
    payload = {"hello": "hi there"}
    jwe_string = generate_jwe(json.dumps(payload), encryption_key)
    payload_from_svc = json.loads(extract_payload(jwe_string, encryption_key))
    assert payload_from_svc["hello"] == payload["hello"]


@pytest.mark.parametrize(
    "issued_at, token_duration_min, expected",
    [
        (datetime(2020, 1, 1), 1, True),
        (datetime.now(), 60, False),
        (None, 60, True),
    ],
)
def test_is_token_expired(issued_at, token_duration_min, expected):
    assert is_token_expired(issued_at, token_duration_min) is expected


async def test_verify_oauth_malformed_oauth_client(db, config):
    with pytest.raises(AuthorizationError):
        await verify_oauth_client(
            SecurityScopes([USER_READ]),
            authorization="invalid",
            db=db,
        )


async def test_verify_oauth_client_no_issued_at(db, config, user):
    payload = {
        JWE_PAYLOAD_SCOPES: [USER_READ],
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: None,
        "token_duration_min": 1,
    }
    token = generate_jwe(
        json.dumps(payload),
        config.security.app_encryption_key,
    )
    with pytest.raises(AuthorizationError):
        await verify_oauth_client(
            SecurityScopes([USER_READ]),
            token,
            db=db,
        )


async def test_verify_oauth_client_expired(db, config, user):
    scope = [USER_READ]
    payload = {
        JWE_PAYLOAD_SCOPES: scope,
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime(2020, 1, 1).isoformat(),
        "token_duration_min": 1,
    }
    token = generate_jwe(
        json.dumps(payload),
        config.security.app_encryption_key,
    )
    with pytest.raises(AuthorizationError):
        await verify_oauth_client(
            SecurityScopes(scope),
            token,
            db=db,
        )


async def test_verify_oauth_client_no_client_id(db, config):
    scope = [USER_READ]
    payload = {
        JWE_PAYLOAD_SCOPES: scope,
        JWE_PAYLOAD_CLIENT_ID: None,
        JWE_ISSUED_AT: datetime.now().isoformat(),
        "token_duration_min": 60,
    }
    token = generate_jwe(
        json.dumps(payload),
        config.security.app_encryption_key,
    )
    with pytest.raises(AuthorizationError):
        await verify_oauth_client(
            SecurityScopes(scope),
            token,
            db=db,
        )


async def test_verify_oauth_client_no_client(db, config, user):
    scopes = [USER_READ]
    payload = {
        JWE_PAYLOAD_SCOPES: scopes,
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
        "token_duration_min": 60,
    }
    token = generate_jwe(
        json.dumps(payload),
        config.security.app_encryption_key,
    )
    user.client.delete(db)
    assert user.client is None
    with pytest.raises(AuthorizationError):
        await verify_oauth_client(
            SecurityScopes(scopes),
            token,
            db=db,
        )


async def test_verify_oauth_client_wrong_security_scope(db, config, user):
    payload = {
        JWE_PAYLOAD_SCOPES: [USER_DELETE],
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
        "token_duration_min": 60,
    }
    token = generate_jwe(
        json.dumps(payload),
        config.security.app_encryption_key,
    )
    with pytest.raises(AuthorizationError):
        await verify_oauth_client(
            SecurityScopes([USER_READ]),
            token,
            db=db,
        )


async def test_verify_oauth_client_wrong_client_scope(db, config, user):
    scopes = [USER_READ]
    payload = {
        JWE_PAYLOAD_SCOPES: scopes,
        JWE_PAYLOAD_CLIENT_ID: user.client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
        "token_duration_min": 60,
    }
    token = generate_jwe(
        json.dumps(payload),
        config.security.app_encryption_key,
    )
    user.client.scopes = [USER_DELETE]
    with pytest.raises(AuthorizationError):
        await verify_oauth_client(
            SecurityScopes(scopes),
            token,
            db=db,
        )
