from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional, Tuple, Type

from sqlalchemy import Boolean, Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import Float, ForeignKey, String, UniqueConstraint, and_, or_
from sqlalchemy.orm import Query, Session, relationship
from sqlalchemy.util import hybridproperty

from fides.api.ops.db.base_class import Base
from fides.api.ops.models.privacy_notice import PrivacyNotice, PrivacyNoticeRegion


class ComponentType(Enum):
    """
    The component type - not formalized in the db
    """

    overlay = "overlay"
    privacy_center = "privacy_center"


class DeliveryMechanism(Enum):
    """
    The delivery mechanism - not formalized in the db
    """

    banner = "banner"
    link = "link"


class ExperienceLanguageBase:
    """Base schema to share common experience language."""

    acknowledgement_button_label = Column(String)
    banner_title = Column(String)
    banner_description = Column(String)
    component = Column(EnumColumn(ComponentType), nullable=False, index=True)
    component_title = Column(String)
    component_description = Column(String)
    confirmation_button_label = Column(String)
    delivery_mechanism = Column(
        EnumColumn(DeliveryMechanism), nullable=False, index=True
    )
    disabled = Column(Boolean, nullable=False, default=False)
    is_default = Column(Boolean, nullable=False, default=False)
    link_label = Column(String)
    reject_button_label = Column(String)
    version = Column(Float, nullable=False, default=1.0)


class ExperienceLanguage(ExperienceLanguageBase, Base):
    """Stores common experience language to be shared across multiple regions"""

    experiences = relationship(
        "PrivacyExperience",
        back_populates="experience_language",
        lazy="dynamic",
    )

    histories = relationship(
        "ExperienceLanguageHistory",
        backref="experience_language",
        lazy="dynamic",
    )

    @property
    def regions(self) -> List[PrivacyNoticeRegion]:
        """Return the regions attached to the various experiences using this ExperienceLanguage"""
        return [exp.region for exp in self.experiences]  # type: ignore[attr-defined]

    @classmethod
    def create(
        cls: Type[ExperienceLanguage],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> ExperienceLanguage:
        """Create experience language and then clone this record into the history table for record keeping"""
        experience_language: ExperienceLanguage = super().create(
            db=db, data=data, check_name=check_name
        )

        # create the history after the initial object creation succeeds, to avoid
        # writing history if the creation fails and so that we can get the generated ID
        history_data = {
            **data,
            "experience_language_id": experience_language.id,
        }
        ExperienceLanguageHistory.create(db, data=history_data, check_name=False)
        return experience_language

    def update(self, db: Session, *, data: dict[str, Any]) -> ExperienceLanguage:
        """
        Overrides the base update method to automatically bump the version of the
        ExperienceLanguage record and also create a new ExperienceLanguageHistory entry
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
            history_data["experience_language_id"] = self.id

            ExperienceLanguageHistory.create(db, data=history_data, check_name=False)

        return self

    def dry_update(self, *, data: dict[str, Any]) -> ExperienceLanguage:
        """
        A utility method to get an updated object without saving it to the db.

        This is used to see what an object update would look like, in memory,
        without actually persisting the update to the db
        """
        cloned_attributes = self.__dict__.copy()
        for key, val in data.items():
            cloned_attributes[key] = val
        cloned_attributes.pop("_sa_instance_state")
        return ExperienceLanguage(**cloned_attributes)

    @hybridproperty
    def experience_language_history_id(self) -> Optional[str]:
        """Convenience property that returns the experience language id for the current version.

        Note that there are possibly many historical records for the given experience language, this just returns the current
        corresponding historical record.
        """
        history: ExperienceLanguageHistory = self.histories.filter_by(  # type: ignore # pylint: disable=no-member
            version=self.version
        ).first()
        return history.id if history else None


class ExperienceLanguageHistory(ExperienceLanguageBase, Base):
    """Experience Language History - stores the history of how the language changed"""

    experience_language_id = Column(
        String, ForeignKey(ExperienceLanguage.id_field_path), nullable=False
    )


class PrivacyExperienceBase:
    """Base Privacy Experience fields that are common between privacy experiences experiences and historical records"""

    disabled = Column(Boolean, nullable=False, default=False)
    component = Column(EnumColumn(ComponentType), nullable=False)
    delivery_mechanism = Column(EnumColumn(DeliveryMechanism), nullable=False)
    region = Column(EnumColumn(PrivacyNoticeRegion), nullable=False, index=True)
    version = Column(Float, nullable=False, default=1.0)


class PrivacyExperience(PrivacyExperienceBase, Base):
    """Stores Privacy Experiences for a given region."""

    experience_language_id = Column(
        String,
        ForeignKey(ExperienceLanguage.id_field_path),
        nullable=True,
        index=True,
    )

    experience_language_history_id = Column(
        String,
        ForeignKey(ExperienceLanguageHistory.id_field_path),
        nullable=True,
        index=True,
    )  # Also links to the historical record, so if the version of the language gets updated, that
    # triggers a new version of the experience.

    UniqueConstraint("region", "component", name="region_component")

    histories = relationship(
        "PrivacyExperienceHistory", backref="privacy_experience", lazy="dynamic"
    )

    experience_language = relationship(
        "ExperienceLanguage",
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
    ) -> List[PrivacyNotice]:
        """Return privacy notices that overlap on at least one region
        and match on ComponentType

        If show_disabled=False, only return enabled notices.
        """
        privacy_notice_query = get_privacy_notices_by_region_and_component(
            db, self.region, self.component  # type: ignore[arg-type]
        )

        if show_disabled is False:
            privacy_notice_query = privacy_notice_query.filter(
                PrivacyNotice.disabled.is_(False)
            )

        return privacy_notice_query.order_by(PrivacyNotice.created_at.desc()).all()

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

        # Cache privacy notices for display
        self.privacy_notices = self.get_related_privacy_notices(db)
        return self

    @staticmethod
    def get_experience_by_component_and_region(
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
        overlay_experience: Optional[PrivacyExperience] = (
            db.query(PrivacyExperience)
            .filter(
                PrivacyExperience.region == region,
                PrivacyExperience.component == ComponentType.overlay,
            )
            .first()
        )

        privacy_center_experience: Optional[PrivacyExperience] = (
            db.query(PrivacyExperience)
            .filter(
                PrivacyExperience.region == region,
                PrivacyExperience.component == ComponentType.privacy_center,
            )
            .first()
        )

        return overlay_experience, privacy_center_experience

    def unlink_privacy_experience_language(self, db: Session) -> PrivacyExperience:
        """Remove language from experience"""
        return self.update(
            db,
            data={
                "experience_language_id": None,
                "experience_language_history_id": None,
            },
        )


class PrivacyExperienceHistory(PrivacyExperienceBase, Base):
    """Stores the history of a privacy experience for a given region for Consent Reporting"""

    version = Column(Float, nullable=False, default=1.0)
    privacy_experience_id = Column(
        String, ForeignKey(PrivacyExperience.id_field_path), nullable=False, index=True
    )
    experience_language_id = Column(
        String,
        ForeignKey(ExperienceLanguage.id_field_path),
        nullable=True,
        index=True,
    )

    experience_language_history_id = Column(
        String,
        ForeignKey(ExperienceLanguageHistory.id_field_path),
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
