from sqlalchemy.orm import Session

from fidesops.api.v1.scope_registry import SCOPE_REGISTRY
from fidesops.core.config import config
from fidesops.models.client import ClientDetail
from fidesops.util.cryptographic_util import hash_with_salt


class TestClientModel:
    def test_create_client_and_secret(self, db: Session) -> None:
        new_client, secret = ClientDetail.create_client_and_secret(db)

        assert new_client.hashed_secret is not None
        assert (
            hash_with_salt(
                secret.encode(config.security.ENCODING),
                new_client.salt.encode(config.security.ENCODING),
            )
            == new_client.hashed_secret
        )

    def test_get_client(self, db: Session, oauth_client) -> None:
        client = ClientDetail.get(db, id=config.security.OAUTH_ROOT_CLIENT_ID)
        hashed_access_key = hash_with_salt(
            config.security.OAUTH_ROOT_CLIENT_SECRET.encode(config.security.ENCODING),
            client.salt.encode(config.security.ENCODING),
        )

        assert "fidesopsadmin" == client.id
        assert client.scopes == SCOPE_REGISTRY
        assert client.hashed_secret == hashed_access_key

        client = ClientDetail.get(db, id=oauth_client.id)
        assert oauth_client.id == client.id
        assert oauth_client.hashed_secret == "thisisatest"

    def test_credentials_valid(self, db: Session) -> None:
        new_client, secret = ClientDetail.create_client_and_secret(db)

        assert new_client.credentials_valid("this-is-not-the-right-secret") is False
        assert new_client.credentials_valid(secret) is True

        new_client.delete(db)
