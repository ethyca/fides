from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type, Union

from fideslang.validation import FidesKey
from sqlalchemy import Boolean, Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import Float, ForeignKey, String, UniqueConstraint, or_
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import RelationshipProperty, Session, relationship
from sqlalchemy.orm.dynamic import AppenderQuery
from sqlalchemy.util import hybridproperty

from fides.api.common_exceptions import ValidationError
from fides.api.db.base_class import Base, FidesBase
from fides.api.models.sql_models import (  # type: ignore[attr-defined]
    Cookies,
    PrivacyDeclaration,
    System,
)


class Language(Enum):
    """Using BCP 47 Language Tags

    TODO propose adding this list:
    https://www.techonthenet.com/js/language_tags.php
    """

    en_us = "en_us"  # US English
    en_gb = "en_gb"  # British English


class PrivacyNoticeFramework(Enum):
    gpp_us_national = "gpp_us_national"
    gpp_us_state = "gpp_us_state"


class UserConsentPreference(Enum):
    opt_in = "opt_in"  # The user wants to opt in to the notice
    opt_out = "opt_out"  # The user wants to opt out of the notice
    acknowledge = "acknowledge"  # The user has acknowledged this notice
    tcf = "tcf"  # Overall preference set for TCF where there are numerous preferences under the single notice


# Enum defined using functional API so we can use regions like "is"
PrivacyNoticeRegion = Enum(
    "PrivacyNoticeRegion",
    [
        ("us", "us"),  # united states
        ("us_al", "us_al"),  # alabama
        ("us_ak", "us_ak"),  # alaska
        ("us_az", "us_az"),  # arizona
        ("us_ar", "us_ar"),  # arkansas
        ("us_ca", "us_ca"),  # california
        ("us_co", "us_co"),  # colorado
        ("us_ct", "us_ct"),  # connecticut
        ("us_de", "us_de"),  # delaware
        ("us_fl", "us_fl"),  # florida
        ("us_ga", "us_ga"),  # georgia
        ("us_hi", "us_hi"),  # hawaii
        ("us_id", "us_id"),  # idaho
        ("us_il", "us_il"),  # illinois
        ("us_in", "us_in"),  # indiana
        ("us_ia", "us_ia"),  # iowa
        ("us_ks", "us_ks"),  # kansas
        ("us_ky", "us_ky"),  # kentucky
        ("us_la", "us_la"),  # louisiana
        ("us_me", "us_me"),  # maine
        ("us_md", "us_md"),  # maryland
        ("us_ma", "us_ma"),  # massachusetts
        ("us_mi", "us_mi"),  # michigan
        ("us_mn", "us_mn"),  # minnesota
        ("us_ms", "us_ms"),  # mississippi
        ("us_mo", "us_mo"),  # missouri
        ("us_mt", "us_mt"),  # montana
        ("us_ne", "us_ne"),  # nebraska
        ("us_nv", "us_nv"),  # nevada
        ("us_nh", "us_nh"),  # new hampshire
        ("us_nj", "us_nj"),  # new jersey
        ("us_nm", "us_nm"),  # new mexico
        ("us_ny", "us_ny"),  # new york
        ("us_nc", "us_nc"),  # north carolina
        ("us_nd", "us_nd"),  # north dakota
        ("us_oh", "us_oh"),  # ohio
        ("us_ok", "us_ok"),  # oklahoma
        ("us_or", "us_or"),  # oregon
        ("us_pa", "us_pa"),  # pennsylvania
        ("us_ri", "us_ri"),  # rhode island
        ("us_sc", "us_sc"),  # south carolina
        ("us_sd", "us_sd"),  # south dakota
        ("us_tn", "us_tn"),  # tennessee
        ("us_tx", "us_tx"),  # texas
        ("us_ut", "us_ut"),  # utah
        ("us_vt", "us_vt"),  # vermont
        ("us_va", "us_va"),  # virginia
        ("us_wa", "us_wa"),  # washington
        ("us_wv", "us_wv"),  # west virginia
        ("us_wi", "us_wi"),  # wisconsin
        ("us_wy", "us_wy"),  # wyoming
        ("eea", "eea"),  # european economic area
        ("be", "be"),  # belgium
        ("bg", "bg"),  # bulgaria
        ("cz", "cz"),  # czechia
        ("dk", "dk"),  # denmark
        ("de", "de"),  # germany
        ("ee", "ee"),  # estonia
        ("ie", "ie"),  # ireland
        ("gr", "gr"),  # greece
        ("es", "es"),  # spain
        ("fr", "fr"),  # france
        ("hr", "hr"),  # croatia
        ("it", "it"),  # italy
        ("cy", "cy"),  # cyprus
        ("lv", "lv"),  # latvia
        ("lt", "lt"),  # lithuania
        ("lu", "lu"),  # luxembourg
        ("hu", "hu"),  # hungary
        ("mt", "mt"),  # malta
        ("nl", "nl"),  # netherlands
        ("at", "at"),  # austria
        ("pl", "pl"),  # poland
        ("pt", "pt"),  # portugal
        ("ro", "ro"),  # romania
        ("si", "si"),  # slovenia
        ("sk", "sk"),  # slovakia
        ("fi", "fi"),  # finland
        ("se", "se"),  # sweden
        ("gb_eng", "gb_eng"),  # england
        ("gb_sct", "gb_sct"),  # scotland
        ("gb_wls", "gb_wls"),  # wales
        ("gb_nir", "gb_nir"),  # northern ireland
        ("is", "is"),  # iceland
        ("no", "no"),  # norway
        ("li", "li"),  # liechtenstein
        ("ca", "ca"),  # canada
        ("ca_ab", "ca_ab"),  # alberta
        ("ca_bc", "ca_bc"),  # british columbia
        ("ca_mb", "ca_mb"),  # manitoba
        ("ca_nb", "ca_nb"),  # new brunswick
        ("ca_nl", "ca_nl"),  # newfoundland and labrador
        ("ca_ns", "ca_ns"),  # nova scotia
        ("ca_on", "ca_on"),  # ontario
        ("ca_pe", "ca_pe"),  # prince edward island
        ("ca_qc", "ca_qc"),  # quebec
        ("ca_sk", "ca_sk"),  # saskatchewan
        ("ca_nt", "ca_nt"),  # northwest territories
        ("ca_nu", "ca_nu"),  # nunavut
        ("ca_yt", "ca_yt"),  # yukon
    ],
)


