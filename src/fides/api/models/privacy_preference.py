# pylint: disable=R0401, C0302, W0143

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, Tuple, Type, Union

from sqlalchemy import ARRAY, Boolean, Column, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Session, relationship
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesGcmEngine

from fides.api.common_exceptions import (
    IdentityNotFoundException,
    PrivacyNoticeHistoryNotFound,
)
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
from fides.config import CONFIG


class RequestOrigin(Enum):
    privacy_center = "privacy_center"
    overlay = "overlay"
    api = "api"


class ConsentMethod(Enum):
    button = "button"
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
            nullable=True,
            index=True,
        )

    # The specific experience under which the user was presented the relevant notice
    # Minimal information stored here, mostly just region and component type
    @declared_attr
    def privacy_experience_id(cls) -> Column:
        return Column(
            String, ForeignKey("privacyexperience.id"), nullable=True, index=True
        )

    # The specific historical record the user consented to
    @declared_attr
    def privacy_notice_history_id(cls) -> Column:
        return Column(
            String, ForeignKey(PrivacyNoticeHistory.id), nullable=False, index=True
        )

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


def _validate_notice_and_identity(
    db: Session, data: dict[str, Any]
) -> PrivacyNoticeHistory:
    """Validates that the PrivacyNoticeHistory specified in the data dictionary
    exists and that at least one provided identity type is supplied in the data

    Shares some common checks we run before saving PrivacyPreferenceHistory
    or ServedPreferenceHistory
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

    return privacy_notice_history


class ServedNoticeHistory(ConsentReportingMixin, Base):
    """A historical record of every time a notice was served in the UI to an end user"""

    acknowledge_mode = Column(
        Boolean,
        default=False,
    )
    serving_component = Column(EnumColumn(ServingComponent), nullable=False, index=True)

    last_served_notice = (
        relationship(  # Only exists if this is the same as the Last Served Notice
            "LastServedNotice",
            back_populates="served_notice_history",
            cascade="all, delete",
            uselist=False,
        )
    )

    @classmethod
    def create(
        cls: Type[ServedNoticeHistory],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> ServedNoticeHistory:
        """Method that creates a ServedNoticeHistory record and upserts a LastServedNotice record.

        The only difference between this and ServedNoticeHistory.save_notice_served_and_last_notice_served
        is the response.
        """
        history, _ = cls.save_notice_served_and_last_notice_served(
            db, data=data, check_name=check_name
        )
        return history

    @classmethod
    def save_notice_served_and_last_notice_served(
        cls: Type[ServedNoticeHistory],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> Tuple[ServedNoticeHistory, LastServedNotice]:
        """Create a ServedNoticeHistory record and then upsert the LastServedNotice record.

        If separate LastServedNotice records exist for both a verified provided identity and a fides user device
        id provided identity, consolidate when the notice was last served into a single record.

        There is only one LastServedNotice for each PrivacyNotice/ProvidedIdentity.
        """
        privacy_notice_history = _validate_notice_and_identity(db, data)

        created_served_notice_history = super().create(
            db=db, data=data, check_name=check_name
        )

        last_served_data = {
            "provided_identity_id": created_served_notice_history.provided_identity_id,
            "privacy_notice_id": privacy_notice_history.privacy_notice_id,
            "privacy_notice_history_id": privacy_notice_history.id,
            "served_notice_history_id": created_served_notice_history.id,
            "fides_user_device_provided_identity_id": created_served_notice_history.fides_user_device_provided_identity_id,
        }

        upserted_last_served_notice_record = upsert_last_saved_record(
            db,
            created_historical_record=created_served_notice_history,
            current_record_class=LastServedNotice,
            privacy_notice_history=privacy_notice_history,
            current_record_data=last_served_data,
        )
        assert isinstance(
            upserted_last_served_notice_record, LastServedNotice
        )  # For mypy

        return created_served_notice_history, upserted_last_served_notice_record


class PrivacyPreferenceHistory(ConsentReportingMixin, Base):
    """The DB ORM model for storing PrivacyPreferenceHistory, used for saving
    every time consent preferences are saved for reporting purposes.
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
        """Method that creates a PrivacyPreferenceRecord and upserts a CurrentPrivacyPreference record.

        The only difference between this and PrivacyPreference.create_history_and_upsert_current_preference
        is the response.
        """
        history, _ = cls.create_history_and_upsert_current_preference(
            db, data=data, check_name=check_name
        )
        return history

    @classmethod
    def create_history_and_upsert_current_preference(
        cls: Type[PrivacyPreferenceHistory],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> Tuple[PrivacyPreferenceHistory, CurrentPrivacyPreference]:
        """Create a PrivacyPreferenceHistory record and then upsert the CurrentPrivacyPreference record.
        If separate CurrentPrivacyPreferences exist for both a verified provided identity and a fides user device
        id provided identity, consolidate these "current" preferences into a single record.

        There is only one CurrentPrivacyPreference for each PrivacyNotice/ProvidedIdentity.
        """
        privacy_notice_history = _validate_notice_and_identity(db, data)

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

        current_preference = upsert_last_saved_record(
            db,
            created_historical_record=created_privacy_preference_history,
            current_record_class=CurrentPrivacyPreference,
            privacy_notice_history=privacy_notice_history,
            current_record_data=current_privacy_preference_data,
        )
        assert isinstance(current_preference, CurrentPrivacyPreference)  # For mypy

        return created_privacy_preference_history, current_preference


class LastSavedMixin:
    """Stores common fields for the last saved preference or last served notice"""

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )

    @declared_attr
    def provided_identity_id(cls) -> Column:
        return Column(String, ForeignKey(ProvidedIdentity.id), index=True)

    @declared_attr
    def fides_user_device_provided_identity_id(cls) -> Column:
        return Column(String, ForeignKey(ProvidedIdentity.id), index=True)

    @declared_attr
    def privacy_notice_id(cls) -> Column:
        return Column(String, ForeignKey(PrivacyNotice.id), nullable=False, index=True)

    @declared_attr
    def privacy_notice_history_id(cls) -> Column:
        return Column(
            String, ForeignKey(PrivacyNoticeHistory.id), nullable=False, index=True
        )

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
    )

    # Relationships
    privacy_preference_history = relationship(
        PrivacyPreferenceHistory, cascade="delete, delete-orphan", single_parent=True
    )

    @property
    def preference_matches_latest_version(self) -> bool:
        """Returns True if the latest saved preference corresponds to the
        latest version for this Notice"""
        return (
            self.privacy_notice.privacy_notice_history_id
            == self.privacy_notice_history_id
        )

    @classmethod
    def get_preference_for_notice_and_fides_user_device(
        cls,
        db: Session,
        fides_user_provided_identity: ProvidedIdentity,
        privacy_notice: PrivacyNotice,
    ) -> Optional[CurrentPrivacyPreference]:
        """Retrieves the CurrentPrivacyPreference for the user with the given identity
        for the given notice"""
        return (
            db.query(CurrentPrivacyPreference)
            .filter(
                CurrentPrivacyPreference.fides_user_device_provided_identity_id
                == fides_user_provided_identity.id,
                CurrentPrivacyPreference.privacy_notice_id == privacy_notice.id,
            )
            .first()
        )


