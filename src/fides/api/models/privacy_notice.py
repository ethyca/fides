from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type

from fideslang.validation import FidesKey, validate_fides_key
from sqlalchemy import Boolean, Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import Float, ForeignKey, String, UniqueConstraint, or_, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import RelationshipProperty, Session, relationship
from sqlalchemy.orm.dynamic import AppenderQuery
from sqlalchemy.util import hybridproperty

from fides.api.db.base_class import Base, FidesBase
from fides.api.models import (
    create_historical_data_from_record,
    dry_update_data,
    update_if_modified,
)
from fides.api.models.asset import Asset
from fides.api.models.location_regulation_selections import DeprecatedNoticeRegion
from fides.api.models.sql_models import (  # type: ignore[attr-defined]
    System,
    get_system_data_uses,
)
from fides.api.schemas.language import SupportedLanguage


class PrivacyNoticeFramework(Enum):
    gpp_us_national = "gpp_us_national"
    gpp_us_state = "gpp_us_state"


class UserConsentPreference(Enum):
    opt_in = "opt_in"  # The user wants to opt in to the notice
    opt_out = "opt_out"  # The user wants to opt out of the notice
    acknowledge = "acknowledge"  # The user has acknowledged this notice
    tcf = "tcf"  # Overall preference set for TCF where there are numerous preferences under the single notice


class ConsentMechanism(Enum):
    """
    Enum is not formalized in the DB because it may be subject to frequent change
    """

    opt_in = "opt_in"
    opt_out = "opt_out"
    notice_only = "notice_only"


class EnforcementLevel(Enum):
    """
    Enum is not formalized in the DB because it may be subject to frequent change
    """

    frontend = "frontend"
    system_wide = "system_wide"
    not_applicable = "not_applicable"


class PrivacyNoticeBase:
    """
    This class contains the common fields between PrivacyNoticeTemplate, PrivacyNotice, and PrivacyNoticeHistory.
    These fields are not translated.
    """

    consent_mechanism = Column(EnumColumn(ConsentMechanism), nullable=False)
    data_uses = Column(
        ARRAY(String),
        nullable=False,
        server_default="{}",
        default=dict,
    )  # a list of `fides_key`s of `DataUse` records

    disabled = Column(Boolean, nullable=False, default=False)
    enforcement_level = Column(EnumColumn(EnforcementLevel), nullable=False)
    framework = Column(String)
    gpp_field_mapping = Column(MutableList.as_mutable(JSONB), index=False, unique=False)
    has_gpc_flag = Column(Boolean, nullable=False, default=False)
    internal_description = Column(String)  # Visible to internal users only
    name = Column(String, nullable=False)
    notice_key = Column(String, nullable=False)

    @property
    def is_gpp(self) -> bool:
        return self.framework in (
            PrivacyNoticeFramework.gpp_us_national.value,
            PrivacyNoticeFramework.gpp_us_state.value,
        )

    def applies_to_system(self, system: System) -> bool:
        """Privacy Notice applies to System if a data use matches or the Privacy Notice
        Data Use is a parent of a System Data Use
        """
        for system_data_use in System.get_data_uses([system], include_parents=True):
            for privacy_notice_data_use in self.data_uses or []:
                if system_data_use == privacy_notice_data_use:
                    return True
        return False

    @classmethod
    def generate_notice_key(cls, name: Optional[str]) -> FidesKey:
        """Generate a notice key from a notice name"""
        if not isinstance(name, str):
            raise Exception("Privacy notice keys must be generated from a string.")
        notice_key: str = re.sub(r"\s+", "_", name.lower().strip())
        return FidesKey(validate_fides_key(notice_key))


class PrivacyNoticeTemplate(PrivacyNoticeBase, Base):
    """
    This table contains the out-of-the-box Privacy Notice Templates that are shipped with Fides
    """

    # All out-of-the-box Notice Translations, stored as a list of JSON
    translations = Column(ARRAY(JSONB))

    def dry_update(self, *, data: dict[str, Any]) -> FidesBase:
        """
        A utility method to dry update the PrivacyNoticeTemplate

        This is used to see what an object update would look like, in memory,
        without actually persisting the update to the db
        """
        updated_attributes: Dict = dry_update_data(resource=self, data_updates=data)

        # create a new object with the updated attribute data to keep this
        # ORM object (i.e., `self`) pristine
        return PrivacyNoticeTemplate(**updated_attributes)


