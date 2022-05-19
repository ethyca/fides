import json
from datetime import datetime
from unittest import mock
from unittest.mock import Mock

from fidesops.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fidesops.util.oauth_util import extract_payload, generate_jwe, is_token_expired


def test_jwe_create_and_extract() -> None:
    payload = {"hello": "hi there"}
    jwt_string = generate_jwe(json.dumps(payload))
    payload_from_svc = json.loads(extract_payload(jwt_string))
    assert payload_from_svc["hello"] == payload["hello"]


def test_token_expired(oauth_client):
    payload = {
        JWE_PAYLOAD_CLIENT_ID: oauth_client.id,
        JWE_PAYLOAD_SCOPES: oauth_client.scopes,
        JWE_ISSUED_AT: datetime(2020, 1, 1).isoformat(),
    }

    # Create a token with a very old issued at date.
    access_token = generate_jwe(json.dumps(payload))

    extracted = json.loads(extract_payload(access_token))
    assert extracted[JWE_PAYLOAD_CLIENT_ID] == oauth_client.id
    issued_at = datetime.fromisoformat(extracted[JWE_ISSUED_AT])
    assert issued_at == datetime(2020, 1, 1)
    assert extracted[JWE_PAYLOAD_SCOPES] == oauth_client.scopes
    assert is_token_expired(issued_at) is True

    # Create a token now
    access_token = oauth_client.create_access_code_jwe()
    extracted = json.loads(extract_payload(access_token))
    assert is_token_expired(datetime.fromisoformat(extracted[JWE_ISSUED_AT])) is False
