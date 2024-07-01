from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import ConfigDict, Field, field_validator, model_validator

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


class CustomPrivacyRequestField(FidesSchema):
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


class PrivacyRequestOption(FidesSchema):
    policy_key: str
    icon_path: str
    title: str
    description: str
    description_subtext: Optional[List[str]] = None
    confirm_button_text: Optional[str] = Field(alias="confirmButtonText", default=None)
    cancel_button_text: Optional[str] = Field(alias="cancelButtonText", default=None)
    identity_inputs: Optional[IdentityInputs] = None
    custom_privacy_request_fields: Optional[Dict[str, CustomPrivacyRequestField]] = None


class ConsentConfigButton(FidesSchema):
    description: str
    description_subtext: Optional[List[str]] = None
    confirm_button_text: Optional[str] = Field(alias="confirmButtonText", default=None)
    cancel_button_text: Optional[str] = Field(alias="cancelButtonText", default=None)
    icon_path: str
    identity_inputs: IdentityInputs
    custom_privacy_request_fields: Optional[Dict[str, CustomPrivacyRequestField]] = None
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


class PartialPrivacyRequestOption(FidesSchema):
    policy_key: str
    title: str
    identity_inputs: Optional[IdentityInputs] = None
    custom_privacy_request_fields: Optional[Dict[str, CustomPrivacyRequestField]] = None


class PartialPrivacyCenterConfig(FidesSchema):
    """Partial schema for the Admin UI privacy request submission."""

    actions: List[PartialPrivacyRequestOption]
