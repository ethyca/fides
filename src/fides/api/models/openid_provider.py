import enum

from sqlalchemy import Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.db.base_class import Base
from fides.config import CONFIG


class ProviderEnum(enum.Enum):
    google = "google"
    okta = "okta"
    custom = "custom"


class OpenIDProvider(Base):
    """The DB ORM model for OpenIDProvider."""

    identifier = Column(String, unique=True, index=True)
    name = Column(String)
    provider = Column(EnumColumn(ProviderEnum))
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
    domain = Column(String, nullable=True)  # Used for Okta provider
    authorization_url = Column(String, nullable=True)  # Used for Custom provider
    token_url = Column(String, nullable=True)  # Used for Custom provider
    user_info_url = Column(String, nullable=True)  # Used for Custom provider

    @declared_attr
    def __tablename__(self) -> str:
        return "openid_provider"
