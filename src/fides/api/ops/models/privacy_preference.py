# pylint: disable=R0401, C0302

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Type

from sqlalchemy import ARRAY, Column, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Session, relationship
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesGcmEngine

from fides.api.ops.common_exceptions import (
    IdentityNotFoundException,
    PrivacyNoticeHistoryNotFound,
)
from fides.api.ops.db.base_class import JSONTypeOverride
from fides.api.ops.models.privacy_notice import (
    PrivacyNotice,
    PrivacyNoticeHistory,
    PrivacyNoticeRegion,
)
from fides.api.ops.models.privacy_request import (
    ExecutionLogStatus,
    PrivacyRequest,
    ProvidedIdentity,
)
from fides.core.config import CONFIG
from fides.lib.db.base import Base  # type: ignore[attr-defined]


class UserConsentPreference(Enum):
    opt_in = "opt_in"  # The user wants to opt in to the notice
    opt_out = "opt_out"  # The user wants to opt out of the notice
    acknowledge = "acknowledge"  # The user has acknowledged this notice


class RequestOrigin(Enum):
    privacy_center = "privacy_center"
    overlay = "overlay"
    api = "api"


class PrivacyPreferenceHistory(Base):
    """The DB ORM model for storing PrivacyPreferenceHistory, used for saving
    every time consent preferences are saved for reporting purposes.
    """

    # Systems capable of propagating their consent, and their status.  If the preference is
    # not relevant for the system, or we couldn't propagate a preference, the status is skipped
    affected_system_status = Column(
        MutableDict.as_mutable(JSONB), server_default="{}", default=dict
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
    fides_user_device_provided_identity_id = Column(
        String, ForeignKey(ProvidedIdentity.id), index=True
    )
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
    # Whether the user wants to opt in, opt out, or has acknowledged the notice
    preference = Column(EnumColumn(UserConsentPreference), nullable=False, index=True)
    # The specific historical record the user consented to
    privacy_notice_history_id = Column(
        String, ForeignKey(PrivacyNoticeHistory.id), nullable=False, index=True
    )
    # The privacy request created to propage the preferences
    privacy_request_id = Column(
        String, ForeignKey(PrivacyRequest.id, ondelete="SET NULL"), index=True
    )
    # Optional FK to a verified provided identity (like email or phone), if applicable
    provided_identity_id = Column(String, ForeignKey(ProvidedIdentity.id), index=True)

    # Systems whose data use match.  This doesn't necessarily mean we propagate. Some may be intentionally skipped later.
    relevant_systems = Column(MutableList.as_mutable(ARRAY(String)))
    # Location where we received the request
    request_origin = Column(EnumColumn(RequestOrigin))
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

    url_recorded = Column(String)
    user_agent = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )

    user_geography = Column(EnumColumn(PrivacyNoticeRegion), index=True)

    # Relationships
    privacy_notice_history = relationship(PrivacyNoticeHistory)
    privacy_request = relationship(PrivacyRequest, backref="privacy_preferences")
    provided_identity = relationship(
        ProvidedIdentity, foreign_keys=[provided_identity_id]
    )
    fides_user_device_provided_identity = relationship(
        ProvidedIdentity, foreign_keys=[fides_user_device_provided_identity_id]
    )
    current_privacy_preference = relationship(  # Only exists if this is the same as the Current Privacy Preference
        "CurrentPrivacyPreference",
        back_populates="privacy_preference_history",
        cascade="all, delete",
        uselist=False,
    )

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

    @classmethod
    def create(
        cls: Type[PrivacyPreferenceHistory],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> PrivacyPreferenceHistory:
        """Create a PrivacyPreferenceHistory record and then upsert the CurrentPrivacyPreference record.
        If separate CurrentPrivacyPreferences exist for both a verified provided identity and a fides user device
        id provided identity, consolidate these "current" preferences into a single record.

        There is only one CurrentPrivacyPreference for each PrivacyNotice/ProvidedIdentity.
        """
        privacy_notice_history = PrivacyNoticeHistory.get(
            db=db, object_id=data.get("privacy_notice_history_id")
        )
        if not privacy_notice_history:
            raise PrivacyNoticeHistoryNotFound()

        if not data.get("provided_identity_id") and not data.get(
            "fides_user_device_provided_identity_id"
        ):
            raise IdentityNotFoundException(
                "Must supply a verified provided identity id or a fides_user_device_provided_identity_id"
            )

        data["relevant_systems"] = privacy_notice_history.calculate_relevant_systems(db)
        created_privacy_preference_history = super().create(
            db=db, data=data, check_name=check_name
        )

        current_privacy_preference_data = {
            "preference": created_privacy_preference_history.preference,
            "provided_identity_id": created_privacy_preference_history.provided_identity_id,
            "privacy_notice_id": privacy_notice_history.privacy_notice_id,
            "privacy_notice_history_id": privacy_notice_history.id,
            "privacy_preference_history_id": created_privacy_preference_history.id,
            "fides_user_device_provided_identity_id": created_privacy_preference_history.fides_user_device_provided_identity_id,
        }

        existing_current_preference_on_provided_identity = None
        # Check if there are Current Privacy Preferences saved against the ProvidedIdentity
        if created_privacy_preference_history.provided_identity_id:
            existing_current_preference_on_provided_identity = (
                db.query(CurrentPrivacyPreference)
                .filter(
                    CurrentPrivacyPreference.provided_identity_id
                    == created_privacy_preference_history.provided_identity_id,
                    CurrentPrivacyPreference.privacy_notice_id
                    == privacy_notice_history.privacy_notice_id,
                )
                .first()
            )

        # Check if there are Current Privacy Preferences saved against the Fides User Device Id Provided Identity
        existing_current_preference_on_fides_user_device_provided_identity = None
        if created_privacy_preference_history.fides_user_device_provided_identity_id:
            existing_current_preference_on_fides_user_device_provided_identity = (
                db.query(CurrentPrivacyPreference)
                .filter(
                    CurrentPrivacyPreference.fides_user_device_provided_identity_id
                    == created_privacy_preference_history.fides_user_device_provided_identity_id,
                    CurrentPrivacyPreference.privacy_notice_id
                    == privacy_notice_history.privacy_notice_id,
                )
                .first()
            )

        if (
            existing_current_preference_on_provided_identity
            and existing_current_preference_on_fides_user_device_provided_identity
            and existing_current_preference_on_provided_identity
            != existing_current_preference_on_fides_user_device_provided_identity
        ):
            # If both exist and were saved separately, let's delete one so we can consolidate.
            # Let's consider these identities as belonging to the same user, and can save their current preferences together.
            existing_current_preference_on_fides_user_device_provided_identity.delete(
                db
            )

        if existing_current_preference_on_provided_identity:
            existing_current_preference_on_provided_identity.update(
                db=db, data=current_privacy_preference_data
            )
        else:
            CurrentPrivacyPreference.create(
                db=db, data=current_privacy_preference_data, check_name=False
            )

        return created_privacy_preference_history


class CurrentPrivacyPreference(Base):
    """Stores only the user's most recently saved preference for a given privacy notice

    The specific privacy notice history and privacy preference history record are linked as well.
    """

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )
    preference = Column(EnumColumn(UserConsentPreference), nullable=False, index=True)
    provided_identity_id = Column(String, ForeignKey(ProvidedIdentity.id), index=True)
    fides_user_device_provided_identity_id = Column(
        String, ForeignKey(ProvidedIdentity.id), index=True
    )
    privacy_notice_id = Column(
        String, ForeignKey(PrivacyNotice.id), nullable=False, index=True
    )
    privacy_notice_history_id = Column(
        String, ForeignKey(PrivacyNoticeHistory.id), nullable=False, index=True
    )
    privacy_preference_history_id = Column(
        String, ForeignKey(PrivacyPreferenceHistory.id), nullable=False, index=True
    )

    UniqueConstraint(
        provided_identity_id, privacy_notice_id, name="identity_privacy_notice"
    )

    UniqueConstraint(
        fides_user_device_provided_identity_id,
        privacy_notice_id,
        name="fides_user_device_identity_privacy_notice",
    )

    # Relationships
    privacy_notice_history = relationship(PrivacyNoticeHistory)
    privacy_preference_history = relationship(
        PrivacyPreferenceHistory, cascade="delete, delete-orphan", single_parent=True
    )
    provided_identity = relationship(
        ProvidedIdentity, foreign_keys=[provided_identity_id]
    )
    fides_user_device_provided_identity = relationship(
        ProvidedIdentity, foreign_keys=[fides_user_device_provided_identity_id]
    )
