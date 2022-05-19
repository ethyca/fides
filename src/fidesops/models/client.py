import json
from datetime import datetime
from typing import Any, List, Optional, Tuple

from sqlalchemy import ARRAY, Column, ForeignKey, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

from fidesops.api.v1.scope_registry import SCOPE_REGISTRY
from fidesops.core.config import config
from fidesops.db.base_class import Base
from fidesops.models.fidesops_user import FidesopsUser
from fidesops.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fidesops.util.cryptographic_util import (
    generate_salt,
    generate_secure_random_string,
    hash_with_salt,
)

DEFAULT_SCOPES: List[str] = []
ADMIN_UI_ROOT = "admin_ui_root"


class ClientDetail(Base):
    """The persisted details about a client in the system"""

    @declared_attr
    def __tablename__(cls) -> str:
        return "client"

    hashed_secret = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    scopes = Column(ARRAY(String), nullable=False, default="{}")
    fides_key = Column(String, index=True, unique=True, nullable=True)
    user_id = Column(
        String, ForeignKey(FidesopsUser.id_field_path), nullable=True, unique=True
    )

    @classmethod
    def create_client_and_secret(
        cls,
        db: Session,
        scopes: List[str] = DEFAULT_SCOPES,
        fides_key: str = None,
        user_id: str = None,
    ) -> Tuple["ClientDetail", str]:
        """Creates a ClientDetail and returns that along with the unhashed secret so it can
        be returned to the user on create"""

        client_id = generate_secure_random_string(
            config.security.OAUTH_CLIENT_ID_LENGTH_BYTES
        )
        secret = generate_secure_random_string(
            config.security.OAUTH_CLIENT_SECRET_LENGTH_BYTES
        )

        if not scopes:
            scopes = DEFAULT_SCOPES

        salt = generate_salt()
        hashed_secret = hash_with_salt(
            secret.encode(config.security.ENCODING),
            salt.encode(config.security.ENCODING),
        )

        client = super().create(
            db,
            data={
                "id": client_id,
                "salt": salt,
                "hashed_secret": hashed_secret,
                "scopes": scopes,
                "fides_key": fides_key,
                "user_id": user_id,
            },
        )
        return client, secret

    @classmethod
    def get(
        cls, db: Session, *, id: Any  # pylint: disable=W0622
    ) -> Optional["ClientDetail"]:
        """Fetch a database record via a table ID"""
        if id == config.security.OAUTH_ROOT_CLIENT_ID:
            return _get_root_client_detail()
        return super().get(db, id=id)

    def create_access_code_jwe(self) -> str:
        """Generates a JWE from the client detail provided"""
        from fidesops.util.oauth_util import generate_jwe

        payload = {
            # client id may not be necessary
            JWE_PAYLOAD_CLIENT_ID: self.id,
            JWE_PAYLOAD_SCOPES: self.scopes,
            JWE_ISSUED_AT: datetime.now().isoformat(),
        }
        return generate_jwe(json.dumps(payload))

    def credentials_valid(self, provided_secret: str) -> bool:
        """Verifies that the provided secret is correct"""
        provided_secret_hash = hash_with_salt(
            provided_secret.encode(config.security.ENCODING),
            self.salt.encode(config.security.ENCODING),
        )

        return provided_secret_hash == self.hashed_secret


def _get_root_client_detail() -> Optional[ClientDetail]:
    root_secret = config.security.OAUTH_ROOT_CLIENT_SECRET_HASH
    assert root_secret is not None
    return ClientDetail(
        id=config.security.OAUTH_ROOT_CLIENT_ID,
        hashed_secret=root_secret[0],
        salt=root_secret[1].decode(config.security.ENCODING),
        scopes=SCOPE_REGISTRY,
    )
