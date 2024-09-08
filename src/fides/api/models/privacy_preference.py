from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Query, Session, relationship
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesGcmEngine

from fides.api.db.base_class import Base, JSONTypeOverride
from fides.api.migrations.hash_migration_mixin import HashMigrationMixin
from fides.api.models.privacy_notice import (
    ConsentMechanism,
    PrivacyNoticeHistory,
    UserConsentPreference,
)
from fides.api.models.privacy_request import (
    ExecutionLogStatus,
    PrivacyRequest,
    ProvidedIdentity,
)
from fides.api.schemas.language import SupportedLanguage
from fides.api.schemas.redis_cache import MultiValue
from fides.config import CONFIG


class RequestOrigin(Enum):
    """
    We currently extract the RequestOrigin from the Privacy Experience
    Config ComponentType when saving, so RequestOrigin needs to be a
    superset of ComponentType.

    Not at the db level due to being subject to change.
    Only add here, do not remove
    """

    privacy_center = "privacy_center"
    overlay = "overlay"  # DEPRECATED. DO NOT REMOVE.
    modal = "modal"
    banner_and_modal = "banner_and_modal"
    api = "api"
    tcf_overlay = "tcf_overlay"


class ConsentMethod(Enum):
    # Not at the db level due to being subject to change.
    # Only add here, do not remove
    button = "button"  # deprecated- keeping for backwards-compatibility
    reject = "reject"
    accept = "accept"
    save = "save"
    dismiss = "dismiss"
    gpc = "gpc"
    individual_notice = "individual_notice"
    acknowledge = "acknowledge"


class ServingComponent(Enum):
    """
    This differs from component type because we want to record exactly
    where consent was served.

    Not at the db level due to being subject to change.
    Only add here, do not remove
    """

    overlay = "overlay"  # DEPRECATED. DO NOT REMOVE.
    banner = "banner"
    modal = "modal"
    privacy_center = "privacy_center"
    tcf_overlay = "tcf_overlay"  # TCF modal in this case
    tcf_banner = "tcf_banner"


class ConsentIdentitiesMixin(HashMigrationMixin):
    """Encrypted and hashed identities for consent reporting and last saved preference retrieval"""

    email = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )  # Encrypted email

    fides_user_device = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )  # Encrypted fides user device

    phone_number = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )  # Encrypted phone number

    external_id = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )

    hashed_email = Column(
        String,
        index=True,
    )  # For exact match searches

    hashed_fides_user_device = Column(String, index=True)  # For exact match searches

    hashed_phone_number = Column(
        String,
        index=True,
    )  # For exact match searches

    hashed_external_id = Column(
        String,
        index=True,
    )  # For exact match searches

    @classmethod
    def bcrypt_hash_value(
        cls,
        value: MultiValue,
        encoding: str = "UTF-8",
    ) -> Optional[str]:
        """
        Temporary function used to hash values to the previously used bcrypt hashes.
        This can be removed once the bcrypt to SHA-256 migration is complete.
        """
        if not value:
            return None

        return ProvidedIdentity.bcrypt_hash_value(value, encoding)

    @classmethod
    def hash_value(
        cls,
        value: Optional[MultiValue] = None,
        encoding: str = "UTF-8",
    ) -> Optional[str]:
        """Utility function to hash the value with a generated salt
        This returns None if there's no value, unlike ProvidedIdentity.hash_value
        """
        if not value:
            return None

        return ProvidedIdentity.hash_value(value, encoding)

    def migrate_hashed_fields(self) -> None:
        if unencrypted_email := self.email:
            self.hashed_email = self.hash_value(unencrypted_email)
        if unencrypted_fides_user_device := self.fides_user_device:
            self.hashed_fides_user_device = self.hash_value(
                unencrypted_fides_user_device
            )
        if unencrypted_phone_number := self.phone_number:
            self.hashed_phone_number = self.hash_value(unencrypted_phone_number)
        if unencrypted_external_id := self.external_id:
            self.hashed_external_id = self.hash_value(unencrypted_external_id)
        self.is_hash_migrated = True


