# pylint: disable=R0401, C0302

from __future__ import annotations

from enum import Enum as EnumType
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.cryptography.cryptographic_util import (
    hash_credential_with_salt,
    hash_value_with_salt,
)
from fides.api.cryptography.identity_salt import get_identity_salt
from fides.api.db.base_class import Base  # type: ignore[attr-defined]
from fides.api.db.base_class import JSONTypeOverride
from fides.api.migrations.hash_migration_mixin import HashMigrationMixin
from fides.api.schemas.redis_cache import Identity, LabeledIdentity, MultiValue
from fides.config import CONFIG

if TYPE_CHECKING:
    from fides.api.models.privacy_request.consent import Consent, ConsentRequest
    from fides.api.models.privacy_request.privacy_request import PrivacyRequest


class ProvidedIdentityType(EnumType):
    """Enum for privacy request identity types"""

    email = "email"
    phone_number = "phone_number"
    ga_client_id = "ga_client_id"
    ljt_readerID = "ljt_readerID"
    fides_user_device_id = "fides_user_device_id"
    external_id = "external_id"


class ProvidedIdentity(HashMigrationMixin, Base):  # pylint: disable=R0904
    """
    A table for storing identity fields and values provided at privacy request
    creation time.
    """

    privacy_request_id = Column(
        String,
        ForeignKey("privacyrequest.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    privacy_request = relationship(
        "PrivacyRequest",
        backref="provided_identities",
    )  # Which privacy request this identity belongs to

    field_name = Column(
        String,
        index=False,
        nullable=False,
    )
    field_label = Column(
        String,
        index=False,
        nullable=True,
    )
    hashed_value = Column(
        String,
        index=True,
        unique=False,
        nullable=True,
    )  # This field is used as a blind index for exact match searches
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
    consent = relationship(
        "Consent", back_populates="provided_identity", cascade="delete, delete-orphan"
    )
    consent_request = relationship(
        "ConsentRequest",
        back_populates="provided_identity",
        cascade="delete, delete-orphan",
    )

    @classmethod
    def bcrypt_hash_value(
        cls,
        value: MultiValue,
        encoding: str = "UTF-8",
    ) -> str:
        """
        Temporary function used to hash values to the previously used bcrypt hashes.
        This can be removed once the bcrypt to SHA-256 migration is complete.
        """

        SALT = "$2b$12$UErimNtlsE6qgYf2BrI1Du"
        value_str = str(value)
        hashed_value = hash_credential_with_salt(
            value_str.encode(encoding),
            SALT.encode(encoding),
        )
        return hashed_value

    @classmethod
    def hash_value(
        cls,
        value: MultiValue,
        encoding: str = "UTF-8",
    ) -> str:
        """Utility function to hash the value with a generated salt"""
        SALT = get_identity_salt()
        value_str = str(value)
        hashed_value = hash_value_with_salt(
            value_str.encode(encoding),
            SALT.encode(encoding),
        )
        return hashed_value

    def migrate_hashed_fields(self) -> None:
        if value := self.encrypted_value.get("value"):
            self.hashed_value = self.hash_value(value)
        self.is_hash_migrated = True

    def as_identity_schema(self) -> Identity:
        """Creates an Identity schema from a ProvidedIdentity record in the application DB."""

        identity_dict = {}
        if any(
            [
                not self.field_name,
                not self.encrypted_value,
            ]
        ):
            return Identity()

        value = self.encrypted_value.get("value")  # type:ignore
        if self.field_label:
            value = LabeledIdentity(label=self.field_label, value=value)
        identity_dict[self.field_name] = value
        return Identity(**identity_dict)
