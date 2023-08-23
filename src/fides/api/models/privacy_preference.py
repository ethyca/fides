# pylint: disable=R0401, C0302, W0143

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from fideslang.gvl import (
    GVL_FEATURES,
    GVL_SPECIAL_FEATURES,
    feature_id_to_feature_name,
    purpose_to_data_use,
)
from fideslang.validation import FidesKey
from sqlalchemy import ARRAY, Boolean, Column, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Session, relationship
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesGcmEngine

from fides.api.common_exceptions import (
    ConsentHistorySaveError,
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
from fides.api.models.sql_models import (  # type:ignore[attr-defined]
    PrivacyDeclaration,
    System,
)
from fides.config import CONFIG

CURRENT_TCF_VERSION = "2.2"


class RequestOrigin(Enum):
    privacy_center = "privacy_center"
    overlay = "overlay"
    api = "api"
    tcf_overlay = "tcf_overlay"


class ConsentMethod(Enum):
    button = "button"
    gpc = "gpc"
    individual_notice = "individual_notice"


class TCFComponentType(Enum):
    """A particular element of the TCF form"""

    purpose = "purpose"
    special_purpose = "special_purpose"
    vendor = "vendor"
    system_fides_key = "system_fides_key"
    feature = "feature"
    special_feature = "special_feature"


class ConsentRecordType(Enum):
    """All of the relevant consent items that can be served or have preferences saved against"""

    privacy_notice_id = "privacy_notice_id"
    privacy_notice_history_id = "privacy_notice_history_id"
    purpose = "purpose"
    special_purpose = "special_purpose"
    vendor = "vendor"
    system_fides_key = "system_fides_key"
    feature = "feature"
    special_feature = "special_feature"


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

    @declared_attr
    def privacy_notice_history_id(cls) -> Column:
        """
        The specific historical record the user consented to - applicable when
        saving preferences with respect to a privacy notice directly
        """
        return Column(
            String, ForeignKey(PrivacyNoticeHistory.id), nullable=True, index=True
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

    # ==== TCF Attributes against which preferences can be saved ==== #
    feature = Column(
        Integer, index=True
    )  # When saving privacy preferences with respect to a TCF feature directly
    purpose = Column(
        Integer, index=True
    )  # When saving privacy preferences with respect to a TCF purpose directly
    special_feature = Column(
        Integer, index=True
    )  # When saving privacy preferences with respect to a TCF special feature directly
    special_purpose = Column(
        Integer, index=True
    )  # When saving privacy preferences with respect to a TCF special purpose directly
    vendor = Column(
        String, index=True
    )  # When saving privacy preferences with respect to a vendor directly. Vendors can apply to multiple systems.
    system_fides_key = Column(
        String, index=True
    )  # When saving privacy preferences with respect to a system directly, in the case where the vendor is unknown

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

    @property
    def consent_record_type(self) -> ConsentRecordType:
        """Determine the type of record for which a preference was saved
        or served against based on which field exists"""
        if self.privacy_notice_history_id:
            return ConsentRecordType.privacy_notice_id
        if self.purpose:
            return ConsentRecordType.purpose
        if self.special_purpose:
            return ConsentRecordType.special_purpose
        if self.vendor:
            return ConsentRecordType.vendor
        if self.system_fides_key:
            return ConsentRecordType.system_fides_key
        if self.special_feature:
            return ConsentRecordType.special_feature
        return ConsentRecordType.feature


class ServingComponent(Enum):
    overlay = "overlay"
    banner = "banner"
    privacy_center = "privacy_center"
    tcf_overlay = "tcf_overlay"


def _validate_before_saving_consent_history(
    db: Session, data: dict[str, Any]
) -> Tuple[
    Optional[PrivacyNoticeHistory], Optional[str], Union[Optional[str], Optional[int]]
]:
    """
    Runs some final validation checks before saving that a user was *served*
    consent components or they *saved* consent preferences

    - Validates that a notice history exists if supplied
    - Validates that at least one provided identity type is supplied
    - Validates that only one of a data use, special purpose, vendor, system_id, feature or special
    feature exists in request body
    """
    privacy_notice_history = None
    if data.get("privacy_notice_history_id"):
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

    tcf_attributes: Dict[str, Union[Optional[str], Optional[int]]] = {
        tcf_key: data[tcf_key]
        for tcf_key in data.keys() & TCFComponentType.__members__.keys()
        if data[tcf_key]
    }

    def only_one_value_supplied(values: List) -> bool:
        """Readability helper to ensure only one type of consent preference is being saved here"""
        return sum(item is not None for item in values) == 1

    if not only_one_value_supplied(
        [privacy_notice_history] + list(tcf_attributes.values())
    ):
        raise ConsentHistorySaveError(
            "Can only save record against a single privacy notice or TCF attribute"
        )

    tcf_key: Optional[str] = list(tcf_attributes.keys())[0] if tcf_attributes else None
    tcf_val: Optional[Union[str, int]] = (
        list(tcf_attributes.values())[0] if tcf_attributes else None
    )

    return privacy_notice_history, tcf_key, tcf_val


class ServedNoticeHistory(ConsentReportingMixin, Base):
    """A historical record of every time a resource was served in the UI to which an end user could consent

    This might be a privacy notice, a data use, a vendor, a system_id, or a feature.
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
        history, _ = cls.save_served_notice_history_and_last_notice_served(
            db, data=data, check_name=check_name
        )
        return history

    @classmethod
    def save_served_notice_history_and_last_notice_served(
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
        (
            privacy_notice_history,
            tcf_field,
            tcf_val,
        ) = _validate_before_saving_consent_history(db, data)

        if tcf_field:
            data["tcf_version"] = CURRENT_TCF_VERSION

        created_served_notice_history = super().create(
            db=db, data=data, check_name=check_name
        )

        last_served_data = {
            "provided_identity_id": created_served_notice_history.provided_identity_id,
            "served_notice_history_id": created_served_notice_history.id,
            "fides_user_device_provided_identity_id": created_served_notice_history.fides_user_device_provided_identity_id,
        }

        if privacy_notice_history:
            last_served_data["privacy_notice_history_id"] = privacy_notice_history.id
            last_served_data[
                "privacy_notice_id"
            ] = privacy_notice_history.privacy_notice_id

        if tcf_field:
            last_served_data[tcf_field] = tcf_val
            last_served_data["tcf_version"] = CURRENT_TCF_VERSION

        upserted_last_served_notice_record = upsert_last_saved_record(
            db,
            created_historical_record=created_served_notice_history,
            current_record_class=LastServedNotice,
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

    @classmethod
    def determine_relevant_systems(
        cls,
        db: Session,
        privacy_notice_history: Optional[PrivacyNoticeHistory] = None,
        tcf_field: Optional[str] = None,
        tcf_value: Union[Optional[int], Optional[str]] = None,
    ) -> List[FidesKey]:
        """Used to take a snapshot of relevant systems before saving privacy preferences.

        TODO: TCF Add in feature and special feature support for calculating relevant systems
        """
        if privacy_notice_history:
            return privacy_notice_history.calculate_relevant_systems(db)

        if tcf_field == TCFComponentType.purpose.value:
            purpose_data_uses: List[str] = purpose_to_data_use(tcf_value)  # type: ignore[arg-type]
            return systems_that_match_tcf_data_uses(db, purpose_data_uses)

        if tcf_field == TCFComponentType.special_purpose.value:
            special_purpose_data_uses: List[str] = purpose_to_data_use(
                tcf_value, special_purpose=True  # type: ignore[arg-type]
            )
            return systems_that_match_tcf_data_uses(db, special_purpose_data_uses)

        if tcf_field == TCFComponentType.feature.value:
            return systems_that_match_tcf_feature(
                db, feature_id_to_feature_name(feature_id=tcf_value)
            )

        if tcf_field == TCFComponentType.special_feature.value:
            return systems_that_match_tcf_feature(
                db,
                feature_id_to_feature_name(feature_id=tcf_value, special_feature=True),
            )

        if tcf_field == TCFComponentType.vendor.value:
            return systems_that_match_vendor_string(db, tcf_value)

        if tcf_field == TCFComponentType.system_fides_key.value:
            return systems_that_match_fides_key(db, tcf_value)

        return []

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
        (
            privacy_notice_history,
            tcf_field,
            tcf_val,
        ) = _validate_before_saving_consent_history(db, data)

        # Take a snapshot of relevant systems and save
        data["relevant_systems"] = PrivacyPreferenceHistory.determine_relevant_systems(
            db,
            privacy_notice_history=privacy_notice_history,
            tcf_field=tcf_field,
            tcf_value=tcf_val,
        )

        if tcf_field:
            data["tcf_version"] = CURRENT_TCF_VERSION

        created_privacy_preference_history = super().create(
            db=db, data=data, check_name=check_name
        )

        current_privacy_preference_data = {
            "preference": created_privacy_preference_history.preference,
            "provided_identity_id": created_privacy_preference_history.provided_identity_id,
            "privacy_preference_history_id": created_privacy_preference_history.id,
            "fides_user_device_provided_identity_id": created_privacy_preference_history.fides_user_device_provided_identity_id,
        }
        if privacy_notice_history:
            current_privacy_preference_data[
                "privacy_notice_id"
            ] = privacy_notice_history.privacy_notice_id
            current_privacy_preference_data[
                "privacy_notice_history_id"
            ] = privacy_notice_history.id

        if tcf_field:
            current_privacy_preference_data[tcf_field] = tcf_val
            current_privacy_preference_data["tcf_version"] = CURRENT_TCF_VERSION

        current_preference = upsert_last_saved_record(
            db,
            created_historical_record=created_privacy_preference_history,
            current_record_class=CurrentPrivacyPreference,
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

    tcf_version = Column(String)

    # ==== TCF Attributes that can be served ==== #
    feature = Column(Integer, index=True)  # When a feature was served directly (TCF)

    purpose = Column(Integer, index=True)  # When a purpose was served directly (TCF)

    special_feature = Column(
        Integer, index=True
    )  # When a special feature was served directly (TCF)

    special_purpose = Column(
        Integer, index=True
    )  # When a special purpose was served directly (TCF)

    vendor = Column(
        String, index=True
    )  # When a vendor was served directly (TCF). Vendors can apply to multiple systems.

    system_fides_key = Column(
        String, index=True
    )  # When a system fides key was served directly (TCF). Used for when the specific vendor type is unknown.

    @declared_attr
    def provided_identity_id(cls) -> Column:
        return Column(String, ForeignKey(ProvidedIdentity.id), index=True)

    @declared_attr
    def fides_user_device_provided_identity_id(cls) -> Column:
        return Column(String, ForeignKey(ProvidedIdentity.id), index=True)

    @declared_attr
    def privacy_notice_id(cls) -> Column:
        """When saving a notice was served directly"""
        return Column(String, ForeignKey(PrivacyNotice.id), nullable=True, index=True)

    @declared_attr
    def privacy_notice_history_id(cls) -> Column:
        return Column(
            String, ForeignKey(PrivacyNoticeHistory.id), nullable=True, index=True
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

    @property
    def record_matches_latest_version(self) -> bool:
        """Returns True if the latest saved preference corresponds to the
        latest version for this notice or TCF standard"""

        if self.privacy_notice and self.privacy_notice_history_id:
            return (
                self.privacy_notice.privacy_notice_history_id
                == self.privacy_notice_history_id
            )

        if self.tcf_version:
            return self.tcf_version == CURRENT_TCF_VERSION

        return False


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
        UniqueConstraint("provided_identity_id", "purpose", name="identity_purpose"),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "purpose",
            name="fides_user_device_identity_purpose",
        ),
        UniqueConstraint(
            "provided_identity_id", "purpose", name="identity_special_purpose"
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "special_purpose",
            name="fides_user_device_identity_special_purpose",
        ),
        UniqueConstraint("provided_identity_id", "vendor", name="identity_vendor"),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "vendor",
            name="fides_user_device_identity_vendor",
        ),
        UniqueConstraint(
            "provided_identity_id", "system_fides_key", name="identity_system_fides_key"
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "system_fides_key",
            name="fides_user_device_identity_system_fides_key",
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

    @classmethod
    def get_preference_by_type_and_fides_user_device(
        cls,
        db: Session,
        fides_user_provided_identity: ProvidedIdentity,
        preference_type: ConsentRecordType,
        preference_value: Union[int, str],
    ) -> Optional[CurrentPrivacyPreference]:
        """Retrieves the CurrentPrivacyPreference saved against a notice, TCF purpose,
        TCF special purpose, TCF vendor, TCF feature, TCF special feature, or system fides key for a given fides user device id
        """

        return (
            db.query(CurrentPrivacyPreference)
            .filter(
                CurrentPrivacyPreference.fides_user_device_provided_identity_id
                == fides_user_provided_identity.id,
                CurrentPrivacyPreference.__table__.c[preference_type.value]
                == preference_value,
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
        UniqueConstraint(
            "provided_identity_id",
            "purpose",
            name="last_served_identity_purpose",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "purpose",
            name="last_served_fides_user_device_identity_purpose",
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
            "vendor",
            name="last_served_identity_vendor",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "vendor",
            name="last_served_fides_user_device_identity_vendor",
        ),
        UniqueConstraint(
            "provided_identity_id",
            "system_fides_key",
            name="last_served_identity_system_fides_key",
        ),
        UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "system_fides_key",
            name="last_served_fides_user_device_identity_system_fides_key",
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

    @classmethod
    def get_last_served_for_record_type_and_fides_user_device(
        cls,
        db: Session,
        fides_user_provided_identity: ProvidedIdentity,
        record_type: ConsentRecordType,
        preference_value: Union[str, int],
    ) -> Optional[LastServedNotice]:
        """Retrieves the CurrentPrivacyPreference for the user with the given identity
        and the served preference type/value"""
        return (
            db.query(LastServedNotice)
            .filter(
                LastServedNotice.fides_user_device_provided_identity_id
                == fides_user_provided_identity.id,
                LastServedNotice.__table__.c[record_type.value] == preference_value,
            )
            .first()
        )


def upsert_last_saved_record(
    db: Session,
    created_historical_record: Union[PrivacyPreferenceHistory, ServedNoticeHistory],
    current_record_class: Union[Type[CurrentPrivacyPreference], Type[LastServedNotice]],
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

    field_val = getattr(
        created_historical_record, created_historical_record.consent_record_type.value
    )

    # Check if we have "current" records for the ProvidedIdentity (usu an email or phone)/Privacy Notice
    if created_historical_record.provided_identity_id:
        existing_record_for_provided_identity = (
            db.query(current_record_class)  # type: ignore[assignment]
            .filter(
                current_record_class.provided_identity_id
                == created_historical_record.provided_identity_id,
                current_record_class.__table__.c[
                    created_historical_record.consent_record_type.value
                ]
                == field_val,
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
                current_record_class.__table__.c[
                    created_historical_record.consent_record_type.value
                ]
                == field_val,
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


def systems_that_match_tcf_data_uses(
    db: Session, data_uses: List[str]
) -> List[FidesKey]:
    """Check which systems have these data uses directly.

    This is used for determining relevant systems for TCF purposes and special purposes. Unlike
    determining relevant systems for Privacy Notices where we use a hierarchy-type matching,
    for TCF, we're looking for an exact match on data use."""
    if not data_uses:
        return []

    return [
        system.fides_key
        for system in (
            db.query(System.fides_key)
            .join(PrivacyDeclaration, System.id == PrivacyDeclaration.system_id)
            .filter(PrivacyDeclaration.data_use.in_(data_uses))
            .distinct(System.id)
        )
    ]


def systems_that_match_tcf_feature(db: Session, feature: str) -> List[FidesKey]:
    """Check which systems have these data uses directly.

    This is used for determining relevant systems for TCF features and special features. Unlike
    determining relevant systems for Privacy Notices where we use a hierarchy-type matching,
    for TCF, we're looking for an exact match on feature."""
    if not feature:
        return []

    return [
        system.fides_key
        for system in (
            db.query(System.fides_key)
            .join(PrivacyDeclaration, System.id == PrivacyDeclaration.system_id)
            .filter(PrivacyDeclaration.features.any(feature))
            .distinct(System.id)
        )
    ]


def systems_that_match_vendor_string(
    db: Session, vendor: Optional[str]
) -> List[FidesKey]:
    """Check which systems have this vendor associated with them. Unlike PrivacyNotices, where we use hierarchy-type matching,
    with TCF components, we are looking for exact matches.
    """
    if not vendor:
        return []
    return [
        system.fides_key
        for system in (
            db.query(System.fides_key)
            .filter(System.vendor_id == vendor)
            .distinct(System.id)
        )
    ]


def systems_that_match_fides_key(
    db: Session, system_fides_key: Optional[str]
) -> List[FidesKey]:
    """Returns the system fides key if it exists on the system"""
    if not system_fides_key:
        return []
    return [
        system.fides_key
        for system in (
            db.query(System.fides_key)
            .filter(System.fides_key == system_fides_key)
            .distinct(System.id)
        )
    ]
