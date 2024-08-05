import enum

import requests
from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.db.base_class import Base
from fides.api.oidc_auth.base_oauth import BaseOAuth
from fides.config import CONFIG


class ProviderEnum(enum.Enum):
    google = "google"


class OpenIDProvider(Base):
    """The DB ORM model for OpenIDProvider."""

    provider = Column(EnumColumn(ProviderEnum), unique=True, index=True)
    client_id = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
        nullable=False,
    )
    client_secret = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
        nullable=False,
    )
    disabled = Column(Boolean, nullable=False, server_default="f")

    @declared_attr
    def __tablename__(self) -> str:
        return "openid_provider"

    def get_oauth_provider_class(self) -> type:
        from fides.api.oidc_auth.google_oauth import GoogleOAuth

        return {
            "google": GoogleOAuth,
        }.get(self.provider.value)

    def test(self) -> bool:
        oauth = self.get_oauth()
        authorization_url = oauth.get_authorization_url()
        test = requests.get(authorization_url)
        print("test.status_code", test.status_code)
        print("test.text", test.text)
        return True

    def get_oauth(self) -> BaseOAuth:
        return self.get_oauth_provider_class()(
            provider=self.provider,
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=f"http://localhost:3000/login/{self.provider}",
            scope=["email"],
        )
