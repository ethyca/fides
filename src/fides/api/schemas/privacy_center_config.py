from abc import ABC
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import (
    ConfigDict,
    Discriminator,
    Field,
    Tag,
    field_validator,
    model_validator,
)

from fides.api.models.location_regulation_selections import PrivacyNoticeRegion
from fides.api.schemas.base_class import FidesSchema

RequiredType = Literal["optional", "required"]


class CustomIdentity(FidesSchema):
    label: str


class IdentityInputs(FidesSchema):
    name: Optional[RequiredType] = None
    email: Optional[RequiredType] = None
    phone: Optional[RequiredType] = None
    model_config = ConfigDict(extra="allow")

    def __init__(self, **data: Any):
        for field, value in data.items():
            if field not in self.model_fields:
                if isinstance(value, CustomIdentity):
                    data[field] = value
                elif isinstance(value, dict) and "label" in value:
                    data[field] = CustomIdentity(**value)
                else:
                    raise ValueError(
                        f'Custom identity "{field}" must be an instance of CustomIdentity '
                        '(e.g. {"label": "Field label"})'
                    )
        super().__init__(**data)


class BaseCustomPrivacyRequestField(FidesSchema, ABC):
    """Abstract base class for all custom privacy request fields"""

    label: str
    required: Optional[bool] = True
    default_value: Optional[str] = None
    hidden: Optional[bool] = False
    query_param_key: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_default_value(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if (
            values.get("hidden")
            and values.get("default_value") is None
            and values.get("query_param_key") is None
        ):
            raise ValueError(
                "default_value or query_param_key are required when hidden is True"
            )
        return values


class CustomPrivacyRequestField(BaseCustomPrivacyRequestField):
    """Regular custom privacy request field supporting text, select, and multiselect types"""

    field_type: Optional[Literal["text", "select", "multiselect"]] = None
    options: Optional[List[str]] = None


class LocationCustomPrivacyRequestField(BaseCustomPrivacyRequestField):
    """Location field that doesn't support options and includes IP geolocation hint"""

    field_type: Literal["location"] = "location"
    ip_geolocation_hint: Optional[bool] = False

    @model_validator(mode="before")
    @classmethod
    def validate_location_field(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure options is not provided for location fields
        if "options" in values:
            raise ValueError(
                "LocationCustomPrivacyRequestField does not support options"
            )

        # This field cannot be hidden
        if values.get("hidden"):
            raise ValueError("Custom location fields cannot be hidden")

        return values


# Create a discriminated union type using the field_type to properly distinguish between types
def get_field_type_discriminator(v: Any) -> str:
    """Discriminator function for CustomPrivacyRequestFieldUnion"""
    if isinstance(v, dict):
        field_type = v.get("field_type")
    else:
        # For model instances, get field_type attribute
        field_type = getattr(v, "field_type", None)

    if field_type == "location":
        return "location"
    return "custom"


CustomPrivacyRequestFieldUnion = Annotated[
    Union[
        Annotated[LocationCustomPrivacyRequestField, Tag("location")],
        Annotated[CustomPrivacyRequestField, Tag("custom")],
    ],
    Discriminator(get_field_type_discriminator),
]


class PrivacyRequestOption(FidesSchema):
    locations: Optional[Union[List[PrivacyNoticeRegion], Literal["fallback"]]] = None
    policy_key: Optional[str] = None
    icon_path: str
    title: str
    description: str
    description_subtext: Optional[List[str]] = None
    confirm_button_text: Optional[str] = Field(alias="confirmButtonText", default=None)
    cancel_button_text: Optional[str] = Field(alias="cancelButtonText", default=None)
    identity_inputs: Optional[IdentityInputs] = None
    custom_privacy_request_fields: Optional[
        Dict[str, CustomPrivacyRequestFieldUnion]
    ] = None


class ConsentConfigButton(FidesSchema):
    description: str
    description_subtext: Optional[List[str]] = None
    confirm_button_text: Optional[str] = Field(alias="confirmButtonText", default=None)
    cancel_button_text: Optional[str] = Field(alias="cancelButtonText", default=None)
    icon_path: str
    identity_inputs: IdentityInputs
    custom_privacy_request_fields: Optional[
        Dict[str, CustomPrivacyRequestFieldUnion]
    ] = None
    title: str
    modal_title: Optional[str] = Field(alias="modalTitle", default=None)


class ConditionalValue(FidesSchema):
    value: bool
    global_privacy_control: bool = Field(alias="globalPrivacyControl")


class ConfigConsentOption(FidesSchema):
    cookie_keys: List[str] = Field([], alias="cookieKeys")
    default: Optional[Union[bool, ConditionalValue]] = None
    description: str
    fides_data_use_key: str = Field(alias="fidesDataUseKey")
    highlight: Optional[bool] = None
    name: str
    url: str
    executable: Optional[bool] = None


class ConsentConfigPage(FidesSchema):
    consent_options: List[ConfigConsentOption] = Field([], alias="consentOptions")
    description: str
    description_subtext: Optional[List[str]] = None
    policy_key: Optional[str] = None
    title: str

    @field_validator("consent_options")
    @classmethod
    def validate_consent_options(
        cls, consent_options: List[ConfigConsentOption]
    ) -> List[ConfigConsentOption]:
        executable_count = sum(option.executable is True for option in consent_options)
        if executable_count > 1:
            raise ValueError("Cannot have more than one consent option be executable.")
        return consent_options


class ConsentConfig(FidesSchema):
    button: ConsentConfigButton
    page: ConsentConfigPage


class PolicyUnavailableMessages(FidesSchema):
    """
    Used to capture the information to present to a user if a policy is unavailable.
    """

    title: str
    description: str
    close_button_text: str
    action_button_text: str
    action_link: str


class PrivacyCenterConfig(FidesSchema):
    """
    NOTE: Add to this schema with care. Any fields added to
    this response schema will be exposed in public-facing
    (i.e. unauthenticated) API responses. If a field has
    sensitive information, it should NOT be added to this schema!
    """

    title: str
    description: str
    description_subtext: Optional[List[str]] = None
    addendum: Optional[List[str]] = None
    server_url_development: Optional[str] = None
    server_url_production: Optional[str] = None
    logo_path: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_path: Optional[str] = None
    actions: List[PrivacyRequestOption]
    include_consent: Optional[bool] = Field(alias="includeConsent", default=None)
    consent: ConsentConfig
    privacy_policy_url: Optional[str] = None
    privacy_policy_url_text: Optional[str] = None
    policy_unavailable_messages: Optional[PolicyUnavailableMessages] = None


class PartialPrivacyRequestOption(FidesSchema):
    policy_key: str
    title: str
    identity_inputs: Optional[IdentityInputs] = None
    custom_privacy_request_fields: Optional[
        Dict[str, CustomPrivacyRequestFieldUnion]
    ] = None


class PartialPrivacyCenterConfig(FidesSchema):
    """Partial schema for the Admin UI privacy request submission."""

    actions: List[PartialPrivacyRequestOption]
