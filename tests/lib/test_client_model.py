# pylint: disable=missing-function-docstring

from copy import deepcopy

import pytest

from fides.lib.cryptography.cryptographic_util import hash_with_salt
from fides.lib.models.client import ClientDetail, _get_root_client_detail
from fides.api.ops.api.v1.scope_registry import SCOPE_REGISTRY as SCOPES


def test_create_client_and_secret(db, config):
    new_client, secret = ClientDetail.create_client_and_secret(
        db,
        config.security.oauth_client_id_length_bytes,
        config.security.oauth_client_secret_length_bytes,
    )

    assert new_client.hashed_secret is not None
    assert (
        hash_with_salt(
            secret.encode(config.security.encoding),
            new_client.salt.encode(config.security.encoding),
        )
        == new_client.hashed_secret
    )


def test_get_client(db, oauth_client, config):
    client = ClientDetail.get(db, object_id=oauth_client.id, config=config)
    assert client
    assert client.id == oauth_client.id
    assert client.scopes == SCOPES
    assert oauth_client.hashed_secret == "thisisatest"


def test_get_client_root_client(db, config):
    client = ClientDetail.get(
        db,
        object_id="fidesadmin",
        config=config,
        scopes=SCOPES,
    )
    assert client
    assert client.id == config.security.oauth_root_client_id
    assert client.scopes == SCOPES


def test_get_client_root_client_no_scopes(db, config):
    client_detail = ClientDetail.get(db, object_id="fidesadmin", config=config)
    assert client_detail
    assert client_detail.scopes is None


def test_credentials_valid(db, config):
    new_client, secret = ClientDetail.create_client_and_secret(
        db,
        config.security.oauth_client_id_length_bytes,
        config.security.oauth_client_secret_length_bytes,
        scopes=SCOPES,
    )

    assert new_client.credentials_valid("this-is-not-the-right-secret") is False
    assert new_client.credentials_valid(secret) is True


def test_get_root_client_detail_no_root_client_hash(config):
    test_config = deepcopy(config)
    test_config.security.oauth_root_client_secret_hash = None
    with pytest.raises(ValueError):
        _get_root_client_detail(test_config, SCOPES)
