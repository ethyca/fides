from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Extra, Field, HttpUrl, root_validator, validator

from fides.api.custom_types import HtmlStr
from fides.api.models.privacy_experience import ComponentType
from fides.api.models.privacy_notice import PrivacyNoticeRegion
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.language import SupportedLanguage
from fides.api.schemas.privacy_notice import PrivacyNoticeResponse


class ExperienceTranslation(FidesSchema):
    """
    Schema for Experience Translations
    """

    language: SupportedLanguage

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


class ExperienceTranslationCreate(ExperienceTranslation):
    """Overrides ExperienceTranslation fields to make some fields required on create"""

    title: str  # Required for all UX types
    description: HtmlStr  # Required for all UX types

    class Config:
        """For when we're creating templates - so the Experience Translation Language can be serialized into JSON"""

        use_enum_values = True


class ExperienceTranslationResponse(ExperienceTranslation):
    """Adds the historical id to the translation for the response"""

    experience_config_history_id: str


class ExperienceConfigSchema(FidesSchema):
    """
    Base for ExperienceConfig API objects.  Here all fields are optional since
    Pydantic allows subclasses to be more strict but not less strict

    Note component is intentionally not included in the base class. This can be specified when creating an ExperienceConfig
    but cannot be updated later.
    """

    name: Optional[str]
    disabled: Optional[bool]
    origin: Optional[str]
    dismissable: Optional[bool]
    allow_language_selection: Optional[bool]
    regions: List[PrivacyNoticeRegion] = []

    @validator("regions")
    @classmethod
    def validate_regions(
        cls, regions: List[PrivacyNoticeRegion]
    ) -> List[PrivacyNoticeRegion]:
        """Assert regions aren't duplicated."""
        if regions and len(regions) != len(set(regions)):
            raise ValueError("Duplicate regions found.")
        return regions


class ExperienceConfigCreateBase(ExperienceConfigSchema):
    """
    An API representation to create ExperienceConfig.
    This model doesn't include an `id` so that it can be used for creation.
    It also establishes some fields _required_ for creation
    """

    translations: List[ExperienceTranslationCreate] = []
    component: ComponentType
    disabled: Optional[bool] = True

    @root_validator()
    def validate_translations(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        - Ensure no two translations with the same language are supplied and that
        at least one is the default
        - Only allow language selection if there are > 1 translations
        """
        translations: List[ExperienceTranslation] = values.get("translations") or []
        allow_language_selection: bool = values.get("allow_language_selection") or False

        if len(translations) < 2 and allow_language_selection:
            raise ValueError(
                "More than one translation must be supplied to allow language selection"
            )

        if not translations:
            return values

        default_translations = 0

        languages: List[SupportedLanguage] = []
        for translation in translations:
            languages.append(translation.language)
            if translation.is_default:
                default_translations += 1

        if len(languages) != len(set(languages)):
            raise ValueError("Multiple translations supplied for the same language")

        if default_translations != 1:
            raise ValueError(
                "One and only one translation must be specified as the default"
            )

        return values


class ExperienceConfigCreateTemplate(ExperienceConfigCreateBase):
    id: str
    privacy_notice_keys: List[str]

    @validator("privacy_notice_keys")
    def check_duplicate_notice_keys(cls, privacy_notice_keys: List[str]) -> List[str]:
        if len(privacy_notice_keys) != len(set(privacy_notice_keys)):
            raise ValueError("Duplicate privacy notice keys detected")
        return privacy_notice_keys


class ExperienceConfigCreate(ExperienceConfigCreateBase):
    privacy_notice_ids: List[str] = []

    @validator("privacy_notice_ids")
    def check_duplicate_notice_ids(cls, privacy_notice_ids: List[str]) -> List[str]:
        return check_dupe_notice_ids(privacy_notice_ids)


class ExperienceConfigUpdate(ExperienceConfigSchema):
    """
    Updating ExperienceConfig. Note that component cannot be updated once its created
    """

    translations: List[ExperienceTranslation]
    regions: List[PrivacyNoticeRegion]
    privacy_notice_ids: List[str]

    @validator("privacy_notice_ids")
    def check_duplicate_notice_ids(cls, privacy_notice_ids: List[str]) -> List[str]:
        return check_dupe_notice_ids(privacy_notice_ids)

    class Config:
        """Forbid extra values - specifically we don't want component to be updated here."""

        extra = Extra.forbid


class ExperienceConfigSchemaWithId(ExperienceConfigSchema):
    """
    An API representation of a ExperienceConfig that includes an `id` field.
    """

    id: str


class ExperienceConfigResponse(ExperienceConfigSchemaWithId):
    """
    An API representation of ExperienceConfig used for response payloads
    """

    created_at: datetime
    updated_at: datetime
    component: ComponentType
    regions: List[PrivacyNoticeRegion]  # Property
    privacy_notices: List[PrivacyNoticeResponse] = []
    translations: List[ExperienceTranslationResponse] = []


class ExperienceConfigCreateOrUpdateResponse(FidesSchema):
    """Schema with the created/updated experience config with regions that succeeded or failed"""

    experience_config: ExperienceConfigResponse
    linked_regions: List[PrivacyNoticeRegion]
    unlinked_regions: List[PrivacyNoticeRegion]


def check_dupe_notice_ids(privacy_notice_ids: List[str]) -> List[str]:
    "Verify if there are duplicates in notice ids"
    if len(privacy_notice_ids) != len(set(privacy_notice_ids)):
        raise ValueError("Duplicate privacy notice ids detected")
    return privacy_notice_ids
