from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import ConfigDict, Field, HttpUrl, field_validator, model_validator

from fides.api.models.privacy_experience import BannerEnabled, ComponentType
from fides.api.models.privacy_notice import PrivacyNoticeRegion
from fides.api.schemas.base_class import FidesSchema
from fides.api.util.endpoint_utils import human_friendly_list


class ExperienceConfigSchema(FidesSchema):
    """
    Base for ExperienceConfig API objects.  Here all fields are optional since
    Pydantic allows subclasses to be more strict but not less strict

    Note component is intentionally not included in the base class. This can be specified when creating an ExperienceConfig
    but cannot be updated later.
    """

    accept_button_label: Optional[str] = Field(
        default=None,
        description="Overlay 'Accept button displayed on the Banner and Privacy Preferences' or Privacy Center 'Confirmation button label'",
    )
    acknowledge_button_label: Optional[str] = Field(
        default=None,
        description="Overlay 'Acknowledge button label for notice only banner'",
    )
    banner_enabled: Optional[BannerEnabled] = Field(
        default=None, description="Overlay 'Banner'"
    )
    description: Optional[str] = Field(
        default=None,
        description="Overlay 'Banner Description' or Privacy Center 'Description'",
    )
    disabled: Optional[bool] = Field(
        default=False, description="Whether the given ExperienceConfig is disabled"
    )
    is_default: Optional[bool] = Field(
        default=False,
        description="Whether the given ExperienceConfig is a global default",
    )
    privacy_policy_link_label: Optional[str] = Field(
        default=None,
        description="Overlay and Privacy Center 'Privacy policy link label'",
    )
    privacy_policy_url: Optional[HttpUrl] = Field(
        default=None, description="Overlay and Privacy Center 'Privacy policy URL"
    )
    privacy_preferences_link_label: Optional[str] = Field(
        default=None, description="Overlay 'Privacy preferences link label'"
    )
    regions: Optional[List[PrivacyNoticeRegion]] = Field(
        default=None, description="Regions using this ExperienceConfig"
    )
    reject_button_label: Optional[str] = Field(
        default=None,
        description="Overlay 'Reject button displayed on the Banner and 'Privacy Preferences' of Privacy Center 'Reject button label'",
    )
    save_button_label: Optional[str] = Field(
        default=None, description="Overlay 'Privacy preferences 'Save' button label"
    )
    title: Optional[str] = Field(
        default=None, description="Overlay 'Banner title' or Privacy Center 'title'"
    )

    @field_validator("regions")
    @classmethod
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

    @model_validator(mode="after")
    def validate_attributes(self) -> "ExperienceConfigCreate":
        """Validate minimum set of required fields exist given the type of component"""
        component: Optional[ComponentType] = self.component

        if component == ComponentType.overlay:
            # Overlays have a few additional required fields beyond the privacy center
            required_overlay_fields = [
                "acknowledge_button_label",
                "banner_enabled",
                "privacy_preferences_link_label",
            ]
            for field in required_overlay_fields:
                if not getattr(self, field):
                    raise ValueError(
                        f"The following additional fields are required when defining an overlay: {human_friendly_list(required_overlay_fields)}."
                    )

        return self


class ExperienceConfigUpdate(ExperienceConfigSchema):
    """
    Updating ExperienceConfig. Note that component cannot be updated once its created
    """

    model_config = ConfigDict(extra="forbid")


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
