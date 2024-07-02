from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import Extra, Field, root_validator, validator

from fides.api.schemas.base_class import FidesSchema

RequiredType = Literal["optional", "required"]


class CustomIdentity(FidesSchema):
    label: str


class IdentityInputs(FidesSchema):
    name: Optional[RequiredType] = None
    email: Optional[RequiredType] = None
    phone: Optional[RequiredType] = None

    class Config:
        """Allows extra fields to be provided but they must have a value of type CustomIdentity."""

        extra = Extra.allow

    def __init__(self, **data: Any):
        for field, value in data.items():
            if field not in self.__fields__:
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

    @root_validator
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
    description_subtext: Optional[List[str]]
    confirm_button_text: Optional[str] = Field(alias="confirmButtonText")
    cancel_button_text: Optional[str] = Field(alias="cancelButtonText")
    identity_inputs: Optional[IdentityInputs] = None
    custom_privacy_request_fields: Optional[Dict[str, CustomPrivacyRequestField]] = None


class ConsentConfigButton(FidesSchema):
    description: str
    description_subtext: Optional[List[str]]
    confirm_button_text: Optional[str] = Field(alias="confirmButtonText")
    cancel_button_text: Optional[str] = Field(alias="cancelButtonText")
    icon_path: str
    identity_inputs: IdentityInputs
    custom_privacy_request_fields: Optional[Dict[str, CustomPrivacyRequestField]] = None
    title: str
    modal_title: Optional[str] = Field(alias="modalTitle")


class ConditionalValue(FidesSchema):
    value: bool
    global_privacy_control: bool = Field(alias="globalPrivacyControl")


class ConfigConsentOption(FidesSchema):
    cookie_keys: List[str] = Field([], alias="cookieKeys")
    default: Optional[Union[bool, ConditionalValue]]
    description: str
    fides_data_use_key: str = Field(alias="fidesDataUseKey")
    highlight: Optional[bool]
    name: str
    url: str
    executable: Optional[bool]


class ConsentConfigPage(FidesSchema):
    consent_options: List[ConfigConsentOption] = Field([], alias="consentOptions")
    description: str
    description_subtext: Optional[List[str]]
    policy_key: Optional[str]
    title: str

    @validator("consent_options")
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
    description_subtext: Optional[List[str]]
    addendum: Optional[List[str]]
    server_url_development: Optional[str]
    server_url_production: Optional[str]
    logo_path: Optional[str]
    logo_url: Optional[str]
    favicon_path: Optional[str]
    actions: List[PrivacyRequestOption]
    include_consent: Optional[bool] = Field(alias="includeConsent")
    consent: ConsentConfig
    privacy_policy_url: Optional[str]
    privacy_policy_url_text: Optional[str]


class PartialPrivacyRequestOption(FidesSchema):
    policy_key: str
    title: str
    identity_inputs: Optional[IdentityInputs] = None
    custom_privacy_request_fields: Optional[Dict[str, CustomPrivacyRequestField]] = None


class PartialPrivacyCenterConfig(FidesSchema):
    """Partial schema for the Admin UI privacy request submission."""

    actions: List[PartialPrivacyRequestOption]
