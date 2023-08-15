from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Extra, Field, root_validator, validator

from fides.api.models.privacy_experience import BannerEnabled, ComponentType
from fides.api.models.privacy_notice import PrivacyNoticeRegion
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.privacy_notice import PrivacyNoticeResponseWithUserPreferences
from fides.api.util.endpoint_utils import human_friendly_list


class ExperienceConfigSchema(FidesSchema):
    """
    Base for ExperienceConfig API objects.  Here all fields are optional since
    Pydantic allows subclasses to be more strict but not less strict

    Note component is intentionally not included in the base class. This can be specified when creating an ExperienceConfig
    but cannot be updated later.
    """

    accept_button_label: Optional[str] = Field(
        description="Overlay 'Accept button displayed on the Banner and Privacy Preferences' or Privacy Center 'Confirmation button label'"
    )
    acknowledge_button_label: Optional[str] = Field(
        description="Overlay 'Acknowledge button label for notice only banner'"
    )
    banner_enabled: Optional[BannerEnabled] = Field(description="Overlay 'Banner'")
    description: Optional[str] = Field(
        description="Overlay 'Banner Description' or Privacy Center 'Description'"
    )
    disabled: Optional[bool] = Field(
        default=False, description="Whether the given ExperienceConfig is disabled"
    )
    is_default: Optional[bool] = Field(
        default=False,
        description="Whether the given ExperienceConfig is a global default",
    )
    privacy_policy_link_label: Optional[str] = Field(
        description="Overlay and Privacy Center 'Privacy policy link label'"
    )
    privacy_policy_url: Optional[str] = Field(
        description="Overlay and Privacy Center 'Privacy policy URl'"
    )
    privacy_preferences_link_label: Optional[str] = Field(
        description="Overlay 'Privacy preferences link label'"
    )
    regions: Optional[List[PrivacyNoticeRegion]] = Field(
        description="Regions using this ExperienceConfig"
    )
    reject_button_label: Optional[str] = Field(
        description="Overlay 'Reject button displayed on the Banner and 'Privacy Preferences' of Privacy Center 'Reject button label'"
    )
    save_button_label: Optional[str] = Field(
        description="Overlay 'Privacy preferences 'Save' button label"
    )
    title: Optional[str] = Field(
        description="Overlay 'Banner title' or Privacy Center 'title'"
    )

    @validator("regions")
    @classmethod
    def validate_regions(
        cls, regions: List[PrivacyNoticeRegion]
    ) -> List[PrivacyNoticeRegion]:
        """Assert regions aren't duplicated."""
        if regions and len(regions) != len(set(regions)):
            raise ValueError("Duplicate regions found.")
        return regions


class ExperienceConfigCreate(ExperienceConfigSchema):
    """
    An API representation to create ExperienceConfig.
    This model doesn't include an `id` so that it can be used for creation.
    It also establishes some fields _required_ for creation
    """

    accept_button_label: str
    component: ComponentType
    description: str
    reject_button_label: str
    save_button_label: str
    title: str

    @root_validator
    def validate_attributes(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate minimum set of required fields exist given the type of component"""
        component: Optional[ComponentType] = values.get("component")

        if component == ComponentType.overlay:
            # Overlays have a few additional required fields beyond the privacy center
            required_overlay_fields = [
                "acknowledge_button_label",
                "banner_enabled",
                "privacy_preferences_link_label",
            ]
            for field in required_overlay_fields:
                if not values.get(field):
                    raise ValueError(
                        f"The following additional fields are required when defining an overlay: {human_friendly_list(required_overlay_fields)}."
                    )

        return values


class ExperienceConfigUpdate(ExperienceConfigSchema):
    """
    Updating ExperienceConfig. Note that component cannot be updated once its created
    """

    class Config:
        """Forbid extra values - specifically we don't want component to be updated here."""

        extra = Extra.forbid


class ExperienceConfigCreateWithId(ExperienceConfigCreate):
    """Schema for creating out-of-the-box experience configs"""

    id: str


class ExperienceConfigSchemaWithId(ExperienceConfigSchema):
    """
    An API representation of a ExperienceConfig that includes an `id` field.

    Also includes the experience config history id and version
    """

    id: str
    component: ComponentType
    experience_config_history_id: str
    version: float


class ExperienceConfigResponse(ExperienceConfigSchemaWithId):
    """
    An API representation of ExperienceConfig used for response payloads
    """

    created_at: datetime
    updated_at: datetime
    regions: List[PrivacyNoticeRegion]  # Property


class ExperienceConfigCreateOrUpdateResponse(FidesSchema):
    """Schema with the created/updated experience config with regions that succeeded or failed"""

    experience_config: ExperienceConfigResponse
    linked_regions: List[PrivacyNoticeRegion]
    unlinked_regions: List[PrivacyNoticeRegion]


class PrivacyExperience(FidesSchema):
    """
    Base for PrivacyExperience API objects.  Here all fields are optional since
    Pydantic allows subclasses to be more strict but not less strict
    """

    region: PrivacyNoticeRegion
    component: Optional[ComponentType]
    experience_config: Optional[ExperienceConfigSchemaWithId]

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
    show_banner: Optional[bool]
    privacy_notices: Optional[List[PrivacyNoticeResponseWithUserPreferences]]
    experience_config: Optional[ExperienceConfigResponse]
