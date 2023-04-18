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

from fides.api.ops.common_exceptions import PrivacyNoticeHistoryNotFound
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

    affected_system_status = Column(
        MutableDict.as_mutable(JSONB), server_default="{}", default=dict
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    email = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )
    hashed_email = Column(String, index=True)  # For filtering
    hashed_phone_number = Column(String, index=True)  # For filtering
    phone_number = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )
    preference = Column(EnumColumn(UserConsentPreference), nullable=False, index=True)
    privacy_notice_history_id = Column(
        String, ForeignKey(PrivacyNoticeHistory.id), nullable=False, index=True
    )
    privacy_request_id = Column(
        String, ForeignKey(PrivacyRequest.id, ondelete="SET NULL"), index=True
    )
    provided_identity_id = Column(String, ForeignKey(ProvidedIdentity.id), index=True)
    relevant_systems = Column(
        MutableList.as_mutable(ARRAY(String))
    )  # Systems whose data use match.  This doesn't necessarily mean we propagate. Some may be intentionally skipped later.
    request_origin = Column(EnumColumn(RequestOrigin))
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
    provided_identity = relationship(ProvidedIdentity)
    current_privacy_preference = relationship(  # Only exists if this is the same as the Current Privacy Preference
        "CurrentPrivacyPreference",
        back_populates="privacy_preference_history",
        cascade="all, delete",
        uselist=False,
    )

    def cache_system_status(self, system: str, status: ExecutionLogStatus) -> None:
        """Update the cached affected system status for consent reporting

        Typically this should just be called for consent connectors only.
        If no request is made or email is sent, this should be called with a status of skipped.
        """
        db = Session.object_session(self)
        if not self.affected_system_status:
            self.affected_system_status = {}
        self.affected_system_status[system] = status.value
        self.save(db)

    def update_secondary_user_ids(self, new_identities: Dict[str, Any]) -> None:
        """Update secondary user identities for consent reporting

        The intent is to only put identities here that we intend to send to third party systems.
        """
        secondary_user_ids = self.secondary_user_ids or {}
        secondary_user_ids.update(new_identities)
        db = Session.object_session(self)
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

        There is only one CurrentPrivacyPreference for each PrivacyNotice/ProvidedIdentity.
        """
        privacy_notice_history = PrivacyNoticeHistory.get(
            db=db, object_id=data.get("privacy_notice_history_id")
        )
        if not privacy_notice_history:
            raise PrivacyNoticeHistoryNotFound()

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
        }

        existing_current_preference = (
            db.query(CurrentPrivacyPreference)
            .filter(
                CurrentPrivacyPreference.provided_identity_id
                == created_privacy_preference_history.provided_identity_id,
                CurrentPrivacyPreference.privacy_notice_id
                == privacy_notice_history.privacy_notice_id,
            )
            .first()
        )

        if existing_current_preference:
            existing_current_preference.update(
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
    preference = Column(EnumColumn(UserConsentPreference), nullable=False, index=True)
    provided_identity_id = Column(String, ForeignKey(ProvidedIdentity.id), index=True)
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

    # Relationships
    privacy_notice_history = relationship(PrivacyNoticeHistory)
    privacy_preference_history = relationship(
        PrivacyPreferenceHistory, cascade="delete, delete-orphan", single_parent=True
    )
