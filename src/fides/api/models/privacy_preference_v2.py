from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Query, Session, relationship
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesGcmEngine

from fides.api.db.base_class import Base, JSONTypeOverride
from fides.api.models.privacy_notice import PrivacyNoticeHistory, UserConsentPreference
from fides.api.models.privacy_preference import (
    ConsentMethod,
    RequestOrigin,
    ServingComponent,
)
from fides.api.models.privacy_request import (
    ExecutionLogStatus,
    PrivacyRequest,
    ProvidedIdentity,
)
from fides.config import CONFIG


class ConsentIdentitiesMixin:
    """Encrypted and hashed identities for consent reporting and last saved preference retrieval"""

    email = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )  # Encrypted email; bytea in the db

    fides_user_device = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )  # Encrypted fides user device; type bytea in the db

    phone_number = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )  # Encrypted phone number; type bytea in the db

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
    def hash_value(
        cls,
        value: Optional[str],
        encoding: str = "UTF-8",
    ) -> Optional[str]:
        """Utility function to hash the value with a generated salt
        This returns None if there's no value, unlike ProvidedIdentity.hash_value
        """
        if not value:
            return None

        return ProvidedIdentity.hash_value(value, encoding)


class CurrentPrivacyPreferenceV2(ConsentIdentitiesMixin, Base):
    """Stores the latest saved privacy preferences for a given user"""

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    preferences = Column(
        MutableDict.as_mutable(JSONB)
    )  # All saved preferences against Privacy Notices and TCF Notices

    fides_string = Column(String)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "email",
            name="last_saved_for_email",
        ),
        UniqueConstraint(
            "phone_number",
            name="last_saved_for_phone_number",
        ),
        UniqueConstraint(
            "fides_user_device",
            name="last_saved_for_fides_user_device",
        ),
    )


class LastServedNoticeV2(ConsentIdentitiesMixin, Base):
    """Stores the latest served notices for a given user"""

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

    @classmethod
    def generate_served_notice_history_id(cls) -> str:
        """Generate a served notice history id

        We save privacy preferences and return immediately alongside this generated
        id that we build up front.
        """
        return f"ser_{uuid.uuid4()}"


class ConsentReportingMixinV2(ConsentIdentitiesMixin):
    """Consent Reporting Mixin to share between historical records saved and
    historical records served
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

    notice_name = Column(String, index=True)  # Privacy Notice name or "TCF"

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

    # Location where we received the request
    request_origin = Column(EnumColumn(RequestOrigin))

    url_recorded = Column(String)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )

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


class ServedNoticeHistoryV2(ConsentReportingMixinV2, Base):
    """A Historical Record of every time a Notice was served to a user"""

    acknowledge_mode = Column(
        Boolean,
        default=False,
    )

    serving_component = Column(EnumColumn(ServingComponent), nullable=True, index=True)

    # Identifier generated when a LastServedNoticeV2 is created and returned in the response.
    # This is saved on all corresponding ServedNoticeHistory records and can be used to link PrivacyPreferenceHistory records.
    served_notice_history_id = Column(String, index=True)

    tcf_served = Column(
        MutableDict.as_mutable(JSONB)
    )  # Dict of all the TCF attributes served if applicable

    @staticmethod
    def get_by_served_id(db: Session, served_id: str) -> Query:
        """Retrieves all ServedNoticeHistoryV2 records with a common served_notice_history_id - generated
        before the task was queued to store these records
        """
        return db.query(ServedNoticeHistoryV2).filter(
            ServedNoticeHistoryV2.served_notice_history_id == served_id
        )


class PrivacyPreferenceHistoryV2(ConsentReportingMixinV2, Base):
    """A Historical Record of every time a Notice was saved for a user"""

    # Systems capable of propagating their consent, and their status.  If the preference is
    # not relevant for the system, or we couldn't propagate a preference, the status is skipped
    affected_system_status = Column(
        MutableDict.as_mutable(JSONB), server_default="{}", default=dict
    )

    # Optional, if fides_string was supplied directly
    fides_string = Column(String)

    # Accept, reject, etc. especially useful for TCF because there is no overall "preference"
    method = Column(EnumColumn(ConsentMethod))

    # Whether the user wants to opt in, opt out, or has acknowledged the notice.
    # Only for non-TCF notices.
    preference = Column(EnumColumn(UserConsentPreference), index=True)

    # The privacy request created to propagate the preferences
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
    )  # Cache secondary user ids (cookies, etc) if known for reporting purposes.

    # The record of where we served the notice in the frontend, for conversion purposes.
    served_notice_history_id = Column(String, index=True)

    tcf_preferences = Column(
        MutableDict.as_mutable(JSONB)
    )  # Dict of TCF attributes saved, for a TCF notice

    privacy_request = relationship(PrivacyRequest, backref="privacy_preferences_v2")

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
