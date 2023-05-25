from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional, Tuple, Type

from sqlalchemy import Boolean, Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import Float, ForeignKey, String, UniqueConstraint, and_, or_
from sqlalchemy.orm import Query, Session, relationship
from sqlalchemy.util import hybridproperty

from fides.api.db.base_class import Base
from fides.api.models.privacy_notice import PrivacyNotice, PrivacyNoticeRegion
from fides.api.models.privacy_preference import CurrentPrivacyPreference
from fides.api.models.privacy_request import ProvidedIdentity


class ComponentType(Enum):
    """
    The component type - not formalized in the db
    """

    overlay = "overlay"
    privacy_center = "privacy_center"


class BannerEnabled(Enum):
    """
    Whether the banner should display
    """

    always_enabled = "always_enabled"
    enabled_where_required = "enabled_where_required"  # If the user's region has at least one opt-in or notice-only notice
    always_disabled = "always_disabled"


class ExperienceConfigBase:
    """Base schema to share common experience config."""

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
    """Stores common experience config to be shared across multiple regions
    This largely contains all the "language" used in a given experience, e.g.
    component titles, descriptions, button labels, etc.
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
        # run through potential updates now
        for key, value in data.items():
            setattr(self, key, value)

        # only if there's a modification do we write the history record
        if db.is_modified(self):
            # on any update to a privacy experience record, its version must be incremented
            # version gets incremented by a full integer, i.e. 1.0 -> 2.0 -> 3.0
            self.version = float(self.version) + 1.0  # type: ignore
            self.save(db)

            # history record data is identical to the new privacy experience record data
            # except the experience's 'id' must be moved to the FK column
            # and is no longer the history record 'id' column
            history_data = self.__dict__.copy()
            history_data.pop("_sa_instance_state")
            history_data.pop("id")
            history_data.pop("created_at")
            history_data.pop("updated_at")
            history_data["experience_config_id"] = self.id

            PrivacyExperienceConfigHistory.create(
                db, data=history_data, check_name=False
            )

        return self

    def dry_update(self, *, data: dict[str, Any]) -> PrivacyExperienceConfig:
        """
        A utility method to get an updated object without saving it to the db.

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


class PrivacyExperienceConfigHistory(ExperienceConfigBase, Base):
    """Experience Config History - stores the history of how the config changed"""

    experience_config_id = Column(
        String, ForeignKey(PrivacyExperienceConfig.id_field_path), nullable=False
    )


class PrivacyExperienceBase:
    """Base Privacy Experience fields that are common between privacy experiences and historical records"""

    disabled = Column(Boolean, nullable=False, default=False)
    component = Column(EnumColumn(ComponentType), nullable=False)
    region = Column(EnumColumn(PrivacyNoticeRegion), nullable=False, index=True)
    version = Column(Float, nullable=False, default=1.0)


