# pylint: disable=R0401, C0302, W0143

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import ARRAY, Boolean, Column, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Session, relationship
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesGcmEngine

from fides.api.db.base_class import Base, JSONTypeOverride
from fides.api.models.privacy_notice import (
    PrivacyNotice,
    PrivacyNoticeHistory,
    UserConsentPreference,
)
from fides.api.models.privacy_request import (
    ExecutionLogStatus,
    PrivacyRequest,
    ProvidedIdentity,
)
from fides.api.models.sql_models import System  # type: ignore[attr-defined]
from fides.config import CONFIG


class RequestOrigin(Enum):
    privacy_center = "privacy_center"
    overlay = "overlay"
    api = "api"
    tcf_overlay = "tcf_overlay"


class ConsentMethod(Enum):
    button = "button"  # deprecated- keeping for backwards-compatibility
    reject = "reject"
    accept = "accept"
    save = "save"
    dismiss = "dismiss"
    gpc = "gpc"
    individual_notice = "individual_notice"


class ConsentReportingMixin:
    """Mixin to be shared between PrivacyPreferenceHistory and ServedNoticeHistory
    Contains common user details, and information about the notice, experience, experience config, etc.
    for use in consent reporting.
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

    # Encrypted email, for reporting
    email = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )

    # Encrypted fides user device id, for reporting
    fides_user_device = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )

    # Optional FK to a fides user device id provided identity, if applicable
    @declared_attr
    def fides_user_device_provided_identity_id(cls) -> Column:
        return Column(String, ForeignKey(ProvidedIdentity.id), index=True)

    # Hashed email, for searching
    hashed_email = Column(String, index=True)
    # Hashed fides user device id, for searching
    hashed_fides_user_device = Column(String, index=True)
    # Hashed phone number, for searching
    hashed_phone_number = Column(String, index=True)
    # Encrypted phone number, for reporting
    phone_number = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
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

    # The specific experience under which the user was presented the relevant notice
    # Minimal information stored here, mostly just region and component type
    @declared_attr
    def privacy_experience_id(cls) -> Column:
        return Column(String, ForeignKey("privacyexperience.id"), index=True)

    @declared_attr
    def privacy_notice_history_id(cls) -> Column:
        """
        The specific historical record the user consented to - applicable when
        saving preferences with respect to a privacy notice directly
        """
        return Column(String, ForeignKey(PrivacyNoticeHistory.id), index=True)

    # Optional FK to a verified provided identity (like email or phone), if applicable
    @declared_attr
    def provided_identity_id(cls) -> Column:
        return Column(String, ForeignKey(ProvidedIdentity.id), index=True)

    # Location where we received the request
    request_origin = Column(EnumColumn(RequestOrigin))  # privacy center, overlay, API

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

    # ==== TCF Attributes against which preferences can be saved ==== #
    feature = Column(
        Integer, index=True
    )  # When saving privacy preferences with respect to a TCF feature directly
    purpose_consent = Column(
        Integer, index=True
    )  # When saving privacy preferences with respect to a TCF purpose with a consent legal basis
    purpose_legitimate_interests = Column(
        Integer, index=True
    )  # When saving privacy preferences with respect to a TCF purpose with a legitimate interests legal basis
    special_feature = Column(
        Integer, index=True
    )  # When saving privacy preferences with respect to a TCF special feature directly
    special_purpose = Column(
        Integer, index=True
    )  # When saving privacy preferences with respect to a TCF special purpose directly
    vendor_consent = Column(
        String, index=True
    )  # When saving privacy preferences with respect to a vendor with a legal basis of consent
    vendor_legitimate_interests = Column(
        String, index=True
    )  # When saving privacy preferences with respect to a vendor with a legal basis of legitimate interests
    system_consent = Column(
        String, index=True
    )  # When saving privacy preferences with respect to a system id with consent legal basis, in the case where the vendor is unknown
    system_legitimate_interests = Column(
        String, index=True
    )  # When saving privacy preferences with respect to a system id with legitimate interests legal basis, in the case where the vendor is unknown
    tcf_version = Column(String)

    @property
    def privacy_notice_id(self) -> Optional[str]:
        if self.privacy_notice_history:
            return self.privacy_notice_history.privacy_notice_id
        return None

    # Relationships
    @declared_attr
    def privacy_notice_history(cls) -> relationship:
        return relationship(PrivacyNoticeHistory)

    @declared_attr
    def provided_identity(cls) -> relationship:
        return relationship(ProvidedIdentity, foreign_keys=[cls.provided_identity_id])

    @declared_attr
    def fides_user_device_provided_identity(cls) -> relationship:
        return relationship(
            ProvidedIdentity, foreign_keys=[cls.fides_user_device_provided_identity_id]
        )


class ServingComponent(Enum):
    overlay = "overlay"
    banner = "banner"
    privacy_center = "privacy_center"
    tcf_overlay = "tcf_overlay"
    tcf_banner = "tcf_banner"


class ServedNoticeHistory(ConsentReportingMixin, Base):
    """A historical record of every time a resource was served in the UI to which an end user could consent

    This might be a privacy notice, a purpose, special purpose, feature, special feature, vendor, or system.

    The name "ServedNoticeHistory" comes from where we originally just stored the history of every time a notice was
    served, but this table was later expanded to store when TCF attributes like purposes, special purposes, etc. were stored
    """

    acknowledge_mode = Column(
        Boolean,
        default=False,
    )
    serving_component = Column(EnumColumn(ServingComponent), nullable=False, index=True)

    last_served_record = (
        relationship(  # Only exists if this is the same as the Last Served Notice
            "LastServedNotice",
            back_populates="served_notice_history",
            cascade="all, delete",
            uselist=False,
        )
    )


class PrivacyPreferenceHistory(ConsentReportingMixin, Base):
    """The DB ORM model for storing PrivacyPreferenceHistory, used for saving
    every time consent preferences are saved for reporting purposes.

    Soon to be deprecated in favor of PrivacyPreferenceHistoryv2
    """

    # Systems capable of propagating their consent, and their status.  If the preference is
    # not relevant for the system, or we couldn't propagate a preference, the status is skipped
    affected_system_status = Column(
        MutableDict.as_mutable(JSONB), server_default="{}", default=dict
    )

    # Button, individual notices
    method = Column(EnumColumn(ConsentMethod))
    # Whether the user wants to opt in, opt out, or has acknowledged the notice
    preference = Column(EnumColumn(UserConsentPreference), nullable=False, index=True)

    # The privacy request created to propagate the preferences
    privacy_request_id = Column(
        String, ForeignKey(PrivacyRequest.id, ondelete="SET NULL"), index=True
    )

    # Systems whose data use match.  This doesn't necessarily mean we propagate.
    # Some may be intentionally skipped later.
    relevant_systems = Column(MutableList.as_mutable(ARRAY(String)))

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
    )  # Cache secondary user ids (cookies, etc) if known for reporting purposes.

    # The record of where we served the notice in the frontend, for conversion purposes
    served_notice_history_id = Column(
        String, ForeignKey(ServedNoticeHistory.id), index=True
    )

    # Relationships
    privacy_request = relationship(PrivacyRequest, backref="privacy_preferences")
    served_notice_history = relationship(ServedNoticeHistory, backref="served_notices")

    current_privacy_preference = relationship(  # Only exists if this is the same as the Current Privacy Preference
        "CurrentPrivacyPreference",
        back_populates="privacy_preference_history",
        cascade="all, delete",
        uselist=False,
    )

    @property
    def privacy_notice_id(self) -> Optional[str]:
        if self.privacy_notice_history:
            return self.privacy_notice_history.privacy_notice_id
        return None

    def cache_system_status(
        self, db: Session, system: str, status: ExecutionLogStatus
    ) -> None:
        """Update the cached affected system status for consent reporting

        Typically this should just be called for consent connectors only.
        If no request is made or email is sent, this should be called with a status of skipped.
        """
        if not self.affected_system_status:
            self.affected_system_status = {}
        self.affected_system_status[system] = status.value
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


class LastSavedMixin:
    """Stores common fields for the last saved preference or last served notice"""

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )

    tcf_version = Column(String)

    # ==== TCF Attributes that can be served ==== #
    feature = Column(Integer, index=True)  # When a feature was served directly (TCF)

    purpose_consent = Column(
        Integer, index=True
    )  # When a TCF purpose with consent legal basis was served directly (TCF)
    purpose_legitimate_interests = Column(
        Integer, index=True
    )  # When a TCF purpose with legitimate interests legal basis was served directly (TCF)

    special_feature = Column(
        Integer, index=True
    )  # When a special feature was served directly (TCF)

    special_purpose = Column(
        Integer, index=True
    )  # When a special purpose was served directly (TCF)

    vendor_consent = Column(
        String, index=True
    )  # When a TCF vendor with consent legal basis was served directly (TCF)
    vendor_legitimate_interests = Column(
        String, index=True
    )  # When a TCF vendor with legitimate interest legal basis was served directly (TCF)

    system_consent = Column(
        String, index=True
    )  # When a system id with consent legal basis was served directly.  Used for when the specific vendor type is unknown.
    system_legitimate_interests = Column(
        String, index=True
    )  # When a system id with legitimate interest legal basis was served directly.  Used for when the specific vendor type is unknown.

    @declared_attr
    def provided_identity_id(cls) -> Column:
        return Column(String, ForeignKey(ProvidedIdentity.id), index=True)

    @declared_attr
    def fides_user_device_provided_identity_id(cls) -> Column:
        return Column(String, ForeignKey(ProvidedIdentity.id), index=True)

    @declared_attr
    def privacy_notice_id(cls) -> Column:
        """When saving a notice was served directly"""
        return Column(String, ForeignKey(PrivacyNotice.id), index=True)

    @declared_attr
    def privacy_notice_history_id(cls) -> Column:
        return Column(String, ForeignKey(PrivacyNoticeHistory.id), index=True)

    # Relationships
    @declared_attr
    def provided_identity(cls) -> relationship:
        return relationship(ProvidedIdentity, foreign_keys=[cls.provided_identity_id])

    @declared_attr
    def fides_user_device_provided_identity(cls) -> relationship:
        return relationship(
            ProvidedIdentity, foreign_keys=[cls.fides_user_device_provided_identity_id]
        )

    @declared_attr
    def privacy_notice(cls) -> relationship:
        return relationship(PrivacyNotice)

    @declared_attr
    def privacy_notice_history(cls) -> relationship:
        return relationship(PrivacyNoticeHistory)


class CurrentPrivacyPreference(LastSavedMixin, Base):
    """Stores only the user's most recently saved preference for a given privacy notice

    The specific privacy notice history and privacy preference history record are linked as well.
    """

    preference = Column(EnumColumn(UserConsentPreference), nullable=False, index=True)

    privacy_preference_history_id = Column(
        String, ForeignKey(PrivacyPreferenceHistory.id), nullable=False, index=True
    )

    __table_args__ = (
        UniqueConstraint(
            "provided_identity_id", "privacy_notice_id", name="identity_privacy_notice"
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "privacy_notice_id",
            name="fides_user_device_identity_privacy_notice",
        ),
        UniqueConstraint(
            "provided_identity_id", "purpose_consent", name="identity_purpose_consent"
        ),
        UniqueConstraint(
            "provided_identity_id",
            "purpose_legitimate_interests",
            name="identity_purpose_leg_interests",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "purpose_consent",
            name="fides_user_device_identity_purpose_consent",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "purpose_legitimate_interests",
            name="fides_user_device_identity_purpose_leg_interests",
        ),
        UniqueConstraint(
            "provided_identity_id", "special_purpose", name="identity_special_purpose"
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "special_purpose",
            name="fides_user_device_identity_special_purpose",
        ),
        UniqueConstraint(
            "provided_identity_id", "vendor_consent", name="identity_vendor_consent"
        ),
        UniqueConstraint(
            "provided_identity_id",
            "vendor_legitimate_interests",
            name="identity_vendor_leg_interests",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "vendor_consent",
            name="fides_user_device_identity_vendor_consent",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "vendor_legitimate_interests",
            name="fides_user_device_identity_vendor_leg_interests",
        ),
        UniqueConstraint(
            "provided_identity_id", "system_consent", name="identity_system_consent"
        ),
        UniqueConstraint(
            "provided_identity_id",
            "system_legitimate_interests",
            name="identity_system_leg_interests",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "system_consent",
            name="fides_user_device_identity_system_consent",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "system_legitimate_interests",
            name="fides_user_device_identity_system_leg_interests",
        ),
        UniqueConstraint("provided_identity_id", "feature", name="identity_feature"),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "feature",
            name="fides_user_device_identity_feature",
        ),
        UniqueConstraint(
            "provided_identity_id", "special_feature", name="identity_special_feature"
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "special_feature",
            name="fides_user_device_identity_special_feature",
        ),
    )

    # Relationships
    privacy_preference_history = relationship(
        PrivacyPreferenceHistory, cascade="delete, delete-orphan", single_parent=True
    )


class LastServedNotice(LastSavedMixin, Base):
    """Stores the last time a consent attribute was served for a given user.

    Also consolidates serving consent among various user identities.

    The name "LastServedNotice" is because we originally stored serving notices to end users,
    and we expanded this table to store serving tcf components like purposes, special purposes, etc.
    to end users.
    """

    served_notice_history_id = Column(
        String, ForeignKey(ServedNoticeHistory.id), nullable=False, index=True
    )

    __table_args__ = (
        UniqueConstraint(
            "provided_identity_id",
            "privacy_notice_id",
            name="last_served_identity_privacy_notice",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "privacy_notice_id",
            name="last_served_fides_user_device_identity_privacy_notice",
        ),
        UniqueConstraint(
            "provided_identity_id",
            "purpose_consent",
            name="last_served_identity_purpose_consent",
        ),
        UniqueConstraint(
            "provided_identity_id",
            "purpose_legitimate_interests",
            name="last_served_identity_purpose_legitimate_interests",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "purpose_consent",
            name="last_served_fides_user_device_identity_purpose_consent",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "purpose_legitimate_interests",
            name="last_served_fides_user_device_identity_purpose_leg_interests",
        ),
        UniqueConstraint(
            "provided_identity_id",
            "special_purpose",
            name="last_served_identity_special_purpose",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "special_purpose",
            name="last_served_fides_user_device_identity_special_purpose",
        ),
        UniqueConstraint(
            "provided_identity_id",
            "feature",
            name="last_served_identity_feature",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "feature",
            name="last_served_fides_user_device_identity_feature",
        ),
        UniqueConstraint(
            "provided_identity_id",
            "vendor_consent",
            name="last_served_identity_vendor_consent",
        ),
        UniqueConstraint(
            "provided_identity_id",
            "vendor_legitimate_interests",
            name="last_served_identity_vendor_leg_interests",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "vendor_consent",
            name="last_served_fides_user_device_identity_vendor_consent",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "vendor_legitimate_interests",
            name="last_served_fides_user_device_identity_vendor_leg_interests",
        ),
        UniqueConstraint(
            "provided_identity_id",
            "system_consent",
            name="last_served_identity_system_consent",
        ),
        UniqueConstraint(
            "provided_identity_id",
            "system_legitimate_interests",
            name="last_served_identity_system_leg_interests",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "system_consent",
            name="last_served_fides_user_device_identity_system_consent",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "system_legitimate_interests",
            name="last_served_fides_user_device_identity_system_leg_interests",
        ),
        UniqueConstraint(
            "provided_identity_id",
            "special_feature",
            name="last_served_identity_special_feature",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "special_feature",
            name="last_served_fides_user_device_identity_special_feature",
        ),
    )

    # Relationships
    served_notice_history = relationship(
        ServedNoticeHistory, cascade="delete, delete-orphan", single_parent=True
    )