class LastServedNotice(LastSavedMixin, Base):
    """Stores the last time a notice was served for a given user

    Also consolidates serving notices among various user identities.
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
    )

    # Relationships
    served_notice_history = relationship(
        ServedNoticeHistory, cascade="delete, delete-orphan", single_parent=True
    )

    @property
    def served_latest_version(self) -> bool:
        """Returns True if the user was last served the latest version of this Notice"""
        return (
            self.privacy_notice.privacy_notice_history_id
            == self.privacy_notice_history_id
        )

    @classmethod
    def get_last_served_for_notice_and_fides_user_device(
        cls,
        db: Session,
        fides_user_provided_identity: ProvidedIdentity,
        privacy_notice: PrivacyNotice,
    ) -> Optional[LastServedNotice]:
        """Retrieves the LastServedNotice record for the user with the given identity
        for the given notice"""
        return (
            db.query(LastServedNotice)
            .filter(
                LastServedNotice.fides_user_device_provided_identity_id
                == fides_user_provided_identity.id,
                LastServedNotice.privacy_notice_id == privacy_notice.id,
            )
            .first()
        )


def upsert_last_saved_record(
    db: Session,
    created_historical_record: Union[PrivacyPreferenceHistory, ServedNoticeHistory],
    current_record_class: Union[Type[CurrentPrivacyPreference], Type[LastServedNotice]],
    privacy_notice_history: PrivacyNoticeHistory,
    current_record_data: Dict[str, str],
) -> Union[CurrentPrivacyPreference, LastServedNotice]:
    """
    Upserts our record of when a user was served consent or when the last saved their preferences for a given notice.

    After we save historical records, this method is called to update a separate table that stores just our most
    recently saved record.

    If we have historical records for multiple identities, and we determine they are the same identity,
    their preferences are consolidated into the same record.
    """
    existing_record_for_provided_identity: Optional[
        Union[CurrentPrivacyPreference, LastServedNotice]
    ] = None
    # Check if we have "current" records for the ProvidedIdentity (usu an email or phone)/Privacy Notice
    if created_historical_record.provided_identity_id:
        existing_record_for_provided_identity = (
            db.query(current_record_class)  # type: ignore[assignment]
            .filter(
                current_record_class.provided_identity_id
                == created_historical_record.provided_identity_id,
                current_record_class.privacy_notice_id
                == privacy_notice_history.privacy_notice_id,
            )
            .first()
        )

    # Check if we have "current" records for the Fides User Device ID and the Privacy Notice
    existing_record_for_fides_user_device: Optional[
        Union[CurrentPrivacyPreference, LastServedNotice]
    ] = None
    if created_historical_record.fides_user_device_provided_identity_id:
        existing_record_for_fides_user_device = (
            db.query(current_record_class)  # type: ignore[assignment]
            .filter(
                current_record_class.fides_user_device_provided_identity_id
                == created_historical_record.fides_user_device_provided_identity_id,
                current_record_class.privacy_notice_id
                == privacy_notice_history.privacy_notice_id,
            )
            .first()
        )

    if (
        existing_record_for_provided_identity
        and existing_record_for_fides_user_device
        and existing_record_for_provided_identity
        != existing_record_for_fides_user_device
    ):
        # If both exist and were saved separately, let's delete one so we can consolidate.
        # Let's consider these identities as belonging to the same user.
        existing_record_for_fides_user_device.delete(db)

    current_record: Optional[Union[CurrentPrivacyPreference, LastServedNotice]] = (
        existing_record_for_provided_identity or existing_record_for_fides_user_device
    )
    if current_record:
        current_record.update(db=db, data=current_record_data)
    else:
        current_record = current_record_class.create(
            db=db, data=current_record_data, check_name=False
        )

    return current_record
