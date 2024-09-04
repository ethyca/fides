from sqlalchemy.orm import Session

from fides.api.cryptography.cryptographic_util import hash_credential_with_salt
from fides.api.models.client import ClientDetail
from fides.common.api.scope_registry import SCOPE_REGISTRY
from fides.config import CONFIG


class TestClientModel:
    def test_create_client_and_secret(self, db: Session) -> None:
        new_client, secret = ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
        )

        assert new_client.hashed_secret is not None
        assert (
            hash_credential_with_salt(
                secret.encode(CONFIG.security.encoding),
                new_client.salt.encode(CONFIG.security.encoding),
            )
            == new_client.hashed_secret
        )

    def test_get_client(self, db: Session, oauth_client) -> None:
        client = ClientDetail.get(
            db,
            object_id=CONFIG.security.oauth_root_client_id,
            config=CONFIG,
            scopes=SCOPE_REGISTRY,
        )

        hashed_access_key = hash_credential_with_salt(
            CONFIG.security.oauth_root_client_secret.encode(CONFIG.security.encoding),
            client.salt.encode(CONFIG.security.encoding),
        )

        assert "fidesadmin" == client.id
        assert client.scopes == SCOPE_REGISTRY
        assert client.hashed_secret == hashed_access_key

        client = ClientDetail.get(db, object_id=oauth_client.id, config=CONFIG)
        assert oauth_client.id == client.id
        assert oauth_client.hashed_secret == "thisisatest"

    def test_credentials_valid(self, db: Session) -> None:
        new_client, secret = ClientDetail.create_client_and_secret(
            db,
            CONFIG.security.oauth_client_id_length_bytes,
            CONFIG.security.oauth_client_secret_length_bytes,
        )

        assert new_client.credentials_valid("this-is-not-the-right-secret") is False
        assert new_client.credentials_valid(secret) is True

        new_client.delete(db)
