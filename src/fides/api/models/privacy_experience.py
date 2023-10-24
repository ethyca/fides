from __future__ import annotations

from copy import copy
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

from sqlalchemy import Boolean, Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import Float, ForeignKey, String, UniqueConstraint, and_, or_
from sqlalchemy.orm import Query, Session, relationship
from sqlalchemy.util import hybridproperty

from fides.api.db.base_class import Base
from fides.api.models.privacy_notice import (
    ConsentMechanism,
    PrivacyNotice,
    PrivacyNoticeRegion,
    create_historical_data_from_record,
    update_if_modified,
)
from fides.api.models.privacy_preference import (
    CurrentPrivacyPreference,
    LastServedNotice,
)
from fides.api.models.privacy_request import ProvidedIdentity
from fides.api.models.sql_models import System  # type: ignore[attr-defined]
from fides.api.schemas.tcf import (
    TCFFeatureRecord,
    TCFPurposeConsentRecord,
    TCFPurposeLegitimateInterestsRecord,
    TCFSpecialFeatureRecord,
    TCFSpecialPurposeRecord,
    TCFVendorConsentRecord,
    TCFVendorLegitimateInterestsRecord,
    TCFVendorRelationships,
)
from fides.api.util.tcf.tcf_experience_contents import (
    TCF_SECTION_MAPPING,
    ConsentRecordType,
    TCFExperienceContents,
)

BANNER_CONSENT_MECHANISMS: Set[ConsentMechanism] = {
    ConsentMechanism.notice_only,
    ConsentMechanism.opt_in,
}


class ComponentType(Enum):
    """
    The component type - not formalized in the db
    """

    overlay = "overlay"
    privacy_center = "privacy_center"
    tcf_overlay = "tcf_overlay"


class BannerEnabled(Enum):
    """
    Whether the banner should display - not formalized in the db
    """

    always_enabled = "always_enabled"
    enabled_where_required = "enabled_where_required"  # If the user's region has at least one opt-in or notice-only notice
    always_disabled = "always_disabled"


class ExperienceConfigBase:
    """Base schema for PrivacyExperienceConfig."""

    accept_button_label = Column(String)
    acknowledge_button_label = Column(String)
    banner_enabled = Column(EnumColumn(BannerEnabled), index=True)
    component = Column(EnumColumn(ComponentType), nullable=False, index=True)
    description = Column(String)
    disabled = Column(Boolean, nullable=False, default=False)
    is_default = Column(Boolean, nullable=False, default=False)
    privacy_policy_link_label = Column(String)
    privacy_policy_url = Column(String)
    privacy_preferences_link_label = Column(String)
    reject_button_label = Column(String)
    save_button_label = Column(String)
    title = Column(String)
    version = Column(Float, nullable=False, default=1.0)


