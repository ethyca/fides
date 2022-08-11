from fideslib.cryptography.cryptographic_util import hash_with_salt
from fideslib.models.client import ClientDetail
from sqlalchemy.orm import Session

from fidesops.ops.api.v1.scope_registry import SCOPE_REGISTRY
from fidesops.ops.core.config import config


class TestClientModel:
    def test_create_client_and_secret(self, db: Session) -> None:
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

    def test_get_client(self, db: Session, oauth_client) -> None:
        client = ClientDetail.get(
            db,
            object_id=config.security.oauth_root_client_id,
            config=config,
            scopes=SCOPE_REGISTRY,
        )

        hashed_access_key = hash_with_salt(
            config.security.oauth_root_client_secret.encode(config.security.encoding),
            client.salt.encode(config.security.encoding),
        )

        assert "fidesopsadmin" == client.id
        assert client.scopes == SCOPE_REGISTRY
        assert client.hashed_secret == hashed_access_key

        client = ClientDetail.get(db, object_id=oauth_client.id, config=config)
        assert oauth_client.id == client.id
        assert oauth_client.hashed_secret == "thisisatest"

    def test_credentials_valid(self, db: Session) -> None:
        new_client, secret = ClientDetail.create_client_and_secret(
            db,
            config.security.oauth_client_id_length_bytes,
            config.security.oauth_client_secret_length_bytes,
        )

        assert new_client.credentials_valid("this-is-not-the-right-secret") is False
        assert new_client.credentials_valid(secret) is True

        new_client.delete(db)
