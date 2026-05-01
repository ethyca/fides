import copy
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
from fides.api.schemas.custom_field_display_validator import (
    DisplayConditionValidator,
)
from fides.api.schemas.privacy_center_field_base import BaseCustomPrivacyRequestField

RequiredType = Literal["optional", "required"]

CustomFieldType = Literal[
    "text", "select", "multiselect", "checkbox", "checkbox_group", "textarea"
]


class PrivacyCenterLink(FidesSchema):
    label: str
    url: str

    @field_validator("url")
    @classmethod
    def validate_url_scheme(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("url must use the http or https scheme")
        return v


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


class CustomPrivacyRequestField(BaseCustomPrivacyRequestField):
    """Regular custom privacy request field supporting text, select, multiselect,
    checkbox, checkbox_group, and textarea types"""

    field_type: Optional[CustomFieldType] = None
    options: Optional[List[str]] = None

    @model_validator(mode="before")
    @classmethod
    def validate_field_type_constraints(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        field_type = values.get("field_type")
        if field_type == "checkbox_group" and not values.get("options"):
            raise ValueError("checkbox_group fields require at least one option")
        if field_type in ("checkbox", "textarea") and values.get("options"):
            raise ValueError(f"{field_type} fields do not support options")
        if field_type in ("multiselect", "checkbox_group") and values.get("hidden"):
            raise ValueError(
                f"{field_type} fields cannot be hidden: default_value does not "
                "support list values"
            )
        return values


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


DEFAULT_FILE_MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _default_allowed_mime_types() -> list[str]:
    # Import locally to avoid pulling storage/service modules at schema import time.
    from fides.api.service.storage.util import AllowedFileType, FilesMagicBytes

    return sorted(
        {
            AllowedFileType[ext].value
            for ext in FilesMagicBytes.default_public_upload_allowed_file_types()
        }
    )


class FileUploadCustomPrivacyRequestField(BaseCustomPrivacyRequestField):
    """File upload field. ``max_size_bytes`` + ``allowed_mime_types`` are
    client-side hints; upload endpoint enforces the global defaults."""

    field_type: Literal["file"] = "file"
    required: Optional[bool] = False
    max_size_bytes: int = Field(default=DEFAULT_FILE_MAX_SIZE_BYTES, gt=0)
    allowed_mime_types: list[str] = Field(default_factory=_default_allowed_mime_types)

    @model_validator(mode="before")
    @classmethod
    def validate_file_field(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("options"):
            raise ValueError("file fields do not support options")
        return values

    @field_validator("allowed_mime_types")
    @classmethod
    def validate_allowed_mime_types(cls, v: list[str]) -> list[str]:
        supported = set(_default_allowed_mime_types())
        if not v:
            raise ValueError("allowed_mime_types must not be empty")
        unsupported = [mime for mime in v if mime not in supported]
        if unsupported:
            raise ValueError(
                f"Unsupported MIME types: {sorted(unsupported)}. "
                f"Supported: {sorted(supported)}"
            )
        return v


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
    if field_type == "file":
        return "file"
    return "custom"


CustomPrivacyRequestFieldUnion = Annotated[
    Union[
        Annotated[LocationCustomPrivacyRequestField, Tag("location")],
        Annotated[FileUploadCustomPrivacyRequestField, Tag("file")],
        Annotated[CustomPrivacyRequestField, Tag("custom")],
    ],
    Discriminator(get_field_type_discriminator),
]


class _HasDisplayConditions:
    """Mixin giving any schema that carries ``custom_privacy_request_fields``
    a save-time validator over attached ``display_condition`` rules.
    """

    @model_validator(mode="after")
    def validate_display_conditions(self) -> "_HasDisplayConditions":
        fields = getattr(self, "custom_privacy_request_fields", None)
        if fields:
            DisplayConditionValidator(fields).validate()
        return self


class PrivacyRequestOption(_HasDisplayConditions, FidesSchema):
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


class ConsentConfigButton(_HasDisplayConditions, FidesSchema):
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
    page_title: Optional[str] = None
    actions: List[PrivacyRequestOption] = []
    include_consent: Optional[bool] = Field(alias="includeConsent", default=None)
    consent: ConsentConfig
    # Deprecated: prefer `links`. Kept for backwards compatibility.
    privacy_policy_url: Optional[str] = None
    # Deprecated: prefer `links`. Kept for backwards compatibility.
    privacy_policy_url_text: Optional[str] = None
    links: List[PrivacyCenterLink] = []
    policy_unavailable_messages: Optional[PolicyUnavailableMessages] = None

    @field_validator(
        "server_url_development",
        "server_url_production",
        "logo_url",
        "privacy_policy_url",
    )
    @classmethod
    def validate_url_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("URL must use the http or https scheme")
        return v


class PartialPrivacyRequestOption(_HasDisplayConditions, FidesSchema):
    policy_key: str
    title: str
    identity_inputs: Optional[IdentityInputs] = None
    custom_privacy_request_fields: Optional[
        Dict[str, CustomPrivacyRequestFieldUnion]
    ] = None


class PartialPrivacyCenterConfig(FidesSchema):
    """Partial schema for the Admin UI privacy request submission."""

    actions: List[PartialPrivacyRequestOption] = []


def reorder_custom_privacy_request_fields(config: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of the privacy center config with custom_privacy_request_fields
    ordered by custom_privacy_request_field_order when present.

    JSONB does not preserve object key order. This helper reconstructs the desired
    order using the stored order list and removes that internal key from the result.
    When no order list exists (legacy config), the existing key order is preserved.
    """
    result = copy.deepcopy(config)
    actions = result.get("actions")
    if not actions or not isinstance(actions, list):
        return result

    for action in actions:
        if not isinstance(action, dict):
            continue
        fields = action.get("custom_privacy_request_fields")
        if not fields or not isinstance(fields, dict):
            continue

        order = action.get("custom_privacy_request_field_order")
        if isinstance(order, list) and len(order) > 0:
            ordered = {k: fields[k] for k in order if k in fields}
            # Append any fields not in order (prevents data loss if order list becomes stale)
            for k in fields:
                if k not in ordered:
                    ordered[k] = fields[k]
            action["custom_privacy_request_fields"] = ordered
            action.pop("custom_privacy_request_field_order", None)
        # No order list: deep copy already preserved existing key order

    return result
