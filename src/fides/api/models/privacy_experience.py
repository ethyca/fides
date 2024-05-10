from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type

from sqlalchemy import Boolean, Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Query, RelationshipProperty, Session, relationship
from sqlalchemy.orm.dynamic import AppenderQuery

from fides.api.db.base_class import Base
from fides.api.models import (
    create_historical_data_from_record,
    dry_update_data,
    update_if_modified,
)
from fides.api.models.location_regulation_selections import PrivacyNoticeRegion
from fides.api.models.privacy_notice import PrivacyNotice
from fides.api.models.property import Property
from fides.api.schemas.language import SupportedLanguage


class ComponentType(Enum):
    """
    The component type - not formalized in the db

    Overlay type has been deprecated but can't be removed for backwards compatibility
    without significant data migrations.
    """

    overlay = "overlay"  # Deprecated. DO NOT REMOVE.
    banner_and_modal = "banner_and_modal"
    modal = "modal"
    privacy_center = "privacy_center"
    tcf_overlay = "tcf_overlay"  # TCF Banner + modal combined


# Fides JS UX Types - there should only be one of these defined per region
FidesJSUXTypes: List[ComponentType] = [
    ComponentType.banner_and_modal,
    ComponentType.modal,
]

# Fides JS Overlay Types - there should only be one of these defined per region + property
FidesJSOverlayTypes: List[ComponentType] = [
    ComponentType.banner_and_modal,
    ComponentType.modal,
    ComponentType.tcf_overlay
]


class PrivacyExperienceConfigBase:
    """
    Common fields shared between:
    - ExperienceConfigTemplate
    - PrivacyExperienceConfig
    - PrivacyExperienceConfigHistory

    These are non-translated fields.
    """

    allow_language_selection = Column(
        Boolean,
    )
    auto_detect_language = Column(
        Boolean,
    )
    disabled = Column(Boolean, nullable=False, default=True)

    dismissable = Column(Boolean)

    @declared_attr
    def component(cls) -> Column:
        return Column(
            EnumColumn(ComponentType),
            nullable=False,
            index=True,
        )

    name = Column(String)


class ExperienceConfigTemplate(PrivacyExperienceConfigBase, Base):
    """Table for out-of-the-box Experience Configurations"""

    allow_language_selection = Column(
        Boolean, nullable=False, default=False, server_default="f"
    )  # Overrides PrivacyExperienceConfigBase to make non-nullable
    auto_detect_language = Column(
        Boolean, nullable=False, default=True, server_default="t"
    )  # Overrides PrivacyExperienceConfigBase to make non-nullable
    dismissable = Column(
        Boolean, nullable=False, default=True, server_default="t"
    )  # Overrides PrivacyExperienceConfigBase to make non-nullable
    name = Column(
        String, nullable=False
    )  # Overriding PrivacyExperienceConfigBase to make non-nullable

    privacy_notice_keys = Column(
        ARRAY(String)
    )  # A list of notice keys which should correspond to a subset of out-of-the-box notice keys
    regions = Column(
        ARRAY(EnumColumn(PrivacyNoticeRegion, native_enum=False)),
    )
    translations = Column(
        ARRAY(JSONB)
    )  # A list of all available out of the box translations


class ExperienceTranslationBase:
    """Base schema for fields shared between ExperienceTranslation and PrivacyExperienceHistory.

    These are translated fields
    """

    accept_button_label = Column(String)
    acknowledge_button_label = Column(String)
    banner_description = Column(String)
    banner_title = Column(String)
    description = Column(String)
    is_default = Column(Boolean, nullable=False, default=False)

    language = Column(
        EnumColumn(
            SupportedLanguage,
            native_enum=False,
            values_callable=lambda x: [
                i.value for i in x
            ],  # allows enum _values_ to be stored rather than name
        ),
    )

    privacy_policy_link_label = Column(String)
    privacy_policy_url = Column(String)
    privacy_preferences_link_label = Column(String)
    modal_link_label = Column(String)
    reject_button_label = Column(String)
    save_button_label = Column(String)
    title = Column(String)