class PrivacyExperienceConfig(ExperienceConfigBase, Base):
    """Stores common copy to be shared across multiple regions, e.g.
    banner titles, descriptions, button labels, etc.

    Can be linked to multiple PrivacyExperiences.
    """

    experiences = relationship(
        "PrivacyExperience",
        back_populates="experience_config",
        lazy="dynamic",
    )

    histories = relationship(
        "PrivacyExperienceConfigHistory",
        backref="experience_config",
        lazy="dynamic",
    )

    @property
    def regions(self) -> List[PrivacyNoticeRegion]:
        """Return the regions using this experience config"""
        return [exp.region for exp in self.experiences]  # type: ignore[attr-defined]

    @classmethod
    def create(
        cls: Type[PrivacyExperienceConfig],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> PrivacyExperienceConfig:
        """Create experience config and then clone this record into the history table for record keeping"""
        experience_config: PrivacyExperienceConfig = super().create(
            db=db, data=data, check_name=check_name
        )
        # create the history after the initial object creation succeeds, to avoid
        # writing history if the creation fails and so that we can get the generated ID
        data.pop(
            "id", None
        )  # Default Experience Configs have id specified but we don't want to use the same id for the historical record
        history_data = {
            **data,
            "experience_config_id": experience_config.id,
        }
        PrivacyExperienceConfigHistory.create(db, data=history_data, check_name=False)
        return experience_config

    def update(self, db: Session, *, data: dict[str, Any]) -> PrivacyExperienceConfig:
        """
        Overrides the base update method to automatically bump the version of the
        PrivacyExperienceConfig record and also create a new PrivacyExperienceConfigHistory entry
        """
        resource, updated = update_if_modified(self, db=db, data=data)

        if updated:
            history_data = create_historical_data_from_record(resource)
            history_data["experience_config_id"] = self.id

            PrivacyExperienceConfigHistory.create(
                db, data=history_data, check_name=False
            )

        return resource  # type: ignore[return-value]

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
        return PrivacyExperienceConfig(**cloned_attributes)

    @hybridproperty
    def experience_config_history_id(self) -> Optional[str]:
        """Convenience property that returns the experience config id for the current version.

        Note that there are possibly many historical records for the given experience config, this just returns the current
        corresponding historical record.
        """
        history: PrivacyExperienceConfigHistory = self.histories.filter_by(  # type: ignore # pylint: disable=no-member
            version=self.version
        ).first()
        return history.id if history else None

    @classmethod
    def get_default_config(
        cls, db: Session, component: ComponentType
    ) -> Optional[PrivacyExperienceConfig]:
        """Load the first default config of a given component type"""
        return (
            db.query(PrivacyExperienceConfig)
            .filter(PrivacyExperienceConfig.component == component)
            .filter(PrivacyExperienceConfig.is_default.is_(True))
            .first()
        )


class PrivacyExperienceConfigHistory(ExperienceConfigBase, Base):
    """Experience Config History - stores the history of how the config has changed over time"""

    experience_config_id = Column(
        String, ForeignKey(PrivacyExperienceConfig.id_field_path), nullable=False
    )


class PrivacyExperience(Base):
    """Stores Privacy Experiences for a given just a single region.  The Experience describes how to surface
    multiple Privacy Notices or TCF content to the end user in a given region.

    There can only be one component per region.
    """

    component = Column(EnumColumn(ComponentType), nullable=False)
    region = Column(EnumColumn(PrivacyNoticeRegion), nullable=False, index=True)

    experience_config_id = Column(
        String,
        ForeignKey(PrivacyExperienceConfig.id_field_path),
        nullable=True,
        index=True,
    )

    # There can only be one component per region
    __table_args__ = (UniqueConstraint("region", "component", name="region_component"),)

    experience_config = relationship(
        "PrivacyExperienceConfig",
        back_populates="experiences",
        uselist=False,
    )

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

    # Attribute that is cached on the PrivacyExperience object by "get_should_show_banner", calculated at runtime
    show_banner: bool

    def get_should_show_banner(
        self, db: Session, show_disabled: Optional[bool] = True
    ) -> bool:
        """Returns True if this Experience should be delivered by a banner

        Relevant privacy notices are queried at runtime.
        """
        if self.component == ComponentType.tcf_overlay:
            # For now, just returning that the TCF Overlay should always show a banner,
            # but this is subject to change.
            return True

        if self.component != ComponentType.overlay:
            return False

        if self.experience_config:
            if self.experience_config.banner_enabled == BannerEnabled.always_disabled:
                return False

            if self.experience_config.banner_enabled == BannerEnabled.always_enabled:
                return True

        privacy_notice_query = get_privacy_notices_by_region_and_component(
            db, self.region, self.component  # type: ignore[arg-type]
        )
        if show_disabled is False:
            privacy_notice_query = privacy_notice_query.filter(
                PrivacyNotice.disabled.is_(False)
            )

        return bool(
            privacy_notice_query.filter(
                PrivacyNotice.consent_mechanism.in_(BANNER_CONSENT_MECHANISMS)
            ).count()
        )

    def get_related_privacy_notices(
        self,
        db: Session,
        show_disabled: Optional[bool] = True,
        systems_applicable: Optional[bool] = False,
        fides_user_provided_identity: Optional[ProvidedIdentity] = None,
    ) -> List[PrivacyNotice]:
        """Return privacy notices that overlap on at least one region
        and match on ComponentType

        If show_disabled=False, only return enabled notices.
        If fides user provided identity supplied, additionally lookup any saved
        preferences for that user id and attach if they exist.
        """
        if self.component == ComponentType.tcf_overlay:
            return []
        privacy_notice_query = get_privacy_notices_by_region_and_component(
            db, self.region, self.component  # type: ignore[arg-type]
        )
        if show_disabled is False:
            privacy_notice_query = privacy_notice_query.filter(
                PrivacyNotice.disabled.is_(False)
            )

        if systems_applicable:
            data_uses: set[str] = System.get_data_uses(
                System.all(db), include_parents=True
            )
            privacy_notice_query = privacy_notice_query.filter(PrivacyNotice.data_uses.overlap(data_uses))  # type: ignore

        if not fides_user_provided_identity:
            return privacy_notice_query.order_by(PrivacyNotice.created_at.desc()).all()

        notices: List[PrivacyNotice] = []
        for notice in privacy_notice_query.order_by(PrivacyNotice.created_at.desc()):
            cache_saved_and_served_on_consent_record(
                db=db,
                consent_record=notice,
                fides_user_provided_identity=fides_user_provided_identity,
                record_type=ConsentRecordType.privacy_notice_id,
            )
            notices.append(notice)

        return notices

    def update_with_tcf_contents(
        self,
        db: Session,
        base_tcf_contents: TCFExperienceContents,
        fides_user_provided_identity: Optional[ProvidedIdentity],
    ) -> bool:
        """
        Supplements the given TCF experience in-place with TCF contents at runtime, and returns whether
        TCF contents exist.

        The TCF experience is determined by systems in the data map as well as any previous records
        of a user being served TCF components and/or consenting to any individual TCF components.
        """
        if self.component == ComponentType.tcf_overlay:
            tcf_contents = copy(base_tcf_contents)

            has_tcf_contents = False
            for (
                tcf_section_name,
                corresponding_db_field_name,
            ) in TCF_SECTION_MAPPING.items():
                # Loop through each top-level section in the TCF Contents
                tcf_section: List = getattr(tcf_contents, tcf_section_name)
                for record in tcf_section:
                    # Loop through each record within a TCF section, and cache
                    # any previously saved preferences if applicable
                    cache_saved_and_served_on_consent_record(
                        db,
                        record,
                        fides_user_provided_identity=fides_user_provided_identity,
                        record_type=corresponding_db_field_name,
                    )
                # Now supplement the TCF Experience with this new section
                setattr(self, tcf_section_name, tcf_section)
                if tcf_section:
                    has_tcf_contents = True

            if has_tcf_contents:
                return True

        return False

    @staticmethod
    def create_default_experience_for_region(
        db: Session, region: PrivacyNoticeRegion, component: ComponentType
    ) -> PrivacyExperience:
        """Creates an Experience for a given Component Type and Region and links
        to default copy (ExperienceConfig)"""
        experience_data: Dict = {
            "region": region,
            "component": component,
        }
        default_config: Optional[
            PrivacyExperienceConfig
        ] = PrivacyExperienceConfig.get_default_config(db, component)

        if default_config:
            experience_data["experience_config_id"] = default_config.id

        return PrivacyExperience.create(
            db=db,
            data=experience_data,
        )

    @staticmethod
    def get_experience_by_region_and_component(
        db: Session, region: str, component: ComponentType
    ) -> Optional[PrivacyExperience]:
        """Load an experience for a given region and component type"""
        return (
            db.query(PrivacyExperience)
            .filter(
                PrivacyExperience.region == region,
                PrivacyExperience.component == component,
            )
            .first()
        )

    @staticmethod
    def get_overlay_and_privacy_center_experience_by_region(
        db: Session, region: str
    ) -> Tuple[Optional[PrivacyExperience], Optional[PrivacyExperience]]:
        """Load both the overlay and privacy center experience for a given region

        TCF overlays are not returned here.  This method is used in building experiences when Notices
        are created, which is not applicable for TCF.
        """
        overlay_experience: Optional[
            PrivacyExperience
        ] = PrivacyExperience.get_experience_by_region_and_component(
            db=db, region=region, component=ComponentType.overlay
        )

        privacy_center_experience: Optional[
            PrivacyExperience
        ] = PrivacyExperience.get_experience_by_region_and_component(
            db=db, region=region, component=ComponentType.privacy_center
        )

        return overlay_experience, privacy_center_experience

    def unlink_experience_config(self, db: Session) -> PrivacyExperience:
        """Removes the experience config

        Note that neither the Experience Config or Experience are deleted; we're only removing
        a FK if it exists.
        """
        return self.update(  # type: ignore[return-value]
            db,
            data={"experience_config_id": None, "experience_config_history_id": None},
        )

    def link_default_experience_config(self, db: Session) -> PrivacyExperience:
        """Replace config from experience with default config

        Replaces the FK only; does not delete Privacy Experiences or Privacy Experience Configs
        """
        default_config: Optional[
            PrivacyExperienceConfig
        ] = PrivacyExperienceConfig.get_default_config(
            db, self.component  # type: ignore[arg-type]
        )
        return self.update(  # type: ignore[return-value]
            db,
            data={
                "experience_config_id": default_config.id if default_config else None,
                "experience_config_history_id": default_config.experience_config_history_id
                if default_config
                else None,
            },
        )


def get_privacy_notices_by_region_and_component(
    db: Session, region: PrivacyNoticeRegion, component: ComponentType
) -> Query:
    """
    Return relevant privacy notices that should be displayed for a certain
    region in a given component type
    """
    return (
        db.query(PrivacyNotice)
        .filter(PrivacyNotice.regions.any(region.value))  # type: ignore[attr-defined]
        .filter(
            or_(
                and_(
                    component == ComponentType.overlay,
                    PrivacyNotice.displayed_in_overlay,
                ),
                and_(
                    component == ComponentType.privacy_center,
                    PrivacyNotice.displayed_in_privacy_center,
                ),
            )
        )
    )


def upsert_privacy_experiences_after_notice_update(
    db: Session, affected_regions: List[PrivacyNoticeRegion]
) -> List[PrivacyExperience]:
    """
    Keeps Privacy Experiences in sync with *PrivacyNotices* changes.
    Create or update "overlay" or "privacy center" PrivacyExperiences based on the PrivacyNotices in the "affected_regions".
    To be called whenever PrivacyNotices are created or updated (pass in any regions that were potentially affected)

    PrivacyExperiences should not be deleted.  It's okay if no notices are associated with an Experience.
    """
    added_experiences: List[PrivacyExperience] = []

    def new_experience_needed(
        existing_experience: Optional[PrivacyExperience], related_notices: Query
    ) -> bool:
        """Do we need to create a new experience to match the notices?"""
        return not existing_experience and bool(related_notices.count())

    for region in affected_regions:
        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_overlay_and_privacy_center_experience_by_region(
            db=db, region=region.value
        )

        privacy_center_notices: Query = get_privacy_notices_by_region_and_component(
            db, region, ComponentType.privacy_center
        )
        overlay_notices: Query = get_privacy_notices_by_region_and_component(
            db, region, ComponentType.overlay
        )

        # See if we need to create a Privacy Center Experience for the Privacy Center Notices
        if new_experience_needed(
            existing_experience=privacy_center_experience,
            related_notices=privacy_center_notices,
        ):
            privacy_center_experience = (
                PrivacyExperience.create_default_experience_for_region(
                    db, region, ComponentType.privacy_center
                )
            )
            added_experiences.append(privacy_center_experience)

        # See if we need to create a new overlay Experience for the overlay Notices.
        if new_experience_needed(
            existing_experience=overlay_experience, related_notices=overlay_notices
        ):
            overlay_experience = PrivacyExperience.create_default_experience_for_region(
                db, region, ComponentType.overlay
            )
            added_experiences.append(overlay_experience)

    return added_experiences


def remove_config_from_matched_experiences(
    db: Session,
    experience_config: PrivacyExperienceConfig,
    regions_to_unlink: List[PrivacyNoticeRegion],
) -> List[PrivacyNoticeRegion]:
    """Remove the config from linked PrivacyExperiences"""
    if not regions_to_unlink:
        return []

    experiences_to_unlink: List[PrivacyExperience] = experience_config.experiences.filter(  # type: ignore[call-arg]
        PrivacyExperience.region.in_(regions_to_unlink)
    ).all()

    for experience in experiences_to_unlink:
        if experience_config.is_default:
            experience.unlink_experience_config(db)
        else:
            experience.link_default_experience_config(db)
    return [experience.region for experience in experiences_to_unlink]  # type: ignore[misc]


def upsert_privacy_experiences_after_config_update(
    db: Session,
    experience_config: PrivacyExperienceConfig,
    regions: List[PrivacyNoticeRegion],
) -> Tuple[List[PrivacyNoticeRegion], List[PrivacyNoticeRegion]]:
    """
    Keeps Privacy Experiences in sync with ExperienceConfig changes.
    Create or update PrivacyExperiences for the regions we're attempting to link to the
    ExperienceConfig.

    Assumes that components on the ExperienceConfig do not change after they're updated.
    """
    linked_regions: List[PrivacyNoticeRegion] = []  # Regions that were linked

    current_regions: List[PrivacyNoticeRegion] = experience_config.regions
    removed_regions: List[
        PrivacyNoticeRegion
    ] = [  # Regions that were not in the request, but currently attached to the Config
        PrivacyNoticeRegion(reg)
        for reg in {reg.value for reg in current_regions}.difference(
            {reg.value for reg in regions}
        )
    ]
    unlinked_regions: List[
        PrivacyNoticeRegion
    ] = remove_config_from_matched_experiences(db, experience_config, removed_regions)

    for region in regions:
        existing_experience: Optional[
            PrivacyExperience
        ] = PrivacyExperience.get_experience_by_region_and_component(
            db=db, region=region, component=experience_config.component  # type: ignore[arg-type]
        )
        data = {
            "component": experience_config.component,
            "region": region,
            "experience_config_id": experience_config.id,
        }

        # If existing experience exists, link to experience config
        if existing_experience:
            if existing_experience.experience_config_id != experience_config.id:
                linked_regions.append(region)
            existing_experience.update(db, data=data)

        else:
            # If existing experience doesn't exist, create and link to experience config
            PrivacyExperience.create(
                db,
                data=data,
            )
            linked_regions.append(region)
    return linked_regions, unlinked_regions


def cache_saved_and_served_on_consent_record(
    db: Session,
    consent_record: Union[
        PrivacyNotice,
        TCFPurposeConsentRecord,
        TCFPurposeLegitimateInterestsRecord,
        TCFSpecialPurposeRecord,
        TCFFeatureRecord,
        TCFSpecialFeatureRecord,
        TCFVendorConsentRecord,
        TCFVendorLegitimateInterestsRecord,
        TCFVendorRelationships,
    ],
    fides_user_provided_identity: Optional[ProvidedIdentity],
    record_type: Optional[ConsentRecordType],
) -> None:
    """For display purposes, look up whether the resource was served to the given user and/or the user has saved
    preferences for that resource and add this to the consent_record

    Updates the consent_record in place.
    """
    if not fides_user_provided_identity:
        return

    if not record_type:
        # Some elements of the TCF form, like vendor relationships don't have saved preferences
        return

    assert not isinstance(consent_record, TCFVendorRelationships)  # For mypy

    consent_record.current_preference = None
    consent_record.outdated_preference = None
    consent_record.current_served = None
    consent_record.outdated_served = None

    # Check if we have any previously saved preferences for this user
    saved_preference = (
        CurrentPrivacyPreference.get_preference_by_type_and_fides_user_device(
            db=db,
            fides_user_provided_identity=fides_user_provided_identity,
            preference_type=record_type,
            preference_value=consent_record.id,
        )
    )
    if saved_preference:
        if saved_preference.record_is_current:
            consent_record.current_preference = saved_preference.preference
        else:
            consent_record.outdated_preference = saved_preference.preference

    # Check if we have previously served this record to this user
    served_record: Optional[
        LastServedNotice
    ] = LastServedNotice.get_last_served_for_record_type_and_fides_user_device(
        db=db,
        fides_user_provided_identity=fides_user_provided_identity,
        record_type=record_type,
        preference_value=consent_record.id,
    )

    if served_record:
        if served_record.record_is_current:
            consent_record.current_served = True
        else:
            consent_record.outdated_served = True