class PrivacyNotice(PrivacyNoticeBase, Base):
    """
    A notice set up by a system administrator that an end user (i.e., data subject)
    accepts or rejects to indicate their consent for particular data uses
    """

    id = Column(
        String(255), primary_key=True, index=True, default=FidesBase.generate_uuid
    )

    origin = Column(
        String,
        ForeignKey(PrivacyNoticeTemplate.id_field_path),
    )  # pointer back to the PrivacyNoticeTemplate

    translations: RelationshipProperty[List[NoticeTranslation]] = relationship(
        "NoticeTranslation",
        backref="privacy_notice",
        lazy="selectin",
        order_by="NoticeTranslation.created_at",
    )

    parent_id = Column(
        String,
        ForeignKey("privacynotice.id", ondelete="SET NULL"),
        nullable=True,
    )
    children: "RelationshipProperty[List[PrivacyNotice]]" = relationship(
        "PrivacyNotice",
        back_populates="parent",
        cascade="all",
        passive_deletes=True,
    )
    parent: "RelationshipProperty[Optional[PrivacyNotice]]" = relationship(
        "PrivacyNotice",
        back_populates="children",
        remote_side=[id],
    )

    @hybridproperty
    def default_preference(self) -> UserConsentPreference:
        """Returns the user's default consent preference given the consent
        mechanism of this notice, or "what is granted to the user"

        For example, if a notice has an opt in consent mechanism, this means
        that they should be granted the opportunity to opt in, but by
        default, they *should be opted out*
        """
        if self.consent_mechanism == ConsentMechanism.opt_in:
            return UserConsentPreference.opt_out  # Intentional
        if self.consent_mechanism == ConsentMechanism.opt_out:
            return UserConsentPreference.opt_in  # Intentional
        if self.consent_mechanism == ConsentMechanism.notice_only:
            return UserConsentPreference.acknowledge

        raise Exception("Invalid notice consent mechanism.")

    @property
    def cookies(self) -> List[Asset]:
        """Return relevant assets of type 'cookie' (via the data use)"""
        db = Session.object_session(self)
        or_queries = [
            f"array_to_string(data_uses, ',') ILIKE '{data_use}%'"
            for data_use in self.data_uses
        ]

        query = db.query(Asset).filter(
            Asset.asset_type == "Cookie",
            or_(*[text(query) for query in or_queries]),
        )

        return query.all()

    @property
    def calculated_systems_applicable(self) -> bool:
        """Convenience property to return if any systems overlap with this notice's data uses

        This is used in the Plus API
        """
        db = Session.object_session(self)

        all_system_data_uses: Set[str] = get_system_data_uses(db, include_parents=True)
        return bool(set(self.data_uses).intersection(all_system_data_uses))

    @property
    def configured_regions_for_notice(self) -> List[str]:
        """Convenience property to look up which regions are using these Notices.

        This is used in the Plus API
        """
        db = Session.object_session(self)

        # Raw sql for performance
        experience_regions_cursor_result = db.execute(
            text(
                """
            SELECT array_agg(distinct(privacyexperience.region) order by privacyexperience.region) AS regions
            FROM privacynotice
               JOIN experiencenotices
                 ON experiencenotices.notice_id = :privacy_notice_id
               JOIN privacyexperienceconfig
                 ON privacyexperienceconfig.id = experiencenotices.experience_config_id
               JOIN privacyexperience
                 ON privacyexperience.experience_config_id = privacyexperienceconfig.id
            GROUP BY privacynotice.id
            """
            ),
            {"privacy_notice_id": self.id},
        )
        res = [result for result in experience_regions_cursor_result]
        return res[0]["regions"] if res else []

    @classmethod
    def fetch_and_validate_notices(
        cls,
        db: Session,
        child_notices: List[Dict[str, Any]],
        parent_id: Optional[str] = None,
    ) -> List[PrivacyNotice]:
        """
        Retrieves existing notices from the database and validates their linkage status.

        This function performs two main checks:
        1. Ensures all specified notices exist in the database.
        2. Verifies that notices are not linked to a different parent than the one specified.
        """

        notice_map = {
            child_notice["id"]: child_notice["name"] for child_notice in child_notices
        }
        child_notice_ids = set(notice_map.keys())
        existing_notices: List[PrivacyNotice] = (
            db.query(cls).filter(cls.id.in_(child_notice_ids)).all()
        )

        if missing_ids := child_notice_ids - {notice.id for notice in existing_notices}:
            missing_names = [notice_map[id] for id in missing_ids]
            raise ValueError(
                f"The following notices do not exist: {', '.join(missing_names)}"
            )

        if linked_ids := {
            notice.id
            for notice in existing_notices
            if notice.parent_id is not None and notice.parent_id != parent_id
        }:
            linked_names = [notice_map[id] for id in linked_ids]
            raise ValueError(
                f"The following notices are already linked to another notice: {', '.join(linked_names)}"
            )

        return existing_notices

    @classmethod
    def create(
        cls: Type[PrivacyNotice],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> PrivacyNotice:
        """
        Creates a Privacy Notice and then a NoticeTranslation record for each supplied Translation.

        - For each Notice translation, we also create a PrivacyNoticeHistory record which versions details
        from both the Notice and the Translation itself for auditing purposes.
        - Privacy preferences can be saved separately against this PrivacyNoticeHistory record which contains all the info
        about the notice and the translation to which the user supplied a consent preference.
        """
        translations = data.pop("translations", []) or []
        child_notices = data.pop("children", []) or []

        # return an error before the actual creation if the children are not valid
        existing_notices = cls.fetch_and_validate_notices(db, child_notices)

        created: PrivacyNotice = super().create(db=db, data=data, check_name=check_name)

        # automatically links and unlinks at the DB level with this assignment
        created.children = existing_notices
        db.commit()

        data.pop(
            "id", None
        )  # Default Notices have id specified but we don't want to use the same id for the historical record

        for translation_data in translations:
            # Create the Notice Translation
            translation = NoticeTranslation.create(
                db, data={**translation_data, "privacy_notice_id": created.id}
            )
            # Take a snapshot of the Privacy Notice and the Notice Translation combined. Privacy preferences
            # are saved against this record.
            PrivacyNoticeHistory.create(
                db,
                data={**data, **translation_data, "translation_id": translation.id},
                check_name=False,
            )

        return created

    def update(self, db: Session, *, data: dict[str, Any]) -> PrivacyNotice:
        """
        Updates the Privacy Notice, child privacy notices, and its translations.

        - Links or unlinks child privacy notices to match the children in the request
        - Upserts or deletes supplied translations to match translations in the request
        - For each remaining translation, create a historical record if the base notice
        or translation changed.
        """
        request_translations = data.pop("translations", [])
        child_notices = data.pop("children", [])

        existing_notices = PrivacyNotice.fetch_and_validate_notices(
            db, child_notices, self.id
        )
        # automatically links and unlinks at the DB level with this assignment
        self.children = existing_notices

        # Performs a patch update of the base privacy notice
        base_notice_updated: bool = update_if_modified(self, db=db, data=data)

        for translation_data in request_translations:
            existing_translation: Optional[NoticeTranslation] = (
                self.get_translation_by_language(db, translation_data.get("language"))
            )

            if existing_translation:
                translation: NoticeTranslation = existing_translation
                # Performs a patch update of the existing translation
                translation_updated: bool = update_if_modified(  # type: ignore[attr-defined]
                    existing_translation,
                    db=db,
                    data={**translation_data, "privacy_notice_id": self.id},
                )
            else:
                translation_updated = True
                # Creates a new translation
                translation = NoticeTranslation.create(
                    db,
                    data={**translation_data, "privacy_notice_id": self.id},
                )

            if base_notice_updated or translation_updated:
                create_historical_record_for_notice_and_translation(
                    db=db, privacy_notice=self, notice_translation=translation
                )

        # Removes any translations not supplied in the request from the Notice
        delete_notice_translations(
            db, privacy_notice=self, request_translations=request_translations
        )

        return self  # type: ignore[return-value]

    def dry_update(self, *, data: dict[str, Any]) -> PrivacyNotice:
        """
        A utility method to get an updated object without saving it to the db.

        This is used to see what an object update would look like, in memory,
        without actually persisting the update to the db
        """
        updated_attributes: Dict = dry_update_data(resource=self, data_updates=data)

        # This relationship needs to be removed before the dry_update
        # to prevent the dry update from being added to Session.new
        updated_attributes.pop("translations", [])
        updated_attributes.pop("children", [])

        # create a new object with the updated attribute data to keep this
        # ORM object (i.e., `self`) pristine
        return PrivacyNotice(**updated_attributes)

    def get_translation_by_language(
        self, db: Session, language: Optional[SupportedLanguage]
    ) -> Optional[NoticeTranslation]:
        """Lookup a translation on a Privacy Notice by language if it exists"""
        if not language:
            # Shouldn't be possible, but just in case
            return None
        return (
            db.query(NoticeTranslation)
            .filter(
                NoticeTranslation.language == language,
                NoticeTranslation.privacy_notice_id == self.id,
            )
            .first()
        )


class NoticeTranslationBase:
    """Base fields for Notice Translations
    These fields are translated
    """

    description = Column(String)
    language = Column(
        EnumColumn(
            SupportedLanguage,
            native_enum=False,
            values_callable=lambda x: [i.value for i in x],
        ),
    )
    title = Column(String, nullable=False)


class NoticeTranslation(NoticeTranslationBase, Base):
    """Available translations saved for a given Privacy Notice"""

    language = Column(
        EnumColumn(
            SupportedLanguage,
            native_enum=False,
            values_callable=lambda x: [i.value for i in x],
        ),
        nullable=False,
    )  # Overrides NoticeTranslationBase to make language non-nullable

    privacy_notice_id = Column(
        String, ForeignKey(PrivacyNotice.id_field_path), nullable=False
    )

    histories: RelationshipProperty[AppenderQuery] = relationship(
        "PrivacyNoticeHistory",
        backref="notice_translation",
        lazy="dynamic",
        order_by="PrivacyNoticeHistory.created_at",
    )

    __table_args__ = (
        UniqueConstraint("language", "privacy_notice_id", name="notice_translation"),
    )

    @property
    def version(self) -> Optional[float]:
        """Convenience property that returns the latest translation version number for this notice"""
        return (
            self.privacy_notice_history.version if self.privacy_notice_history else None  # type: ignore[return-value]
        )

    @property
    def privacy_notice_history(self) -> Optional[PrivacyNoticeHistory]:
        """Convenience property that returns the privacy notice history for the latest version.

        Note that there are possibly many historical records for the notice translation, this just returns the current
        corresponding historical record.
        """
        # Histories are sorted at the relationship level
        return self.histories[-1] if self.histories.count() else None

    @property
    def privacy_notice_history_id(self) -> Optional[str]:
        """Convenience property that returns the privacy notice history id for the current version.

        Note that there are possibly many historical records for the given notice translation, this just returns the current
        corresponding historical record.
        """
        return self.privacy_notice_history.id if self.privacy_notice_history else None


class DeprecatedPrivacyNoticeHistoryFields:
    """
    Fields we no longer save on the privacy notice, but are now configured on the Experience side.

    However, these fields are retained for auditing purposes on early historical records.
    """

    displayed_in_privacy_center = Column(
        Boolean,
    )
    displayed_in_overlay = Column(
        Boolean,
    )
    displayed_in_api = Column(
        Boolean,
    )
    regions = Column(
        ARRAY(EnumColumn(DeprecatedNoticeRegion, native_enum=False)),
        index=True,
    )


class PrivacyNoticeHistory(
    NoticeTranslationBase, PrivacyNoticeBase, DeprecatedPrivacyNoticeHistoryFields, Base
):
    """
    An "audit table" stores all versions of `PrivacyNotice` + `NoticeTranslations`.

    - When a Privacy Notice and/or its translations are updated, each translation has a PrivacyNoticeHistory record created.
    Privacy preferences are saved against this notice history.
    """

    origin = Column(
        String,
        ForeignKey(PrivacyNoticeTemplate.id_field_path),
    )  # pointer back to the PrivacyNoticeTemplate

    translation_id = Column(
        String,
        ForeignKey(NoticeTranslation.id_field_path, ondelete="SET NULL"),
        index=True,
    )  # pointer back to the NoticeTranslation.  Set to null if the translation is deleted, but
    # we retain this record for consent reporting

    version = Column(Float, nullable=False, default=1.0)


def create_historical_record_for_notice_and_translation(
    db: Session, privacy_notice: PrivacyNotice, notice_translation: NoticeTranslation
) -> None:
    existing_version: float = notice_translation.version or 0.0
    history_data: dict = create_historical_data_from_record(privacy_notice)
    history_data.pop("translations", None)
    history_data.pop("parent_id", None)

    updated_translation_data: dict = create_historical_data_from_record(
        notice_translation
    )
    # Translations have a FK back to privacy_notice_id, but this historical records do not
    updated_translation_data.pop("privacy_notice_id")

    # Creates a historical record of the Notice and the translation combined. Preferences are saved
    # against this resource.
    PrivacyNoticeHistory.create(
        db,
        data={
            **history_data,
            **updated_translation_data,
            "translation_id": notice_translation.id,
            "version": existing_version + 1.0,
        },
        check_name=False,
    )


def delete_notice_translations(
    db: Session,
    privacy_notice: PrivacyNotice,
    request_translations: Dict,
) -> None:
    """Removes any translations that are currently stored on the PrivacyNotice but not in the update request"""
    notice_translations: List[NoticeTranslation] = privacy_notice.translations
    translations_to_remove: Set[SupportedLanguage] = set(  # type: ignore[assignment]
        translation.language for translation in notice_translations
    ).difference(
        set(translation.get("language") for translation in request_translations)
    )

    db.query(NoticeTranslation).filter(
        NoticeTranslation.language.in_(translations_to_remove),
        NoticeTranslation.privacy_notice_id == privacy_notice.id,
    ).delete()
    db.commit()