class PrivacyExperience(PrivacyExperienceBase, Base):
    """Stores Privacy Experiences for a given just a single region.
    There can only be one component per region.
    """

    experience_config_id = Column(
        String,
        ForeignKey(PrivacyExperienceConfig.id_field_path),
        nullable=True,
        index=True,
    )

    experience_config_history_id = Column(
        String,
        ForeignKey(PrivacyExperienceConfigHistory.id_field_path),
        nullable=True,
        index=True,
    )  # Also links to the historical record, so if the version of config gets updated, that
    # triggers a new version of the experience.

    # There can only be one component per region
    __table_args__ = (UniqueConstraint("region", "component", name="region_component"),)

    histories = relationship(
        "PrivacyExperienceHistory", backref="privacy_experience", lazy="dynamic"
    )

    experience_config = relationship(
        "PrivacyExperienceConfig",
        back_populates="experiences",
        uselist=False,
    )

    # Attribute that can be added as the result of "get_related_privacy_notices". Privacy notices aren't directly
    # related to experiences.
    privacy_notices: List[PrivacyNotice] = []

    @hybridproperty
    def privacy_experience_history_id(self) -> Optional[str]:
        """Convenience property that returns the historical privacy experience id for the current version.

        Note that there are possibly many historical records for the given experience, this just returns the current
        corresponding historical record.
        """
        history: PrivacyExperienceHistory = self.histories.filter_by(  # type: ignore # pylint: disable=no-member
            version=self.version
        ).first()
        return history.id if history else None

    def get_related_privacy_notices(
        self,
        db: Session,
        show_disabled: Optional[bool] = True,
        fides_user_provided_identity: Optional[ProvidedIdentity] = None,
    ) -> List[PrivacyNotice]:
        """Return privacy notices that overlap on at least one region
        and match on ComponentType

        If show_disabled=False, only return enabled notices.
        If fides user provided identity supplied, additionally lookup any saved
        preferences for that user id and attach if they exist.
        """
        privacy_notice_query = get_privacy_notices_by_region_and_component(
            db, self.region, self.component  # type: ignore[arg-type]
        )
        if show_disabled is False:
            privacy_notice_query = privacy_notice_query.filter(
                PrivacyNotice.disabled.is_(False)
            )

        if not fides_user_provided_identity:
            return privacy_notice_query.order_by(PrivacyNotice.created_at.desc()).all()

        notices: List[PrivacyNotice] = []
        for notice in privacy_notice_query.order_by(PrivacyNotice.created_at.desc()):
            saved_preference: Optional[
                CurrentPrivacyPreference
            ] = CurrentPrivacyPreference.get_preference_for_notice_and_fides_user_device(
                db=db,
                fides_user_provided_identity=fides_user_provided_identity,
                privacy_notice=notice,
            )
            if saved_preference:
                # Temporarily cache the preference for the given fides user device id in memory.
                if saved_preference.preference_matches_latest_version:
                    notice.current_preference = saved_preference.preference
                    notice.outdated_preference = None
                else:
                    notice.current_preference = None
                    notice.outdated_preference = saved_preference.preference
            notices.append(notice)

        return notices

    @classmethod
    def create(
        cls: Type[PrivacyExperience],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> PrivacyExperience:
        """Create a privacy experience and the clone this record into the history table for record keeping"""
        privacy_experience = super().create(db=db, data=data, check_name=check_name)

        # create the history after the initial object creation succeeds, to avoid
        # writing history if the creation fails and so that we can get the generated ID
        history_data = {
            **data,
            "privacy_experience_id": privacy_experience.id,
        }
        PrivacyExperienceHistory.create(db, data=history_data, check_name=False)
        return privacy_experience

    def update(self, db: Session, *, data: dict[str, Any]) -> PrivacyExperience:
        """
        Overrides the base update method to automatically bump the version of the
        PrivacyExperience record and also create a new PrivacyExperienceHistory entry
        """

        # run through potential updates now
        for key, value in data.items():
            setattr(self, key, value)

        # only if there's a modification do we write the history record
        if db.is_modified(self):
            # on any update to a privacy experience record, its version must be incremented
            # version gets incremented by a full integer, i.e. 1.0 -> 2.0 -> 3.0
            self.version = float(self.version) + 1.0  # type: ignore
            self.save(db)

            # history record data is identical to the new privacy experience record data
            # except the experience's 'id' must be moved to the FK column
            # and is no longer the history record 'id' column
            history_data = self.__dict__.copy()
            history_data.pop("_sa_instance_state")
            history_data.pop("id")
            history_data.pop("created_at")
            history_data.pop("updated_at")
            history_data["privacy_experience_id"] = self.id

            PrivacyExperienceHistory.create(db, data=history_data, check_name=False)

        return self

    @staticmethod
    def get_experience_by_region_and_component(
        db: Session, region: PrivacyNoticeRegion, component: ComponentType
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
    def get_experiences_by_region(
        db: Session, region: PrivacyNoticeRegion
    ) -> Tuple[Optional[PrivacyExperience], Optional[PrivacyExperience]]:
        """Load both the overlay and privacy center experience for a given region"""
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
        """Remove config from experience

        Removes the FK, does not remove Privacy Experiences or Privacy Experience Configs
        """
        return self.update(
            db,
            data={
                "experience_config_id": None,
                "experience_config_history_id": None,
            },
        )


class PrivacyExperienceHistory(PrivacyExperienceBase, Base):
    """Stores the history of a privacy experience for a given region for Consent Reporting"""

    version = Column(Float, nullable=False, default=1.0)
    privacy_experience_id = Column(
        String, ForeignKey(PrivacyExperience.id_field_path), nullable=False, index=True
    )
    experience_config_id = Column(
        String,
        ForeignKey(PrivacyExperienceConfig.id_field_path),
        nullable=True,
        index=True,
    )

    experience_config_history_id = Column(
        String,
        ForeignKey(PrivacyExperienceConfigHistory.id_field_path),
        nullable=True,
        index=True,
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
    Create or update PrivacyExperiences based on the PrivacyNotices in the "affected_regions".
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
        ) = PrivacyExperience.get_experiences_by_region(db=db, region=region)

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
            privacy_center_experience = PrivacyExperience.create(
                db=db,
                data={
                    "region": region,
                    "component": ComponentType.privacy_center,
                },
            )
            added_experiences.append(privacy_center_experience)

        # See if we need to create a new overlay Experience for the overlay Notices.
        if new_experience_needed(
            existing_experience=overlay_experience, related_notices=overlay_notices
        ):
            overlay_experience = PrivacyExperience.create(
                db=db,
                data={
                    "region": region,
                    "component": ComponentType.overlay,
                },
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
        experience.unlink_experience_config(db)
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
    """
    linked_regions: List[PrivacyNoticeRegion] = []  # Regions that were linked
    current_regions: List[PrivacyNoticeRegion] = experience_config.regions
    removed_regions: List[PrivacyNoticeRegion] = [
        PrivacyNoticeRegion(reg)
        for reg in {reg.value for reg in current_regions}.difference(
            {reg.value for reg in regions}
        )
    ]
    unlinked_regions: List[
        PrivacyNoticeRegion
    ] = remove_config_from_matched_experiences(db, experience_config, removed_regions)

    for region in regions:
        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, region)

        existing_experience: Optional[PrivacyExperience] = (
            overlay_experience
            if experience_config.component == ComponentType.overlay
            else privacy_center_experience
        )

        data = {
            "component": experience_config.component,
            "region": region,
            "experience_config_id": experience_config.id,
            "experience_config_history_id": experience_config.experience_config_history_id,
            "disabled": experience_config.disabled,
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
