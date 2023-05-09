from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Extra, root_validator, validator

from fides.api.custom_types import SafeStr
from fides.api.ops.models.privacy_experience import ComponentType, DeliveryMechanism
from fides.api.ops.models.privacy_notice import PrivacyNoticeRegion
from fides.api.ops.schemas.base_class import FidesSchema
from fides.api.ops.schemas.privacy_notice import PrivacyNoticeResponse


class ExperienceLanguage(FidesSchema):
    """
    Base for ExperienceLanguage API objects.  Here all fields are optional since
    Pydantic allows subclasses to be more strict but not less strict
    """

    acknowledgement_button_label: Optional[SafeStr]
    banner_title: Optional[SafeStr]
    banner_description: Optional[SafeStr]
    component: Optional[ComponentType]
    component_title: Optional[SafeStr]
    component_description: Optional[SafeStr]
    confirmation_button_label: Optional[SafeStr]
    delivery_mechanism: Optional[DeliveryMechanism]
    disabled: Optional[bool] = False
    is_default: Optional[bool] = False
    link_label: Optional[SafeStr]
    reject_button_label: Optional[SafeStr]


class ExperienceLanguageCreate(ExperienceLanguage):
    """
    An API representation to create ExperienceLanguage.
    This model doesn't include an `id` so that it can be used for creation.
    It also establishes some fields _required_ for creation
    """

    component: ComponentType
    delivery_mechanism: DeliveryMechanism
    regions: List[PrivacyNoticeRegion]
    component_title: SafeStr

    @validator("regions")
    @classmethod
    def validate_regions(
        cls, regions: List[PrivacyNoticeRegion]
    ) -> List[PrivacyNoticeRegion]:
        """Assert regions aren't duplicated."""
        if len(regions) != len(set(regions)):
            raise ValueError("Duplicate regions found.")
        return regions

    @root_validator
    def validate_attributes(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate minimum set of required fields exist given the type of component and/or delivery_mechanism"""
        component: Optional[ComponentType] = values.get("component")
        delivery_mechanism: Optional[DeliveryMechanism] = values.get(
            "delivery_mechanism"
        )

        if delivery_mechanism == DeliveryMechanism.link and not values.get(
            "link_label"
        ):
            raise ValueError(
                "Link label required when the delivery mechanism is of type link."
            )

        if component == ComponentType.overlay:
            if delivery_mechanism == DeliveryMechanism.banner:
                required_banner_fields = [
                    "banner_title",
                    "confirmation_button_label",
                    "reject_button_label",
                ]
                for field in required_banner_fields:
                    if not values.get(field):
                        raise ValueError(
                            f"The following fields are required when defining a banner: {required_banner_fields}."
                        )

        if component == ComponentType.privacy_center:
            if delivery_mechanism != DeliveryMechanism.link:
                raise ValueError(
                    "Privacy center experiences can only be delivered via a link."
                )

        return values


class ExperienceLanguageUpdate(ExperienceLanguage):
    """
    Updating ExperienceLanguage - requires regions to be patched specifically
    """

    regions: List[PrivacyNoticeRegion]

    @validator("regions")
    @classmethod
    def validate_regions(
        cls, regions: List[PrivacyNoticeRegion]
    ) -> List[PrivacyNoticeRegion]:
        """Assert regions aren't duplicated."""
        if len(regions) != len(set(regions)):
            raise ValueError("Duplicate regions found.")
        return regions


class ExperienceLanguageWithId(ExperienceLanguage):
    """
    An API representation of a ExperienceLanguage that includes an `id` field.

    Also includes the experience language history id and version
    """

    id: str
    experience_language_history_id: str
    version: float


class ExperienceLanguageResponse(ExperienceLanguageWithId):
    """
    An API representation of ExperienceLanguage used for response payloads
    """

    created_at: datetime
    updated_at: datetime
    regions: List[PrivacyNoticeRegion]  # Property


class ExperienceLanguageCreateOrUpdateResponse(FidesSchema):
    """Schema with the created/updated experience language with regions that succeeded or failed"""

    experience_language: ExperienceLanguageResponse
    added_regions: List[PrivacyNoticeRegion]
    removed_regions: List[PrivacyNoticeRegion]
    skipped_regions: List[PrivacyNoticeRegion]


class PrivacyExperience(FidesSchema):
    """
    Base for PrivacyExperience API objects.  Here all fields are optional since
    Pydantic allows subclasses to be more strict but not less strict
    """

    disabled: Optional[bool] = False
    component: Optional[ComponentType]
    delivery_mechanism: Optional[DeliveryMechanism]
    region: PrivacyNoticeRegion
    experience_language: Optional[ExperienceLanguageWithId]

    class Config:
        """Populate models with the raw value of enum fields, rather than the enum itself"""

        use_enum_values = True
        orm_mode = True
        extra = Extra.forbid


class PrivacyExperienceWithId(PrivacyExperience):
    """
    An API representation of a PrivacyExperience that includes an `id` field.
    Used to help model API responses and update payloads
    """

    id: str


class PrivacyExperienceResponse(PrivacyExperienceWithId):
    """
    An API representation of a PrivacyExperience used for response payloads
    """

    created_at: datetime
    updated_at: datetime
    version: float
    privacy_experience_history_id: str
    privacy_notices: Optional[List[PrivacyNoticeResponse]]
