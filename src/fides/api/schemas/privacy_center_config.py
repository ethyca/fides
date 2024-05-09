from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import Extra, root_validator

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

    @root_validator
    def validate_default_value(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("hidden") and values.get("default_value") is None:
            raise ValueError("default_value is required when hidden is True")
        return values


class PrivacyRequestOption(FidesSchema):
    policy_key: str
    icon_path: str
    title: str
    description: str
    description_subtext: Optional[List[str]]
    confirmButtonText: Optional[str]
    cancelButtonText: Optional[str]
    identity_inputs: Optional[IdentityInputs] = None
    custom_privacy_request_fields: Optional[Dict[str, CustomPrivacyRequestField]] = None


class ConsentConfigButton(FidesSchema):
    description: str
    description_subtext: Optional[List[str]]
    confirmButtonText: Optional[str]
    cancelButtonText: Optional[str]
    icon_path: str
    identity_inputs: IdentityInputs
    custom_privacy_request_fields: Optional[Dict[str, CustomPrivacyRequestField]] = None
    title: str
    modalTitle: Optional[str]


class ConditionalValue(FidesSchema):
    value: bool
    globalPrivacyControl: bool


class ConfigConsentOption(FidesSchema):
    cookieKeys: List[str] = []
    default: Optional[Union[bool, ConditionalValue]]
    description: str
    fidesDataUseKey: str
    highlight: Optional[bool]
    name: str
    url: str
    executable: Optional[bool]


class ConsentConfigPage(FidesSchema):
    consentOptions: List[ConfigConsentOption]
    description: str
    description_subtext: Optional[List[str]]
    policy_key: Optional[str]
    title: str


class ConsentConfig(FidesSchema):
    button: ConsentConfigButton
    page: ConsentConfigPage


class PrivacyCenterConfig(FidesSchema):
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
    includeConsent: Optional[bool]
    consent: ConsentConfig
    privacy_policy_url: Optional[str]
    privacy_policy_url_text: Optional[str]