class CurrentPrivacyPreference(ConsentIdentitiesMixin, Base):
    """Stores the latest saved privacy preferences for a given user

    Email/phone/fides device must be unique.  If we later tie identities together, these records
    are consolidated.
    """

    @declared_attr
    def __tablename__(self) -> str:
        """Table name is currentprivacypreferencev2 - currentprivacypreference was deprecated and removed"""
        return "currentprivacypreferencev2"

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    preferences = Column(
        MutableDict.as_mutable(JSONB)
    )  # All saved preferences against Privacy Notices and TCF Notices

    fides_string = Column(String)

    property_id = Column(
        String,
        nullable=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )

    @declared_attr
    def __table_args__(cls: Any) -> Tuple:
        return (
            UniqueConstraint(
                "email",
                "property_id",
                name="last_saved_for_email_per_property_id",
            ),
            UniqueConstraint(
                "phone_number",
                "property_id",
                name="last_saved_for_phone_number_per_property_id",
            ),
            UniqueConstraint(
                "fides_user_device",
                "property_id",
                name="last_saved_for_fides_user_device_per_property_id",
            ),
            UniqueConstraint(
                "external_id",
                "property_id",
                name="last_saved_for_external_id_per_property_id",
            ),
            Index(
                "idx_currentprivacypreferencev2_unmigrated",
                "is_hash_migrated",
                postgresql_where=cls.is_hash_migrated.is_(  # pylint: disable=no-member
                    False
                ),
            ),
        )


class LastServedNotice(Base):
    """
    DEPRECATED. DO NOT UPDATE THIS TABLE.  This will soon be removed.

    This table consolidates every notice a user has been served, (analogous to CurrentPrivacyPreference
    but it is being removed). Backend is not writing to this any longer.
    """

    @declared_attr
    def __tablename__(self) -> str:
        """Table name is lastservednoticev2 - lastservednotice was deprecated and removed"""
        return "lastservednoticev2"

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    served = Column(
        MutableDict.as_mutable(JSONB)
    )  # All Privacy Notices and TCF Notices Served

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "email",
            name="last_served_for_email",
        ),
        UniqueConstraint(
            "phone_number",
            name="last_served_for_phone_number",
        ),
        UniqueConstraint(
            "fides_user_device",
            name="last_served_for_fides_user_device",
        ),
    )

    email = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )  # Encrypted email

    fides_user_device = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )  # Encrypted fides user device

    phone_number = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )  # Encrypted phone number

    hashed_email = Column(
        String,
        index=True,
    )  # For exact match searches

    hashed_fides_user_device = Column(String, index=True)  # For exact match searches

    hashed_phone_number = Column(
        String,
        index=True,
    )  # For exact match searches

    @classmethod
    def generate_served_notice_history_id(cls) -> str:
        """Generate a served notice history id

        We save privacy preferences and return immediately alongside this generated
        id that we build up front.  This value will be saved under related ServedNoticeHistory.served_notice_history_id
        fields, and then passed in to save privacy preferences and saved under PrivacyPreferenceHistory.served_notice_history_id
        """
        return f"ser_{uuid.uuid4()}"


class ConsentReportingMixinV2(ConsentIdentitiesMixin):
    """Consent Reporting Mixin to share between historical preferences saved and
    historical notices served
    """

    anonymized_ip_address = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    language = Column(
        EnumColumn(
            SupportedLanguage,
            native_enum=False,
            values_callable=lambda x: [i.value for i in x],
        ),
        index=True,
    )

    notice_key = Column(String, index=True)  # Privacy Notice Key

    notice_mechanism = Column(
        EnumColumn(ConsentMechanism), index=True
    )  # Privacy Notice Mechanism

    notice_name = Column(String, index=True)  # Privacy Notice name or "TCF"

    property_id = Column(
        String,
        index=True,
        nullable=True,
    )

    # The specific version of the experience config the user was shown to present the relevant notice
    # Contains the version, language, button labels, description, etc.
    @declared_attr
    def privacy_experience_config_history_id(cls) -> Column:
        return Column(
            String,
            ForeignKey("privacyexperienceconfighistory.id"),
            index=True,
        )

    @declared_attr
    def privacy_notice_history_id(cls) -> Column:
        """
        The specific historical record the user consented to - applicable when
        saving preferences with respect to a privacy notice directly
        """
        return Column(String, ForeignKey(PrivacyNoticeHistory.id), index=True)

    # Preferences and Notices Served are saved in celery - there may be some gap in between
    # when the data was received, and when we actually were able to save it to the db
    received_at = Column(DateTime(timezone=True))

    # Location where we received the request
    request_origin = Column(EnumColumn(RequestOrigin))

    url_recorded = Column(String)

    user_agent = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )

    user_geography = Column(String, index=True)

    # Relationships
    @declared_attr
    def privacy_notice_history(cls) -> relationship:
        return relationship(PrivacyNoticeHistory)


