import enum

from sqlalchemy import Boolean, Column
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