class ConsentMechanism(Enum):
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
    This class contains the common fields between PrivacyNoticeTemplate, PrivacyNotice, and PrivacyNoticeHistory
    """

    name = Column(String, nullable=False)
    description = Column(
        String
    )  # TODO will be removed from PrivacyNoticeTemplate and PrivacyNotice in favor of NoticeTranslation.
    internal_description = Column(String)  # Visible to internal users only
    regions = Column(  # TODO will be removed in favor of configuring this on the Experience-side
        ARRAY(EnumColumn(PrivacyNoticeRegion, native_enum=False)),
        index=True,
        nullable=True,
    )
    consent_mechanism = Column(EnumColumn(ConsentMechanism), nullable=False)
    data_uses = Column(
        ARRAY(String),
        nullable=False,
        server_default="{}",
        default=dict,
    )  # a list of `fides_key`s of `DataUse` records
    enforcement_level = Column(EnumColumn(EnforcementLevel), nullable=False)
    disabled = Column(Boolean, nullable=False, default=False)
    has_gpc_flag = Column(Boolean, nullable=False, default=False)
    displayed_in_privacy_center = Column(
        Boolean, nullable=False, default=False
    )  # TODO will be removed
    displayed_in_overlay = Column(
        Boolean, nullable=False, default=False
    )  # TODO will be removed
    displayed_in_api = Column(
        Boolean, nullable=False, default=False
    )  # TODO will be removed
    notice_key = Column(String, nullable=False)
    framework = Column(String)
    gpp_field_mapping = Column(MutableList.as_mutable(JSONB), index=False, unique=False)

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
        return FidesKey(FidesKey.validate(notice_key))

    def validate_enabled_has_data_uses(self) -> None:
        """Validated that enabled privacy notices have data uses"""
        if not self.disabled and not self.data_uses:
            raise ValidationError(
                "A privacy notice must have at least one data use assigned in order to be enabled."
            )


class PrivacyNoticeTemplate(PrivacyNoticeBase, Base):
    """
    This table contains the out-of-the-box Privacy Notice Templates that are shipped with Fides
    """

    translations = Column(ARRAY(JSONB))

    def dry_update(self, *, data: dict[str, Any]) -> FidesBase:
        """
        A utility method to get an updated object without saving it to the db.

        This is used to see what an object update would look like, in memory,
        without actually persisting the update to the db
        """
        # Update our attributes with values in data
        cloned_attributes = self.__dict__.copy()
        for key, val in data.items():
            cloned_attributes[key] = val

        # remove protected fields from the cloned dict
        cloned_attributes.pop("_sa_instance_state", None)
        cloned_attributes.pop("id", None)

        # create a new object with the updated attribute data to keep this
        # ORM object (i.e., `self`) pristine
        return PrivacyNoticeTemplate(**cloned_attributes)


class PrivacyNotice(PrivacyNoticeBase, Base):
    """
    A notice set up by a system administrator that an end user (i.e., data subject)
    accepts or rejects to indicate their consent for particular data uses
    """

    origin = Column(
        String, ForeignKey(PrivacyNoticeTemplate.id_field_path), nullable=True
    )  # pointer back to the PrivacyNoticeTemplate
    version = Column(
        Float, nullable=False, default=1.0
    )  # TODO Pending Removal.  This is now only on PrivacyNoticeHistory.

    translations: RelationshipProperty[List[NoticeTranslation]] = relationship(
        "NoticeTranslation",
        backref="privacy_notice",
        lazy="selectin",
        order_by="NoticeTranslation.created_at",
    )

    # Forward declaration to avoid circular import errors
    PrivacyExperienceConfig = "PrivacyExperienceConfig"

    experience_configs = relationship(
        PrivacyExperienceConfig,
        secondary="experiencenotices",
        back_populates="privacy_notices",
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
    def cookies(self) -> List[Cookies]:
        """Return relevant cookie names (via the data use)"""
        db = Session.object_session(self)
        return (
            db.query(Cookies)
            .join(
                PrivacyDeclaration,
                PrivacyDeclaration.id == Cookies.privacy_declaration_id,
            )
            .filter(
                or_(
                    *[
                        PrivacyDeclaration.data_use.like(f"{notice_use}%")
                        for notice_use in self.data_uses
                    ]
                )
            )
        ).all()

    @property
    def systems_applicable(self) -> bool:
        """Return if any systems overlap with this notice's data uses"""
        db = Session.object_session(self)
        for system in db.query(System):
            if self.applies_to_system(system):
                return True
        return False

    @property
    def configured_regions(self) -> List[PrivacyNoticeRegion]:
        """Look up the regions on the Experiences using these Notices"""
        from fides.api.models.privacy_experience import (
            ExperienceNotices,
            PrivacyExperience,
        )

        db = Session.object_session(self)
        configured_regions = (
            db.query(PrivacyExperience.region)
            .join(
                ExperienceNotices,
                PrivacyExperience.experience_config_id
                == ExperienceNotices.experience_config_id,
            )
            .filter(ExperienceNotices.notice_id == self.id)
            .group_by(PrivacyExperience.region)
            .order_by(PrivacyExperience.region.asc())
        )
        return [region[0] for region in configured_regions]

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

        For each Translation a historical record is created which combines details from the Notice and
        the Translation for auditing purposes.  Privacy preferences are saved against the PrivacyNoticeHistory
        record which contains the full details."""
        translations = data.pop("translations", []) or []
        created = super().create(db=db, data=data, check_name=check_name)

        for translation_data in translations:
            data.pop(
                "id", None
            )  # Default Notices have id specified but we don't want to use the same id for the historical record
            translation = NoticeTranslation.create(
                db, data={**translation_data, "privacy_notice_id": created.id}
            )
            PrivacyNoticeHistory.create(
                db,
                data={**data, **translation_data, "translation_id": translation.id},
                check_name=False,
            )

        return created

    def update(self, db: Session, *, data: dict[str, Any]) -> PrivacyNotice:
        """
        Updates the Privacy Notice
        - Upserts or deletes supplied translations to match translations in the request
        - For each remaining translation, create a historical record if the base notice or translation changed.
        """
        request_translations = data.pop("translations", [])

        base_notice_updated: bool = update_if_modified(self, db=db, data=data)

        for translation_data in request_translations:
            existing_translation: Optional[
                NoticeTranslation
            ] = self.get_translation_by_language(db, translation_data.get("language"))

            if existing_translation:
                translation: NoticeTranslation = existing_translation
                translation_updated: bool = update_if_modified(  # type: ignore[attr-defined]
                    existing_translation,
                    db=db,
                    data={**translation_data, "privacy_notice_id": self.id},
                )
            else:
                translation_updated = True
                translation = NoticeTranslation.create(
                    db,
                    data={**translation_data, "privacy_notice_id": self.id},
                )

            if base_notice_updated or translation_updated:
                existing_version: float = translation.version or 0.0
                history_data: dict = create_historical_data_from_record(self)
                history_data.pop("translations", None)
                updated_translation_data: dict = create_historical_data_from_record(
                    translation
                )
                PrivacyNoticeHistory.create(
                    db,
                    data={
                        **history_data,
                        **updated_translation_data,
                        "translation_id": translation.id,
                        "version": existing_version + 1.0,
                    },
                    check_name=False,
                )

        notice_translations: List[NoticeTranslation] = self.translations
        translations_to_remove: Set[Language] = set(  # type: ignore[assignment]
            translation.language for translation in notice_translations
        ).difference(
            set(translation.get("language") for translation in request_translations)
        )

        db.query(NoticeTranslation).filter(
            NoticeTranslation.language.in_(translations_to_remove),
            NoticeTranslation.privacy_notice_id == self.id,
        ).delete()

        return self  # type: ignore[return-value]

    def dry_update(self, *, data: dict[str, Any]) -> PrivacyNotice:
        """
        A utility method to get an updated object without saving it to the db.

        This is used to see what an object update would look like, in memory,
        without actually persisting the update to the db
        """
        # Update our attributes with values in data
        cloned_attributes = self.__dict__.copy()
        for key, val in data.items():
            cloned_attributes[key] = val

        # remove protected fields from the cloned dict
        cloned_attributes.pop("_sa_instance_state", None)
        cloned_attributes.pop("id", None)
        cloned_attributes.pop("translations", [])

        # create a new object with the updated attribute data to keep this
        # ORM object (i.e., `self`) pristine
        return PrivacyNotice(**cloned_attributes)

    def get_translation_by_language(
        self, db: Session, language: Optional[Language]
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
    language = Column(EnumColumn(Language), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)


class NoticeTranslation(NoticeTranslationBase, Base):
    """Available translations for a given Privacy Notice"""

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
        """Convenience property that returns the latest version number of the translation"""
        return (
            self.privacy_notice_history.version if self.privacy_notice_history else None  # type: ignore[return-value]
        )

    @property
    def privacy_notice_history(self) -> Optional[PrivacyNoticeHistory]:
        """Convenience property that returns the privacy notice history for the latest version.

        Note that there are possibly many historical records for the given experience config translation, this just returns the current
        corresponding historical record.
        """
        # Histories are sorted at the relationship level
        return self.histories[-1] if self.histories.count() else None

    @property
    def privacy_notice_history_id(self) -> Optional[str]:
        """Convenience property that returns the privacy notice history id for the current version.

        Note that there are possibly many historical records for the given experience config translation, this just returns the current
        corresponding historical record.
        """
        return self.privacy_notice_history.id if self.privacy_notice_history else None


PRIVACY_NOTICE_TYPE = Union[PrivacyNotice, PrivacyNoticeTemplate]


def new_data_use_conflicts_with_existing_use(existing_use: str, new_use: str) -> bool:
    """Data use check that prevents grandparent/parent/child, but allows siblings, aunt/child, etc.
    Check needs to happen in both directions.
    This assumes the supplied uses are on notices in the same region.
    """
    return existing_use.startswith(new_use) or new_use.startswith(existing_use)


class PrivacyNoticeHistory(NoticeTranslationBase, PrivacyNoticeBase, Base):
    """
    An "audit table" stores outdated versions of `PrivacyNotice` + `NoticeTranslations`.
    Privacy preferences are saved against this notice history.
    """

    origin = Column(
        String, ForeignKey(PrivacyNoticeTemplate.id_field_path), nullable=True
    )  # pointer back to the PrivacyNoticeTemplate

    version = Column(Float, nullable=False, default=1.0)

    translation_id = Column(
        String, ForeignKey(NoticeTranslation.id_field_path, ondelete="SET NULL")
    )  # pointer back to the NoticeTranslation

    privacy_notice_id = Column(
        String, ForeignKey(PrivacyNotice.id_field_path), nullable=True
    )  # TODO Will be removed.  This now points to just the translation.


def update_if_modified(resource: Base, db: Session, *, data: dict[str, Any]) -> bool:
    """Returns whether the resource was modified on save (which determines if we should create
    a corresponding historical record).
    """
    # run through potential updates now
    for key, value in data.items():
        setattr(resource, key, value)

    if db.is_modified(resource):
        resource.save(db)
        return True

    return False


def create_historical_data_from_record(resource: Base) -> Dict:
    """Prep data to be saved in a historical table for record keeping"""
    # Resource attributes are being lazy loaded and not showing up in the dict.  Accessing
    # an attribute causes them to be loaded.
    resource.id  # pylint: disable=pointless-statement
    history_data = resource.__dict__.copy()
    history_data.pop("_sa_instance_state", None)
    history_data.pop("id", None)
    history_data.pop("created_at", None)
    history_data.pop("updated_at", None)
    return history_data
