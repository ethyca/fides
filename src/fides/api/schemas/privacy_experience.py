from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Extra, Field, HttpUrl, root_validator, validator

from fides.api.custom_types import HtmlStr
from fides.api.models.privacy_experience import BannerEnabled, ComponentType
from fides.api.models.privacy_notice import Language, PrivacyNoticeRegion
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.privacy_notice import PrivacyNoticeResponse
from fides.api.util.endpoint_utils import human_friendly_list


class ExperienceTranslation(FidesSchema):
    language: Language

    accept_button_label: Optional[str] = Field(
        description="Overlay 'Accept button displayed on the Banner and Privacy Preferences' or Privacy Center 'Confirmation button label'"
    )
    acknowledge_button_label: Optional[str] = Field(
        description="Overlay 'Acknowledge button label for notice only banner'"
    )
    banner_description: Optional[HtmlStr] = Field(
        description="Overlay 'Banner Description'"
    )
    banner_title: Optional[str] = Field(description="Overlay 'Banner title'")
    description: Optional[HtmlStr] = Field(
        description="Overlay 'Description' or Privacy Center 'Description'"
    )
    is_default: Optional[bool] = Field(
        default=False,
        description="Whether the given translation is the default",
    )
    privacy_policy_link_label: Optional[str] = Field(
        description="Overlay and Privacy Center 'Privacy policy link label'"
    )
    privacy_policy_url: Optional[HttpUrl] = Field(
        default=None, description="Overlay and Privacy Center 'Privacy policy URL"
    )
    privacy_preferences_link_label: Optional[str] = Field(
        description="Overlay 'Privacy preferences link label'"
    )
    reject_button_label: Optional[str] = Field(
        description="Overlay 'Reject button displayed on the Banner and 'Privacy Preferences' of Privacy Center 'Reject button label'"
    )
    save_button_label: Optional[str] = Field(
        description="Overlay 'Privacy preferences 'Save' button label"
    )
    title: Optional[str] = Field(
        description="Overlay 'title' or Privacy Center 'title'"
    )

    class Config:
        use_enum_values = True


class ExperienceTranslationResponse(ExperienceTranslation):
    experience_config_history_id: str


class ExperienceConfigSchema(FidesSchema):
    """
    Base for ExperienceConfig API objects.  Here all fields are optional since
    Pydantic allows subclasses to be more strict but not less strict

    Note component is intentionally not included in the base class. This can be specified when creating an ExperienceConfig
    but cannot be updated later.
    """

    component: ComponentType
    banner_enabled: Optional[BannerEnabled] = Field(description="Overlay 'Banner'")
    origin: Optional[str]
    dismissable: Optional[bool]
    allow_language_selection: Optional[bool]
    translations: List[ExperienceTranslation] = []

    @root_validator()
    def validate_translations(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure no two translations with the same language are supplied
        """
        translations: List[Dict] = values.get("translations")
        if not translations:
            return values

        languages = [translation.language for translation in translations]
        if len(languages) != len(set(languages)):
            raise ValueError("Multiple translations supplied for the same language")

        return values


class ExperienceConfigCreate(ExperienceConfigSchema):
    """
    An API representation to create ExperienceConfig.
    This model doesn't include an `id` so that it can be used for creation.
    It also establishes some fields _required_ for creation
    """

    regions: List[PrivacyNoticeRegion] = []
    component: ComponentType
    privacy_notices: List[str] = []

    @validator("regions")
    @classmethod
    def validate_regions(
        cls, regions: List[PrivacyNoticeRegion]
    ) -> List[PrivacyNoticeRegion]:
        """Assert regions aren't duplicated."""
        if regions and len(regions) != len(set(regions)):
            raise ValueError("Duplicate regions found.")
        return regions

    @root_validator
    def validate_attributes(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate minimum set of required fields exist given the type of component"""
        component: Optional[ComponentType] = values.get("component")

        translations = values.get("translations")

        if not translations:
            return values

        if component == ComponentType.overlay:
            # Overlays have a few additional required fields beyond the privacy center
            required_overlay_fields = [
                "acknowledge_button_label",
                # "banner_enabled",  # TODO are we removing this?
                "privacy_preferences_link_label",
            ]
            for translation in translations:
                for field in required_overlay_fields:
                    if not getattr(translation, field, None):
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
    version: float


class ExperienceConfigResponse(ExperienceConfigSchemaWithId):
    """
    An API representation of ExperienceConfig used for response payloads
    """

    created_at: datetime
    updated_at: datetime
    regions: List[PrivacyNoticeRegion]  # Property
    privacy_notices: List[PrivacyNoticeResponse] = []
    translations: List[ExperienceTranslationResponse]


class ExperienceConfigCreateOrUpdateResponse(FidesSchema):
    """Schema with the created/updated experience config with regions that succeeded or failed"""

    experience_config: ExperienceConfigResponse
    linked_regions: List[PrivacyNoticeRegion]
    unlinked_regions: List[PrivacyNoticeRegion]
