from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type
from uuid import uuid4

from sqlalchemy import Boolean, Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Query, RelationshipProperty, Session, relationship
from sqlalchemy.orm.dynamic import AppenderQuery

from fides.api.db.base_class import Base
from fides.api.models.custom_asset import CustomAsset
from fides.api.models.privacy_notice import (
    ConsentMechanism,
    PrivacyNotice,
    PrivacyNoticeRegion,
    create_historical_data_from_record,
    update_if_modified,
)
from fides.api.schemas.language import SupportedLanguage

BANNER_CONSENT_MECHANISMS: Set[ConsentMechanism] = {
    ConsentMechanism.notice_only,
    ConsentMechanism.opt_in,
}


class ExperienceNotices(Base):
    """Many-to-many table that stores which Notices are on which Experience Configs"""

    def generate_uuid(self) -> str:
        """
        Generates a uuid with a prefix based on the tablename to be used as the
        record's ID value
        """
        try:
            # `self` in this context is an instance of
            # sqlalchemy.dialects.postgresql.psycopg2.PGExecutionContext_psycopg2
            prefix = f"{self.current_column.table.name[:3]}_"  # type: ignore
        except AttributeError:
            # If the table name is unavailable for any reason, we don't
            # need to use it
            prefix = ""
        uuid = str(uuid4())
        return f"{prefix}{uuid}"

    id = Column(String(255), default=generate_uuid)

    notice_id = Column(
        String,
        ForeignKey("privacynotice.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        primary_key=True,
    )
    experience_config_id = Column(
        String,
        ForeignKey("privacyexperienceconfig.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        primary_key=True,
    )


class ComponentType(Enum):
    """
    The component type - not formalized in the db
    """

    overlay = "overlay"  # Overlay means banner + modal combined.
    privacy_center = "privacy_center"
    modal = "modal"
    tcf_overlay = "tcf_overlay"  # TCF Banner + modal combined


FidesJSUXTypes: List = [
    ComponentType.overlay,
    ComponentType.modal,
]


class BannerEnabled(Enum):
    """
    Whether the banner should display - not formalized in the db
    """

    always_enabled = "always_enabled"
    enabled_where_required = "enabled_where_required"  # If the user's region has at least one opt-in or notice-only notice
    always_disabled = "always_disabled"


class ExperienceConfigTemplate(Base):
    """Table for out-of-the-box Experience Configurations"""

    regions = Column(
        ARRAY(EnumColumn(PrivacyNoticeRegion, native_enum=False)),
    )
    component = Column(EnumColumn(ComponentType), nullable=False)
    privacy_notice_keys = Column(
        ARRAY(String)
    )  # A list of notice keys which should correspond to a subset of out-of-the-box notice keys
    translations = Column(ARRAY(JSONB))
    disabled = Column(Boolean, nullable=False, default=True)
    dismissable = Column(Boolean, nullable=False, default=True, server_default="t")
    allow_language_selection = Column(
        Boolean, nullable=False, default=True, server_default="t"
    )


class ExperienceTranslationBase:
    """Base schema for Experience translations"""

    language = Column(
        EnumColumn(
            SupportedLanguage,
            native_enum=False,
            values_callable=lambda x: [
                i.value for i in x
            ],  # allows enum _values_ to be stored rather than name
        ),
        nullable=False,
    )

    accept_button_label = Column(String)
    acknowledge_button_label = Column(String)
    banner_description = Column(String)
    banner_title = Column(String)
    description = Column(String)
    is_default = Column(Boolean, nullable=False, default=False)

    privacy_policy_link_label = Column(String)
    privacy_policy_url = Column(String)
    privacy_preferences_link_label = Column(String)
    reject_button_label = Column(String)
    save_button_label = Column(String)
    title = Column(String)


class ExperienceConfigBase:
    """Base schema for PrivacyExperienceConfig."""

    accept_button_label = Column(
        String
    )  # TODO pending removal in favor of ExperienceTranslation
    acknowledge_button_label = Column(
        String
    )  # TODO pending removal in favor of ExperienceTranslation
    banner_description = Column(
        String
    )  # TODO pending removal in favor of ExperienceTranslation
    banner_enabled = Column(
        EnumColumn(BannerEnabled), index=True
    )  # TODO pending removal
    banner_title = Column(
        String
    )  # TODO pending removal in favor of ExperienceTranslation
    component = Column(EnumColumn(ComponentType), nullable=False, index=True)
    description = Column(
        String
    )  # TODO pending removal in favor of ExperienceTranslation
    disabled = Column(Boolean, nullable=False, default=True)
    privacy_policy_link_label = Column(
        String
    )  # TODO pending removal in favor of ExperienceTranslation
    privacy_policy_url = Column(
        String
    )  # TODO pending removal in favor of ExperienceTranslation
    privacy_preferences_link_label = Column(
        String
    )  # TODO pending removal in favor of ExperienceTranslation
    reject_button_label = Column(
        String
    )  # TODO pending removal in favor of ExperienceTranslation
    save_button_label = Column(
        String
    )  # TODO pending removal in favor of ExperienceTranslation
    title = Column(String)  # TODO pending removal in favor of ExperienceTranslation
    version = Column(Float, nullable=False, default=1.0)  # TODO pending removal


class PrivacyExperienceConfig(ExperienceConfigBase, Base):
    """Experience Config are details shared among multiple Privacy Experiences.

    An Experience Config can have multiple translations, multiple notices, and multiple
    regions (Privacy Experiences) linked to it.
    """

    origin = Column(String, ForeignKey(ExperienceConfigTemplate.id_field_path))
    dismissable = Column(Boolean, nullable=False, default=True, server_default="t")
    allow_language_selection = Column(
        Boolean, nullable=False, default=True, server_default="t"
    )
    custom_asset_id = Column(String, ForeignKey(CustomAsset.id_field_path))
    is_default = Column(Boolean, nullable=False, default=False)  # TODO will be removed
    name = Column(String)

    experiences = relationship(
        "PrivacyExperience",
        back_populates="experience_config",
        lazy="dynamic",
    )

    privacy_notices: RelationshipProperty[List[PrivacyNotice]] = relationship(
        "PrivacyNotice",
        secondary="experiencenotices",
        back_populates="experience_configs",
        lazy="selectin",
    )

    translations: RelationshipProperty[List[ExperienceTranslation]] = relationship(
        "ExperienceTranslation",
        backref="privacy_experience_config",
        lazy="selectin",
        order_by="ExperienceTranslation.created_at",
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
        - Adds/removes Notices to the Experience Config
        """
        translations = data.pop("translations", [])
        regions = data.pop("regions", [])
        privacy_notice_ids = data.pop("privacy_notice_ids", [])
        data.pop(
            "id", None
        )  # Default templates may have ids but we don't want to use them here

        experience_config: PrivacyExperienceConfig = super().create(
            db=db, data=data, check_name=check_name
        )

        for translation_data in translations:
            data.pop(
                "id", None
            )  # Default Experience Configs have id specified but we don't want to use the same id for the historical record
            translation = ExperienceTranslation.create(
                db,
                data={**translation_data, "experience_config_id": experience_config.id},
            )
            PrivacyExperienceConfigHistory.create(
                db,
                data={**data, **translation_data, "translation_id": translation.id},
                check_name=False,
            )

        upsert_privacy_experiences_after_config_update(db, experience_config, regions)
        link_notices_to_experience_config(
            db, notice_ids=privacy_notice_ids, experience_config=experience_config
        )

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

        config_updated = update_if_modified(self, db=db, data=data)

        for translation_data in request_translations:
            existing_translation: Optional[
                ExperienceTranslation
            ] = self.get_translation_by_language(db, translation_data.get("language"))
            if existing_translation:
                translation_updated: bool = update_if_modified(
                    existing_translation,
                    db=db,
                    data={**translation_data, "experience_config_id": self.id},
                )
                translation = existing_translation
            else:
                translation_updated = True
                translation = ExperienceTranslation.create(
                    db,
                    data={**translation_data, "experience_config_id": self.id},
                )

            if config_updated or translation_updated:
                existing_version: float = translation.version or 0.0
                history_data: dict = create_historical_data_from_record(self)
                history_data.pop("privacy_notices", None)
                history_data.pop("translations", None)
                updated_translation_data: dict = create_historical_data_from_record(
                    translation
                )
                PrivacyExperienceConfigHistory.create(
                    db,
                    data={
                        **history_data,
                        **updated_translation_data,
                        "translation_id": translation.id,
                        "version": existing_version + 1.0,
                    },
                    check_name=False,
                )

        experience_translations: List[ExperienceTranslation] = self.translations
        translations_to_remove: Set[SupportedLanguage] = set(  # type: ignore[assignment]
            translation.language for translation in experience_translations
        ).difference(
            set(translation.get("language") for translation in request_translations)
        )

        db.query(ExperienceTranslation).filter(
            ExperienceTranslation.language.in_(translations_to_remove),
            ExperienceTranslation.experience_config_id == self.id,
        ).delete()
        db.commit()

        upsert_privacy_experiences_after_config_update(db, self, regions)
        link_notices_to_experience_config(
            db, notice_ids=privacy_notice_ids, experience_config=self
        )

        return self  # type: ignore[return-value]

    def dry_update(self, *, data: dict[str, Any]) -> PrivacyExperienceConfig:
        """
        A utility method to get an updated ExperienceConfig without saving it to the db.

        This is used to see what an object update would look like, in memory,
        without actually persisting the update to the db
        """
        cloned_attributes = self.__dict__.copy()
        for key, val in data.items():
            cloned_attributes[key] = val
        cloned_attributes.pop("_sa_instance_state")
        cloned_attributes.pop("regions", [])
        cloned_attributes.pop("translations", [])
        cloned_attributes.pop("privacy_notice_ids", [])
        cloned_attributes.pop("id", None)
        return PrivacyExperienceConfig(**cloned_attributes)

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
                cloned_attributes = existing_translation.__dict__.copy()
                for key, val in translation_data.items():
                    cloned_attributes[key] = val
                cloned_attributes.pop("_sa_instance_state")
                cloned_attributes.pop("id")
            else:
                cloned_attributes = translation_data
            dry_updated_translations.append(ExperienceTranslation(**cloned_attributes))
        return dry_updated_translations

    @classmethod
    def get_default_config(
        cls, db: Session, component: ComponentType
    ) -> Optional[PrivacyExperienceConfig]:
        """Load the first default config of a given component type
        TODO pending removal - there is no longer a "default" config
        """
        return (
            db.query(PrivacyExperienceConfig)
            .filter(PrivacyExperienceConfig.component == component)
            .filter(PrivacyExperienceConfig.is_default.is_(True))
            .first()
        )


class ExperienceTranslation(ExperienceTranslationBase, Base):
    """Stores all the translations for a given Experience Config"""

    experience_config_id = Column(
        String, ForeignKey(PrivacyExperienceConfig.id_field_path), nullable=False
    )

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
    def experience_config_history_id(self) -> Optional[str]:
        """Convenience property that returns the experience config history id for the latest version.

        Note that there are possibly many historical records for the given experience config translation, this just returns the current
        corresponding historical record.
        """
        return (
            self.experience_config_history.id
            if self.experience_config_history
            else None
        )


class PrivacyExperienceConfigHistory(ExperienceTranslationBase, Base):
    """Experience Config History - stores the history of how the config has changed over time
    Both an ExperienceTranslation and its ExperienceConfig are versioned here together.
    """

    name = Column(String)

    origin = Column(String, ForeignKey(ExperienceConfigTemplate.id_field_path))
    dismissable = Column(Boolean, nullable=False, default=True, server_default="t")
    allow_language_selection = Column(
        Boolean, nullable=False, default=True, server_default="t"
    )
    custom_asset_id = Column(String, ForeignKey(CustomAsset.id_field_path))
    disabled = Column(Boolean, nullable=False, default=True)

    experience_config_id = Column(
        String, ForeignKey(PrivacyExperienceConfig.id_field_path), nullable=True
    )  # TODO slated for removal after data migration

    translation_id = Column(
        String, ForeignKey(ExperienceTranslation.id_field_path, ondelete="SET NULL")
    )

    version = Column(Float, nullable=False, default=1.0)

    banner_enabled = Column(
        EnumColumn(BannerEnabled), index=True
    )  # TODO pending removal
    component = Column(EnumColumn(ComponentType), nullable=False, index=True)


class PrivacyExperience(Base):
    """Stores Privacy Experiences for just a single region.
    The Experience describes how to surface multiple Privacy Notices or TCF content to the
    end user in a given region.

    There can only be one component per region.  Most of the details for a given Experience
    are on the ExperienceConfig (which allows multiple Experiences to share the same
    configuration options).
    """

    region = Column(EnumColumn(PrivacyNoticeRegion), nullable=False, index=True)

    experience_config_id = Column(
        String,
        ForeignKey(PrivacyExperienceConfig.id_field_path),
        nullable=True,  # Needs an ExperienceConfig to be valid
        index=True,
    )

    experience_config = relationship(
        "PrivacyExperienceConfig",
        back_populates="experiences",
        uselist=False,
    )

    @property
    def component(self) -> Optional[ComponentType]:
        """For backwards compatibility, returns the component from the attached Privacy Experience Config"""
        if not self.experience_config_id:
            return None
        return self.experience_config.component  # type: ignore[return-value]

    @property
    def show_banner(self) -> bool:
        """Backwards compatible property for whether the banner should be shown.

        Logic used to be much more complex and calculated at runtime.  Now only certain
        UX types load banners.
        """
        if self.component in [ComponentType.tcf_overlay, ComponentType.overlay]:
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
                PrivacyExperienceConfig.component == component,
            )
        )


def get_privacy_notices_by_region_and_component(
    db: Session, regions: List[str], component: ComponentType
) -> Query:
    """
    Return relevant privacy notices that should be displayed for a certain
    region in a given component type
    """
    return (
        db.query(PrivacyNotice)
        .join(ExperienceNotices, PrivacyNotice.id == ExperienceNotices.notice_id)
        .join(
            PrivacyExperience,
            PrivacyExperience.experience_config_id
            == ExperienceNotices.experience_config_id,
        )
        .filter(
            PrivacyExperience.region.in_(regions),
            PrivacyExperienceConfig.component == component,
        )
    )


def remove_regions_from_experience_config(
    experience_config: PrivacyExperienceConfig,
    regions_to_unlink: List[PrivacyNoticeRegion],
) -> None:
    """Remove regions from a PrivacyExperienceConfig by deleting the associated PrivacyExperiences"""
    if not regions_to_unlink:
        return None

    experience_config.experiences.filter(  # type: ignore[call-arg]
        PrivacyExperience.region.in_(regions_to_unlink)
    ).delete()

    return None


def upsert_privacy_experiences_after_config_update(
    db: Session,
    experience_config: PrivacyExperienceConfig,
    regions: List[PrivacyNoticeRegion],
) -> List[PrivacyNoticeRegion]:
    """
    Keeps Privacy Experiences in sync with ExperienceConfig changes.
    Create or update PrivacyExperiences for the regions we're attempting to link to the
    ExperienceConfig.

    Assumes that components on the ExperienceConfig do not change after they're updated.
    """
    current_regions: List[PrivacyNoticeRegion] = experience_config.regions
    removed_regions: List[
        PrivacyNoticeRegion
    ] = [  # Regions that were not in the request, but currently attached to the Config
        PrivacyNoticeRegion(reg)
        for reg in {reg.value for reg in current_regions}.difference(
            {reg.value for reg in regions}
        )
    ]

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

        # If existing experience exists, refresh data
        if not existing_experience:
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

    Notices retrieved by Notice Key
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