class ServedNoticeHistory(ConsentReportingMixinV2, Base):
    """A Historical Record of every time a Notice was served to a user

    Each Privacy Notice served gets its own record, while served TCF attributes are collapsed into one record.

    The "served_notice_history_id" column on this table can be mapped to the PrivacyPreferenceHistory records
    to calculate conversion.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "servednoticehistory"

    acknowledge_mode = Column(
        Boolean,
        default=False,
    )

    serving_component = Column(EnumColumn(ServingComponent), nullable=False, index=True)

    # Generated identifier for the ServedNoticeHistory, used to link a ServedNoticeHistory and PrivacyPreferenceHistory
    # record together
    served_notice_history_id = Column(String, index=True)

    tcf_served = Column(
        MutableDict.as_mutable(JSONB)
    )  # Dict of all the TCF attributes served if applicable

    @staticmethod
    def get_by_served_id(db: Session, served_id: str) -> Query:
        """Retrieves all ServedNoticeHistory records with a common served_notice_history_id - generated
        before the task was queued to store these records
        """
        return db.query(ServedNoticeHistory).filter(
            ServedNoticeHistory.served_notice_history_id == served_id
        )


class PrivacyPreferenceHistory(ConsentReportingMixinV2, Base):
    """A Historical Record of every time a Notice was saved for a user

    Each Privacy Notice served gets its own record, while served TCF attributes are collapsed into one record.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "privacypreferencehistory"

    # Systems capable of propagating their consent, and their status.  If the preference is
    # not relevant for the system, or we couldn't propagate a preference, the status is skipped
    affected_system_status = Column(
        MutableDict.as_mutable(JSONB), server_default="{}", default=dict
    )

    # Optional, if fides_string was supplied directly
    fides_string = Column(String)

    # Accept, reject, etc. especially useful for TCF
    method = Column(EnumColumn(ConsentMethod))

    # Whether the user wants to opt in, opt out, or has acknowledged the notice.
    # For TCF notices, we just say "tcf", and more detailed preferences are under "tcf_preferences"
    preference = Column(EnumColumn(UserConsentPreference), index=True, nullable=False)

    # The privacy request created to propagate the preferences if applicable.  The notice
    # must have had system wide enforcement. TCF notices don't have privacy requests created.
    privacy_request_id = Column(
        String, ForeignKey(PrivacyRequest.id, ondelete="SET NULL"), index=True
    )

    # Relevant identities are added to the report during request propagation
    secondary_user_ids = Column(
        MutableDict.as_mutable(
            StringEncryptedType(
                JSONTypeOverride,
                CONFIG.security.app_encryption_key,
                AesGcmEngine,
                "pkcs5",
            )
        ),
    )

    # The record of where we served the notice in the frontend, for conversion purposes.
    served_notice_history_id = Column(String, index=True)

    tcf_preferences = Column(
        MutableDict.as_mutable(JSONB)
    )  # Dict of TCF attributes saved, for a TCF notice

    privacy_request = relationship(PrivacyRequest, backref="privacy_preferences")

    def cache_system_status(
        self, db: Session, system: str, status: ExecutionLogStatus
    ) -> None:
        """Update the cached affected system status for consent reporting

        Typically this should just be called for consent connectors only.
        If no request is made or email is sent, this should be called with a status of skipped.
        """
        if not self.affected_system_status:
            self.affected_system_status = {}
        self.affected_system_status[system] = (
            status.name
        )  # To avoid using "ExecutionLogStatus.paused" in the logs
        self.save(db)

    def update_secondary_user_ids(
        self, db: Session, new_identities: Dict[str, Any]
    ) -> None:
        """Update secondary user identities for consent reporting

        The intent is to only put identities here that we intend to send to third party systems.
        """
        secondary_user_ids = self.secondary_user_ids or {}
        secondary_user_ids.update(new_identities)
        self.secondary_user_ids = secondary_user_ids
        self.save(db)
