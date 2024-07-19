# pylint: disable=missing-docstring, redefined-outer-name
import json
from datetime import datetime
from typing import List

import pytest
from fastapi_pagination import Params

from fides.api.cryptography.cryptographic_util import str_to_b64_str
from fides.api.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fides.api.models.client import ClientDetail
from fides.api.models.fides_user import FidesUser
from fides.api.oauth.jwt import generate_jwe
from fides.common.api.scope_registry import USER_CREATE
from fides.config import CONFIG

page_size = Params().size

import json
from typing import Any, Dict, Generator

import pytest

from fides.api import middleware as _middleware
from fides.api.cryptography.cryptographic_util import str_to_b64_str
from fides.api.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fides.api.oauth.jwt import generate_jwe
from fides.common.api.scope_registry import USER_CREATE
from fides.config import CONFIG

# from sqlalchemy.exc import SQLAlchemyError


@pytest.fixture
def test_audit_log_resource_data() -> Generator:
    """
    Returns a well-formed dictionary of test data
    """
    audit_log_resource_data = {
        "user_id": "test_user_id",
        "request_path": "some/path",
        "request_type": "POST",
        "fides_keys": ["new_fides_key"],
        "extra_data": {"key": "value"},
    }
    yield audit_log_resource_data


@pytest.fixture
def test_bad_audit_log_resource_data() -> Generator:
    """
    Returns a well-formed dictionary of test data
    """
    audit_log_resource_data = {
        "user_id": None,
        "request_path": "some/path",
        "request_type": "POST",
        "fides_keys": ["new_fides_key"],
    }
    yield audit_log_resource_data


def test_record_written_to_db(db, test_audit_log_resource_data: Dict[str, Any]) -> None:
    assert _middleware.write_audit_log_resource_record(db, test_audit_log_resource_data)


async def test_extracted_token(db) -> None:
    # This was taken from test_user_endpoints.py
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_token_user",
            "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
        },
    )

    client, _ = ClientDetail.create_client_and_secret(
        db,
        CONFIG.security.oauth_client_id_length_bytes,
        CONFIG.security.oauth_client_secret_length_bytes,
        scopes=[USER_CREATE],
        user_id=user.id,
    )
    payload = {
        JWE_PAYLOAD_SCOPES: [USER_CREATE],
        JWE_PAYLOAD_CLIENT_ID: client.id,
        JWE_ISSUED_AT: datetime.now().isoformat(),
    }

    jwe = generate_jwe(json.dumps(payload), CONFIG.security.app_encryption_key)
    auth_header = {"Authorization": "Bearer " + jwe}
    assert client.user_id == await _middleware.get_client_user_id(
        db, auth_header["Authorization"]
    )


@pytest.mark.parametrize(
    "request_body, expected_fides_keys",
    [
        (
            b'{"fides_key": "test_key"}',
            ["test_key"],
        ),
        (
            b'{"name": "test_name"}',
            [],
        ),
        (
            b'[{"fides_key": "test_key"}, {"fides_key": "test_key_2"}]',
            ["test_key", "test_key_2"],
        ),
    ],
)
async def test_extract_data_from_body(
    request_body: bytes, expected_fides_keys: List
) -> None:
    fides_keys = await _middleware.extract_data_from_body(request_body)
    assert fides_keys == expected_fides_keys