class PrivacyExperienceConfig(PrivacyExperienceConfigBase, Base):
    """
    The Privacy Experience Configuration model that stores shared configuration for Privacy Experiences.

    - Translations, Notices, and Regions (via Privacy Experiences) are linked to this resource.
    """

    allow_language_selection = Column(
        Boolean, nullable=False, default=False, server_default="f"
    )  # Overrides PrivacyExperienceConfigBase to make non-nullable
    auto_detect_language = Column(
        Boolean, nullable=False, default=True, server_default="t"
    )  # Overrides PrivacyExperienceConfigBase to make non-nullable
    disabled = Column(
        Boolean, nullable=False, default=True, index=True
    )  # Overridding PrivacyExperienceConfigBase to index
    dismissable = Column(
        Boolean, nullable=False, default=True, server_default="t"
    )  # Overrides PrivacyExperienceConfigBase to make non-nullable
    name = Column(
        String, nullable=False
    )  # Overriding PrivacyExperienceConfigBase to make non-nullable
    origin = Column(
        String, ForeignKey(ExperienceConfigTemplate.id_field_path)
    )  # The template from which this config was created if applicable

    # Relationships
    experiences = relationship(
        "PrivacyExperience",
        back_populates="experience_config",
        lazy="dynamic",
        cascade="all,delete",
    )

    privacy_notices: RelationshipProperty[List[PrivacyNotice]] = relationship(
        "PrivacyNotice",
        secondary="experiencenotices",
        backref="experience_configs",
        lazy="selectin",
    )

    translations: RelationshipProperty[List[ExperienceTranslation]] = relationship(
        "ExperienceTranslation",
        backref="privacy_experience_config",
        lazy="selectin",
        order_by="ExperienceTranslation.created_at",
    )

    properties: RelationshipProperty[List[Property]] = relationship(
        "Property",
        secondary="plus_privacy_experience_config_property",
        back_populates="experiences",
        lazy="selectin",
    )

    @property
    def regions(self) -> List[PrivacyNoticeRegion]:
        """Return the regions using this experience config"""
        return [exp.region for exp in self.experiences]  # type: ignore[attr-defined]

    def get_translation_by_language(
        self, db: Session, language: Optional[SupportedLanguage]
    ) -> Optional[ExperienceTranslation]:
        """Lookup a translation on an ExperienceConfig by language if it exists"""
        if not language:
            return None
        return (
            db.query(ExperienceTranslation)
            .filter(
                ExperienceTranslation.language == language,
                ExperienceTranslation.experience_config_id == self.id,
            )
            .first()
        )

    @classmethod
    def create(
        cls: Type[PrivacyExperienceConfig],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> PrivacyExperienceConfig:
        """
        Creates an Experience Config which is a large exercise!

        - Creates the ExperienceConfig
        - For each Translation supplied, creates an ExperienceTranslation and a historical
        record combining details from the translation and the Experience Config
        - Links regions to the ExperienceConfig (by creating/updating associated PrivacyExperiences
        and adding a FK back to the config)
        - Adds/removes Notices to/from the Experience Config
        """
        translations = data.pop("translations", [])
        regions = data.pop("regions", [])
        privacy_notice_ids = data.pop("privacy_notice_ids", [])
        properties = data.pop("properties", [])
        data.pop(
            "id", None
        )  # Default templates have ids but we don't want to use them here

        experience_config: PrivacyExperienceConfig = super().create(
            db=db, data=data, check_name=check_name
        )

        for translation_data in translations:
            # Create an ExperienceTranslation
            translation = ExperienceTranslation.create(
                db,
                data={**translation_data, "experience_config_id": experience_config.id},
            )
            # Version the ExperienceTranslation and the original PrivacyExperienceConfig together.
            PrivacyExperienceConfigHistory.create(
                db,
                data={**data, **translation_data, "translation_id": translation.id},
                check_name=False,
            )

        # Link regions to this PrivacyExperienceConfig via the PrivacyExperience table
        upsert_privacy_experiences_after_config_update(db, experience_config, regions)
        # Link Privacy Notices to this Privacy Experience config via the ExperienceNotices table
        link_notices_to_experience_config(
            db, notice_ids=privacy_notice_ids, experience_config=experience_config
        )
        # Link Properties to this Privacy Experience config via the PrivacyExperienceConfigProperty table
        link_properties_to_experience_config(db, properties, experience_config)

        return experience_config

    def update(self, db: Session, *, data: dict[str, Any]) -> PrivacyExperienceConfig:
        """
        Updates a PrivacyExperienceConfig and related resources which is a large exercise!

        - Updates the PrivacyExperienceConfig details
        - For each supplied translation, add, update, or delete translations so they match
        the translations in the update request
        - For each remaining translation, if the translation or the config has changed,
        create a historical record for auditing purposes
        - Link or unlink regions (via Privacy Experiences)
        - Link or unlink Privacy Notices
        """
        request_translations = data.pop("translations", [])
        regions = data.pop("regions", [])
        privacy_notice_ids = data.pop("privacy_notice_ids", [])
        properties = data.pop("properties", [])

        # Do a patch update of the existing privacy experience config if applicable
        config_updated = update_if_modified(self, db=db, data=data)

        for translation_data in request_translations:
            existing_translation: Optional[ExperienceTranslation] = (
                self.get_translation_by_language(db, translation_data.get("language"))
            )
            if existing_translation:
                # Do a patch update of the existing experience translation if applicable
                translation_updated: bool = update_if_modified(
                    existing_translation,
                    db=db,
                    data={**translation_data, "experience_config_id": self.id},
                )
                translation = existing_translation
            else:
                translation_updated = True
                # Create a new Experience Translation since one doesn't exist
                translation = ExperienceTranslation.create(
                    db,
                    data={**translation_data, "experience_config_id": self.id},
                )

            if config_updated or translation_updated:
                create_historical_record_for_config_and_translation(
                    db,
                    privacy_experience_config=self,
                    experience_translation=translation,
                )

        # Deletes any Experience Translations that were not supplied in the request
        delete_experience_config_translations(
            db=db,
            privacy_experience_config=self,
            request_translations=request_translations,
        )

        # Link regions to this PrivacyExperienceConfig via the PrivacyExperience table
        upsert_privacy_experiences_after_config_update(db, self, regions)

        # Link Privacy Notices to this Privacy Experience config via the ExperienceNotices table
        link_notices_to_experience_config(
            db, notice_ids=privacy_notice_ids, experience_config=self
        )
        # Link Properties to this Privacy Experience config via the PrivacyExperienceConfigProperty table
        link_properties_to_experience_config(db, properties, self)

        return self  # type: ignore[return-value]

    def dry_update(self, *, data: dict[str, Any]) -> PrivacyExperienceConfig:
        """
        A utility method to get an updated ExperienceConfig without saving it to the db.

        This is used to see what an object update would look like, in memory,
        without actually persisting the update to the db
        """
        updated_attributes = dry_update_data(resource=self, data_updates=data)
        updated_attributes.pop("regions", [])
        updated_attributes.pop("translations", [])
        # Updated privacy notice ids from the request will be in this format
        updated_attributes.pop("privacy_notice_ids", [])
        # Existing privacy notices on the ExperienceConfig need to be popped off here as well
        # to prevent the ExperienceConfig "dry_update" from being added to Session.new
        # (which would cause another PrivacyExperienceConfig to be created!)
        updated_attributes.pop("privacy_notices", [])
        updated_attributes.pop("properties", [])

        return PrivacyExperienceConfig(**updated_attributes)

    def dry_update_translations(
        self, data: list[dict[str, Any]]
    ) -> List[ExperienceTranslation]:
        """A utility method to get updated ExperienceTranslations without saving them to the db"""
        dry_updated_translations = []
        for translation_data in data:
            existing_translation = self.get_translation_by_language(
                Session.object_session(self), translation_data.get("language")
            )
            if existing_translation:
                updated_attributes: Dict = dry_update_data(
                    existing_translation, translation_data
                )
            else:
                updated_attributes = translation_data
            dry_updated_translations.append(ExperienceTranslation(**updated_attributes))
        return dry_updated_translations


class ExperienceTranslation(ExperienceTranslationBase, Base):
    """Stores all the translations for a given Experience Config"""

    experience_config_id = Column(
        String,
        ForeignKey(PrivacyExperienceConfig.id_field_path),
        nullable=False,
        index=True,
    )

    language = Column(
        EnumColumn(
            SupportedLanguage,
            native_enum=False,
            values_callable=lambda x: [
                i.value for i in x
            ],  # allows enum _values_ to be stored rather than name
        ),
        nullable=False,
    )  # Overridding language on ExperienceTranslationBase to make this non-nullable

    __table_args__ = (
        UniqueConstraint(
            "language", "experience_config_id", name="experience_translation"
        ),
    )

    histories: RelationshipProperty[AppenderQuery] = relationship(
        "PrivacyExperienceConfigHistory",
        backref="experience_translation",
        lazy="dynamic",
        order_by="PrivacyExperienceConfigHistory.created_at",
    )

    @property
    def version(self) -> Optional[float]:
        """Convenience property that returns the latest version number of the translation"""
        return (
            self.experience_config_history.version  # type: ignore[return-value]
            if self.experience_config_history
            else None
        )

    @property
    def experience_config_history(self) -> Optional[PrivacyExperienceConfigHistory]:
        """Convenience property that returns the experience config history for the latest version.

        Note that there are possibly many historical records for the given experience config translation,
        this just returns the current corresponding historical record.
        """
        # Histories are sorted at the relationship level
        return self.histories[-1] if self.histories.count() else None

    @property
    def privacy_experience_config_history_id(self) -> Optional[str]:
        """Convenience property that returns the experience config history id for the latest version.

        Note that there are possibly many historical records for the given experience config translation, this just returns the current
        corresponding historical record.
        """
        return (
            self.experience_config_history.id
            if self.experience_config_history
            else None
        )


class DeprecatedPrivacyExperienceConfigHistoryFields:
    """Fields we no longer collect and save, but are retaining on early records for auditing purposes"""

    banner_enabled = Column(
        String(), index=True
    )  # No longer collected, this is now a function of the experience config type itself


class PrivacyExperienceConfigHistory(
    ExperienceTranslationBase,
    PrivacyExperienceConfigBase,
    DeprecatedPrivacyExperienceConfigHistoryFields,
    Base,
):
    """Experience Config History table for auditing purposes.

    When an Experience Config and/or an Experience Translation is modified, a new version is
    created here that stores a snapshot of these records combined.  Consent reporting can contain
    an id to this resource which preserves the details of the Experience viewed by the end user.
    """

    origin = Column(String, ForeignKey(ExperienceConfigTemplate.id_field_path))

    translation_id = Column(
        String,
        ForeignKey(ExperienceTranslation.id_field_path, ondelete="SET NULL"),
        index=True,
    )  # If a translation is deleted, this is set to null, but the overall record remains in the database for reporting purposes

    version = Column(Float, nullable=False, default=1.0)


class PrivacyExperience(Base):
    """Privacy Experiences connect a region to a shared PrivacyExperienceConfig.

    Privacy Experiences are queried by end-users in a specific region.  The configuration is loaded
    from their PrivacyExperienceConfig.
    """

    region = Column(EnumColumn(PrivacyNoticeRegion), nullable=False, index=True)

    experience_config_id = Column(
        String,
        ForeignKey(PrivacyExperienceConfig.id_field_path),
        nullable=False,
        index=True,
    )

    experience_config = relationship(
        "PrivacyExperienceConfig",
        back_populates="experiences",
        uselist=False,
    )

    @property
    def component(self) -> Optional[ComponentType]:
        """For backwards compatibility, returns the component from the attached Privacy Experience Config
        This used to be stored at the PrivacyExperience level too.
        """
        if not self.experience_config_id:
            return None
        return self.experience_config.component  # type: ignore[return-value]

    @property
    def show_banner(self) -> bool:
        """Backwards compatible property for whether the banner should be shown.

        Logic used to be much more complex and calculated at runtime. Now this can be derived from just the component type
        """
        if self.component in [
            ComponentType.tcf_overlay,
            ComponentType.banner_and_modal,
            ComponentType.overlay,
        ]:  # Overlay type is deprecated. For backwards compatibility.
            return True

        return False

    # Attribute that can be added as the result of "get_related_privacy_notices". Privacy notices aren't directly
    # related to experiences.
    privacy_notices: List[PrivacyNotice] = []
    # TCF attributes that can be added at runtime as the result of "get_related_tcf_contents"
    tcf_purpose_consents: List = []
    tcf_purpose_legitimate_interests: List = []
    tcf_special_purposes: List = []
    tcf_vendor_consents: List = []
    tcf_vendor_legitimate_interests: List = []
    tcf_features: List = []
    tcf_special_features: List = []
    tcf_system_consents: List = []
    tcf_system_legitimate_interests: List = []
    gvl: Optional[Dict] = {}
    gvl_translations: Optional[Dict] = {}
    # TCF Developer-Friendly Meta added at runtime as the result of build_tc_data_for_mobile
    meta: Dict = {}

    @property
    def region_country(self) -> str:
        """The experience's country, based on naming convention of its region string."""
        return region_country(self.region.value)  # type: ignore[attr-defined]

    @staticmethod
    def get_experiences_by_region_and_component(
        db: Session, region: str, component: ComponentType
    ) -> Query:
        """Utility method to load experiences for a given region and component type"""
        return (
            db.query(PrivacyExperience)
            .join(
                PrivacyExperienceConfig,
                PrivacyExperienceConfig.id == PrivacyExperience.experience_config_id,
            )
            .filter(
                PrivacyExperience.region == region,
                PrivacyExperienceConfig.component  # pylint: disable=comparison-with-callable
                == component,
            )
        )


def upsert_privacy_experiences_after_config_update(
    db: Session,
    experience_config: PrivacyExperienceConfig,
    regions: List[PrivacyNoticeRegion],
) -> List[PrivacyNoticeRegion]:
    """
    Links regions to a PrivacyExperienceConfig by adding or removing PrivacyExperience records.
    """
    current_regions: List[PrivacyNoticeRegion] = experience_config.regions
    removed_regions: List[PrivacyNoticeRegion] = (
        [  # Regions that were not in the request, but currently attached to the Config
            PrivacyNoticeRegion(reg)
            for reg in {reg.value for reg in current_regions}.difference(
                {reg.value for reg in regions}
            )
        ]
    )

    # Delete any PrivacyExperiences whose regions are not in the request
    experience_config.experiences.filter(  # type: ignore[call-arg]
        PrivacyExperience.region.in_(removed_regions)
    ).delete()

    for region in regions:
        existing_experience = (
            db.query(PrivacyExperience)
            .filter(
                PrivacyExperience.experience_config_id == experience_config.id,
                PrivacyExperience.region == region,
            )
            .first()
        )

        if not existing_experience:
            # Create a Privacy Experience for any new regions
            PrivacyExperience.create(
                db,
                data={
                    "region": region,
                    "experience_config_id": experience_config.id,
                },
            )

    return experience_config.regions


def region_country(region: str) -> str:
    """
    Utility function to extract the country string from a region string,
    based on naming convention (i.e. `country_subregion`)
    """
    return region.split("_")[0]


def link_notices_to_experience_config(
    db: Session,
    notice_ids: List[str],
    experience_config: PrivacyExperienceConfig,
) -> List[PrivacyNotice]:
    """
    Link supplied Notices to ExperienceConfig and unlink any notices not supplied.
    """
    new_notices: Query = db.query(PrivacyNotice).filter(
        PrivacyNotice.id.in_(notice_ids)
    )

    for notice in new_notices:
        if notice not in experience_config.privacy_notices:
            experience_config.privacy_notices.append(notice)

    to_remove: Set[PrivacyNotice] = set(
        notice for notice in experience_config.privacy_notices
    ) - set(notice for notice in new_notices)

    for privacy_notice in to_remove:
        experience_config.privacy_notices.remove(privacy_notice)

    experience_config.save(db)
    return experience_config.privacy_notices


def link_properties_to_experience_config(
    db: Session,
    properties: List[Dict[str, Any]],
    experience_config: PrivacyExperienceConfig,
) -> List[Property]:
    """
    Link supplied properties to ExperienceConfig and unlink any properties not supplied.
    """
    new_properties = (
        db.query(Property)
        .filter(Property.id.in_([prop["id"] for prop in properties]))
        .all()
    )
    experience_config.properties = new_properties
    experience_config.save(db)
    return experience_config.properties


def create_historical_record_for_config_and_translation(
    db: Session,
    privacy_experience_config: PrivacyExperienceConfig,
    experience_translation: ExperienceTranslation,
) -> None:
    """
    Create a PrivacyExperienceConfigHistory record that preserves changes from the ExperienceTranslation and/or its
    PrivacyExperienceConfig for consent reporting purposes.

    The id of this record is used to save more context around what an end user was shown when saving privacy preferences.
    """
    existing_version: float = experience_translation.version or 0.0
    history_data: dict = create_historical_data_from_record(privacy_experience_config)
    history_data.pop("privacy_notices", None)
    history_data.pop("translations", None)
    history_data.pop("properties", None)

    updated_translation_data: dict = create_historical_data_from_record(
        experience_translation
    )
    # Translations have FK's back to experience config but the historical data does not
    updated_translation_data.pop("experience_config_id", None)

    # Create a historical record for reporting purposes, which versions
    # elements from both the PrivacyExperienceConfig and ExperienceTranslation
    PrivacyExperienceConfigHistory.create(
        db,
        data={
            **history_data,
            **updated_translation_data,
            "translation_id": experience_translation.id,
            "version": existing_version + 1.0,
        },
        check_name=False,
    )


def delete_experience_config_translations(
    db: Session,
    privacy_experience_config: PrivacyExperienceConfig,
    request_translations: Dict,
) -> None:
    """Removes any translations that are currently stored on the PrivacyExperienceConfig
    but not in the update request"""
    experience_translations: List[ExperienceTranslation] = (
        privacy_experience_config.translations
    )
    translations_to_remove: Set[SupportedLanguage] = set(  # type: ignore[assignment]
        translation.language for translation in experience_translations
    ).difference(
        set(translation.get("language") for translation in request_translations)
    )

    db.query(ExperienceTranslation).filter(
        ExperienceTranslation.language.in_(translations_to_remove),
        ExperienceTranslation.experience_config_id == privacy_experience_config.id,
    ).delete()
    db.commit()
