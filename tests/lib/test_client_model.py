# pylint: disable=missing-function-docstring
import json
from copy import deepcopy

import pytest

from fides.api.cryptography.cryptographic_util import (
    generate_salt,
    generate_secure_random_string,
    hash_credential_with_salt,
)
from fides.api.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_CONNECTIONS,
    JWE_PAYLOAD_ROLES,
    JWE_PAYLOAD_SCOPES,
    JWE_PAYLOAD_SYSTEMS,
)
from fides.api.models.client import ClientDetail, _get_root_client_detail
from fides.api.oauth.roles import OWNER, VIEWER
from fides.api.oauth.utils import extract_payload
from fides.common.api.scope_registry import DATASET_CREATE_OR_UPDATE, SCOPE_REGISTRY


def test_create_client_and_secret(db, config):
    new_client, secret = ClientDetail.create_client_and_secret(
        db,
        config.security.oauth_client_id_length_bytes,
        config.security.oauth_client_secret_length_bytes,
    )

    assert new_client.hashed_secret is not None
    assert (
        hash_credential_with_salt(
            secret.encode(config.security.encoding),
            new_client.salt.encode(config.security.encoding),
        )
        == new_client.hashed_secret
    )
    assert new_client.scopes == []
    assert new_client.roles == []
    assert new_client.systems == []
    assert new_client.connections == []


def test_create_client_and_secret_no_roles(db, config):
    new_client, secret = ClientDetail.create_client_and_secret(
        db,
        config.security.oauth_client_id_length_bytes,
        config.security.oauth_client_secret_length_bytes,
        scopes=["user:create", "user:read"],
    )

    assert new_client.hashed_secret is not None
    assert (
        hash_credential_with_salt(
            secret.encode(config.security.encoding),
            new_client.salt.encode(config.security.encoding),
        )
        == new_client.hashed_secret
    )
    assert new_client.scopes == ["user:create", "user:read"]
    assert new_client.roles == []
    assert new_client.systems == []
    assert new_client.connections == []


def test_create_client_and_secret_no_scopes(db, config):
    new_client, secret = ClientDetail.create_client_and_secret(
        db,
        config.security.oauth_client_id_length_bytes,
        config.security.oauth_client_secret_length_bytes,
        roles=[VIEWER],
    )

    assert new_client.hashed_secret is not None
    assert (
        hash_credential_with_salt(
            secret.encode(config.security.encoding),
            new_client.salt.encode(config.security.encoding),
        )
        == new_client.hashed_secret
    )
    assert new_client.scopes == []
    assert new_client.roles == [VIEWER]
    assert new_client.systems == []
    assert new_client.connections == []


def test_create_client_and_secret_scopes_and_roles(db, config):
    new_client, secret = ClientDetail.create_client_and_secret(
        db,
        config.security.oauth_client_id_length_bytes,
        config.security.oauth_client_secret_length_bytes,
        roles=[VIEWER],
        scopes=[DATASET_CREATE_OR_UPDATE],
    )

    assert new_client.hashed_secret is not None
    assert (
        hash_credential_with_salt(
            secret.encode(config.security.encoding),
            new_client.salt.encode(config.security.encoding),
        )
        == new_client.hashed_secret
    )
    assert new_client.scopes == [DATASET_CREATE_OR_UPDATE]
    assert new_client.roles == [VIEWER]
    assert new_client.systems == []
    assert new_client.connections == []


def test_create_client_defaults(db):
    client_id = generate_secure_random_string(16)
    secret = generate_secure_random_string(16)

    salt = generate_salt()
    hashed_secret = hash_credential_with_salt(
        secret.encode("UTF-8"),
        salt.encode("UTF-8"),
    )
    client = ClientDetail(
        id=client_id,
        salt=salt,
        hashed_secret=hashed_secret,
    )
    db.add(client)
    db.commit()

    assert client.scopes == []
    assert client.roles == []
    assert client.systems == []
    assert client.connections == []

    client.delete(db)


def test_get_client_with_scopes(db, oauth_client, config):
    client = ClientDetail.get(db, object_id=oauth_client.id, config=config)
    assert client
    assert client.id == oauth_client.id
    assert client.scopes == SCOPE_REGISTRY
    assert client.roles == []
    assert client.systems == []
    assert client.connections == []
    assert oauth_client.hashed_secret == "thisisatest"


def test_get_client_with_roles(db, owner_client, config):
    client = ClientDetail.get(db, object_id=owner_client.id, config=config)
    assert client
    assert client.id == owner_client.id
    assert client.scopes == []
    assert client.roles == [OWNER]
    assert owner_client.hashed_secret == "thisisatest"
    assert client.systems == []
    assert client.connections == []


def test_get_client_with_systems(db, system_manager_client, config, system):
    client = ClientDetail.get(db, object_id=system_manager_client.id, config=config)
    assert client
    assert client.id == system_manager_client.id
    assert client.scopes == []
    assert client.roles == []
    assert client.systems == [system.id]
    assert client.connections == []


