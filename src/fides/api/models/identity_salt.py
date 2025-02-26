from sqlalchemy import Boolean, CheckConstraint, Column, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.db.base_class import Base  # type: ignore[attr-defined]
from fides.api.db.base_class import JSONTypeOverride
from fides.config import CONFIG


class IdentitySalt(Base):
    """
    A single-row table used to store the encrypted salt value used for identity hashing (SHA-256).
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "identity_salt"

    encrypted_value = Column(
        MutableDict.as_mutable(
            StringEncryptedType(
                JSONTypeOverride,
                CONFIG.security.app_encryption_key,
                AesGcmEngine,
                "pkcs5",
            )
        ),
        nullable=True,
    )  # Type bytea in the db
    single_row = Column(
        Boolean,
        default=True,
        nullable=False,
        unique=True,
    )  # used to constrain table to one row

    CheckConstraint("single_row", name="identity_salt_single_row_check")
    UniqueConstraint("single_row", name="identity_salt_single_row_unique")
