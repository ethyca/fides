from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional, Type

from sqlalchemy import Boolean, Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import Float, ForeignKey, String, and_, or_
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Session, relationship
from sqlalchemy.util import hybridproperty

from fides.api.ops.models.privacy_notice import PrivacyNotice, PrivacyNoticeRegion
from fides.lib.db.base_class import Base


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


class PrivacyExperienceBase:
    """Base Privacy Experience fields that are common between templates, experiences, and historical records"""

    disabled = Column(Boolean, nullable=False, default=False)
    component = Column(EnumColumn(ComponentType), nullable=False)
    delivery_mechanism = Column(EnumColumn(DeliveryMechanism), nullable=False)
    regions = Column(
        ARRAY(EnumColumn(PrivacyNoticeRegion, native_enum=False)),
        index=True,
        nullable=False,
    )
    component_title = Column(String)
    component_description = Column(String)
    banner_title = Column(String)
    banner_description = Column(String)
    link_label = Column(String)
    confirmation_button_label = Column(String)
    reject_button_label = Column(String)
    acknowledgement_button_label = Column(String)


class PrivacyExperienceTemplate(PrivacyExperienceBase, Base):
    """Stores the out of the box Privacy Experiences"""


class PrivacyExperience(PrivacyExperienceBase, Base):
    """Stores saved Privacy Experiences to surface for users"""

    version = Column(Float, nullable=False, default=1.0)
    privacy_experience_template_id = Column(
        String, ForeignKey(PrivacyExperienceTemplate.id_field_path), nullable=True
    )

    # Attribute that can be added as the result of "get_related_privacy_notices". Privacy notices aren't directly
    # related to experiences.
    privacy_notices: List[PrivacyNotice] = []

    def get_related_privacy_notices(
        self,
        db: Session,
        region: Optional[PrivacyNoticeRegion] = None,
        show_disabled: Optional[bool] = True,
    ) -> List[PrivacyNotice]:
        """Return privacy notices that overlap on at least one region
        and match on ComponentType

        If region parameter, further restrict on notices matching a specific region. Same
        thing goes for show_disabled filter.
        """
        privacy_notice_query = db.query(PrivacyNotice)

        if show_disabled is False:
            privacy_notice_query = privacy_notice_query.filter(
                PrivacyNotice.disabled.is_(False)
            )

        if region is not None:
            privacy_notice_query = privacy_notice_query.filter(
                PrivacyNotice.regions.contains([region])
            )

        return (
            privacy_notice_query.filter(PrivacyNotice.regions.overlap(self.regions))  # type: ignore
            .filter(
                or_(
                    and_(
                        self.component == ComponentType.overlay,
                        PrivacyNotice.displayed_in_overlay,
                    ),
                    and_(
                        self.component == ComponentType.privacy_center,
                        PrivacyNotice.displayed_in_privacy_center,
                    ),
                )
            )
            .order_by(PrivacyNotice.created_at.desc())
            .all()
        )

    histories = relationship(
        "PrivacyExperienceHistory", backref="privacy_experience", lazy="dynamic"
    )

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
        history_data = {**data, "privacy_experience_id": privacy_experience.id}
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


class PrivacyExperienceHistory(PrivacyExperienceBase, Base):
    """Stores historical records of Privacy Experiences for Consent Reporting"""

    version = Column(Float, nullable=False, default=1.0)
    privacy_experience_template_id = Column(
        String, ForeignKey(PrivacyExperienceTemplate.id_field_path), nullable=True
    )
    privacy_experience_id = Column(
        String, ForeignKey(PrivacyExperience.id_field_path), nullable=False
    )