def test_get_client_with_connections(
    db, connection_client, config, system, connection_config
):
    client = ClientDetail.get(db, object_id=connection_client.id, config=config)
    assert client
    assert client.id == connection_client.id
    assert client.scopes == []
    assert client.roles == []
    assert client.systems == []
    assert client.connections == [connection_config.id]


def test_get_client_root_client(db, config):
    client = ClientDetail.get(
        db, object_id="fidesadmin", config=config, scopes=SCOPE_REGISTRY, roles=[OWNER]
    )
    assert client
    assert client.id == config.security.oauth_root_client_id
    assert client.scopes == SCOPE_REGISTRY
    assert client.roles == [OWNER]
    assert client.systems == []
    assert client.connections == []


def test_get_root_client_no_scopes(db, config):
    client_detail = ClientDetail.get(db, object_id="fidesadmin", config=config)
    assert client_detail
    assert client_detail.scopes == []
    assert client_detail.roles == []
    assert client_detail.systems == []


def test_credentials_valid(db, config):
    new_client, secret = ClientDetail.create_client_and_secret(
        db,
        config.security.oauth_client_id_length_bytes,
        config.security.oauth_client_secret_length_bytes,
        scopes=SCOPE_REGISTRY,
    )

    assert new_client.credentials_valid("this-is-not-the-right-secret") is False
    assert new_client.credentials_valid(secret) is True
    assert new_client.scopes == SCOPE_REGISTRY
    assert new_client.roles == []
    assert new_client.systems == []
    assert new_client.connections == []


def test_get_root_client_detail_no_root_client_hash(config):
    test_config = deepcopy(config)
    test_config.security.oauth_root_client_secret_hash = None
    with pytest.raises(ValueError):
        _get_root_client_detail(test_config, SCOPE_REGISTRY, [])


def test_client_create_access_code_jwe(oauth_client, config):
    jwe = oauth_client.create_access_code_jwe(config.security.app_encryption_key)

    token_data = json.loads(extract_payload(jwe, config.security.app_encryption_key))

    assert token_data[JWE_PAYLOAD_CLIENT_ID] == oauth_client.id
    assert token_data[JWE_PAYLOAD_SCOPES] == oauth_client.scopes
    assert token_data[JWE_ISSUED_AT] is not None
    assert token_data[JWE_PAYLOAD_ROLES] == []
    assert token_data[JWE_PAYLOAD_SYSTEMS] == []
    assert token_data[JWE_PAYLOAD_CONNECTIONS] == []


def test_client_create_access_code_jwe_owner_client(owner_client, config):
    jwe = owner_client.create_access_code_jwe(config.security.app_encryption_key)

    token_data = json.loads(extract_payload(jwe, config.security.app_encryption_key))

    assert token_data[JWE_PAYLOAD_CLIENT_ID] == owner_client.id
    assert token_data[JWE_PAYLOAD_SCOPES] == []
    assert token_data[JWE_ISSUED_AT] is not None
    assert token_data[JWE_PAYLOAD_ROLES] == [OWNER]
    assert token_data[JWE_PAYLOAD_SYSTEMS] == []
    assert token_data[JWE_PAYLOAD_CONNECTIONS] == []


def test_client_create_access_code_jwe_viewer_client(viewer_client, config):
    jwe = viewer_client.create_access_code_jwe(config.security.app_encryption_key)

    token_data = json.loads(extract_payload(jwe, config.security.app_encryption_key))

    assert token_data[JWE_PAYLOAD_CLIENT_ID] == viewer_client.id
    assert token_data[JWE_PAYLOAD_SCOPES] == []
    assert token_data[JWE_ISSUED_AT] is not None
    assert token_data[JWE_PAYLOAD_ROLES] == [VIEWER]
    assert token_data[JWE_PAYLOAD_SYSTEMS] == []
    assert token_data[JWE_PAYLOAD_CONNECTIONS] == []


def test_client_create_access_code_with_systems(system_manager_client, config, system):
    jwe = system_manager_client.create_access_code_jwe(
        config.security.app_encryption_key
    )

    token_data = json.loads(extract_payload(jwe, config.security.app_encryption_key))

    assert token_data[JWE_PAYLOAD_CLIENT_ID] == system_manager_client.id
    assert token_data[JWE_PAYLOAD_SCOPES] == []
    assert token_data[JWE_ISSUED_AT] is not None
    assert token_data[JWE_PAYLOAD_ROLES] == []
    assert token_data[JWE_PAYLOAD_SYSTEMS] == [system.id]
    assert token_data[JWE_PAYLOAD_CONNECTIONS] == []


def test_client_create_access_code_with_connections(
    connection_client, config, connection_config
):
    jwe = connection_client.create_access_code_jwe(config.security.app_encryption_key)

    token_data = json.loads(extract_payload(jwe, config.security.app_encryption_key))

    assert token_data[JWE_PAYLOAD_CLIENT_ID] == connection_client.id
    assert token_data[JWE_PAYLOAD_SCOPES] == []
    assert token_data[JWE_ISSUED_AT] is not None
    assert token_data[JWE_PAYLOAD_ROLES] == []
    assert token_data[JWE_PAYLOAD_SYSTEMS] == []
    assert token_data[JWE_PAYLOAD_CONNECTIONS] == [connection_config.id]
