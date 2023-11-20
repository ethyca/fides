from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import ARRAY, Column, ForeignKey, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

from fides.api.cryptography.cryptographic_util import (
    generate_salt,
    generate_secure_random_string,
    hash_with_salt,
)
from fides.api.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_ROLES,
    JWE_PAYLOAD_SCOPES,
    JWE_PAYLOAD_SYSTEMS,
)
from fides.api.db.base_class import Base
from fides.api.models.fides_user import FidesUser
from fides.api.oauth.jwt import generate_jwe
from fides.config import FidesConfig

DEFAULT_SCOPES: list[str] = []
DEFAULT_ROLES: list[str] = []
DEFAULT_SYSTEMS: list[str] = []


class ClientDetail(Base):
    """The persisted details about a client in the system"""

    @declared_attr
    def __tablename__(self) -> str:
        return "client"

    hashed_secret = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    scopes = Column(ARRAY(String), nullable=False, server_default="{}", default=dict)
    roles = Column(ARRAY(String), nullable=False, server_default="{}", default=dict)
    systems = Column(ARRAY(String), nullable=False, server_default="{}", default=dict)
    fides_key = Column(String, index=True, unique=True, nullable=True)
    user_id = Column(
        String, ForeignKey(FidesUser.id_field_path), nullable=True, unique=True
    )

    @classmethod
    def create_client_and_secret(
        cls,
        db: Session,
        client_id_byte_length: int,
        client_secret_byte_length: int,
        *,
        scopes: list[str] | None = None,
        fides_key: str = None,
        user_id: str = None,
        encoding: str = "UTF-8",
        roles: list[str] | None = None,
        systems: list[str] | None = None,
    ) -> tuple["ClientDetail", str]:
        """Creates a ClientDetail and returns that along with the unhashed secret
        so it can be returned to the user on create
        """

        client_id = generate_secure_random_string(client_id_byte_length)
        secret = generate_secure_random_string(client_secret_byte_length)

        if not scopes:
            scopes = DEFAULT_SCOPES

        if not roles:
            roles = DEFAULT_ROLES

        if not systems:
            systems = DEFAULT_SYSTEMS

        salt = generate_salt()
        hashed_secret = hash_with_salt(
            secret.encode(encoding),
            salt.encode(encoding),
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
                "roles": roles,
                "systems": systems,
            },
        )
        return client, secret  # type: ignore

    @classmethod
    def get(  # type: ignore
        cls,
        db: Session,
        *,
        object_id: Any,
        config: FidesConfig,
        scopes: list[str] = [],
        roles: list[str] = [],
    ) -> ClientDetail | None:
        """Fetch a database record via a client_id"""
        if object_id == config.security.oauth_root_client_id:
            return _get_root_client_detail(config, scopes=scopes, roles=roles)
        return super().get(db, object_id=object_id)

    def create_access_code_jwe(self, encryption_key: str) -> str:
        """Generates a JWE from the client detail provided"""
        payload = {
            # client id may not be necessary
            JWE_PAYLOAD_CLIENT_ID: self.id,
            JWE_PAYLOAD_SCOPES: self.scopes,
            JWE_ISSUED_AT: datetime.now().isoformat(),
            JWE_PAYLOAD_ROLES: self.roles,
            JWE_PAYLOAD_SYSTEMS: self.systems,
        }
        return generate_jwe(json.dumps(payload), encryption_key)

    def credentials_valid(self, provided_secret: str, encoding: str = "UTF-8") -> bool:
        """Verifies that the provided secret is correct."""
        provided_secret_hash = hash_with_salt(
            provided_secret.encode(encoding),
            self.salt.encode(encoding),
        )

        return provided_secret_hash == self.hashed_secret


def _get_root_client_detail(
    config: FidesConfig,
    scopes: list[str],
    roles: list[str],
    encoding: str = "UTF-8",
) -> ClientDetail | None:
    """
    Return a root ClientDetail
    """
    if not config.security.oauth_root_client_secret_hash:
        raise ValueError("A root client hash is required")

    if scopes or roles:
        return ClientDetail(
            id=config.security.oauth_root_client_id,
            hashed_secret=config.security.oauth_root_client_secret_hash[0],
            salt=config.security.oauth_root_client_secret_hash[1].decode(encoding),
            scopes=scopes,
            roles=roles,
            systems=[],
        )

    return ClientDetail(
        id=config.security.oauth_root_client_id,
        hashed_secret=config.security.oauth_root_client_secret_hash[0],
        salt=config.security.oauth_root_client_secret_hash[1].decode(encoding),
        scopes=DEFAULT_SCOPES,
        roles=DEFAULT_ROLES,
        systems=DEFAULT_SYSTEMS,
    )
