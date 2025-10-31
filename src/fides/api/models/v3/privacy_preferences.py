"""SQLAlchemy model for the v3 privacy_preferences table."""

from sqlalchemy import (  # type: ignore[attr-defined]
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Identity,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.cryptography.cryptographic_util import hash_value_with_salt
from fides.api.cryptography.identity_salt import get_identity_salt
from fides.api.db.base_class import Base
from fides.api.schemas.redis_cache import MultiValue
from fides.config import CONFIG


class PrivacyPreferences(Base):
    """
    Model for the v3 privacy_preferences table.
    This is used for the v3 privacy preferences API.

    This table stores privacy preference records with a partitioning scheme
    based on the is_latest flag, splitting records into current and historic partitions.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "privacy_preferences"

    # Override the default id column from Base (which is a String UUID)
    # with a BigInteger identity column for this table
    id = Column(
        BigInteger,  # type: ignore[arg-type]
        Identity(start=1, increment=1, always=True),
        primary_key=True,
    )

    # Searchable/queryable data stored as JSONB
    search_data = Column(JSONB, nullable=True)

    # Full record data stored as encrypted text (contains PII)
    record_data = Column(
        StringEncryptedType(
            type_in=Text(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
        nullable=True,
    )

    # Partition key - determines if record goes to _current or _historic partition
    is_latest = Column(
        Boolean, nullable=False, server_default=text("false"), primary_key=True
    )

    # Override base class timestamp columns to match migration
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = Column(DateTime(timezone=True), nullable=True)

    @classmethod
    def hash_value(
        cls,
        value: MultiValue,
        encoding: str = "UTF-8",
    ) -> str:
        """Utility function to hash the value with a generated salt"""
        salt = get_identity_salt()
        value_str = str(value)
        hashed_value = hash_value_with_salt(
            value_str.encode(encoding),
            salt.encode(encoding),
        )
        return hashed_value
