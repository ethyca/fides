# pylint: disable=R0401, C0302, W0143

from __future__ import annotations

from enum import Enum

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base
from fides.api.models.privacy_notice import (
    PrivacyNotice,
    PrivacyNoticeHistory,
    UserConsentPreference,
)
from fides.api.models.privacy_request import ProvidedIdentity


class RequestOrigin(Enum):
    # Not at the db level due to being subject to change.
    # Only add here, do not remove
    privacy_center = "privacy_center"
    overlay = "overlay"
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


class ServingComponent(Enum):
    # Not at the db level due to being subject to change.
    # Only add here, do not remove
    overlay = "overlay"
    banner = "banner"
    privacy_center = "privacy_center"
    tcf_overlay = "tcf_overlay"
    tcf_banner = "tcf_banner"


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


class DeprecatedCurrentPrivacyPreference(LastSavedMixin, Base):
    """
    ***DEPRECATED*** in favor of CurrentPrivacyPreference. Soon to be removed.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "currentprivacypreference"

    preference = Column(EnumColumn(UserConsentPreference), nullable=False, index=True)

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


class DeprecatedLastServedNotice(LastSavedMixin, Base):
    """
    ***DEPRECATED*** in favor of LastServedNoticeV2. Soon to be removed.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "lastservednotice"

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
