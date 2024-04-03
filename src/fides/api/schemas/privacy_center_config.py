from typing import Any, Dict, List, Literal, Optional

from pydantic import root_validator

from fides.api.schemas.base_class import FidesSchema

RequiredType = Literal["optional", "required"]


class IdentityInputs(FidesSchema):
    name: Optional[RequiredType] = None
    email: Optional[RequiredType] = None
    phone: Optional[RequiredType] = None


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
    title: str
    identity_inputs: Optional[IdentityInputs] = None
    custom_privacy_request_fields: Optional[Dict[str, CustomPrivacyRequestField]] = None

    class Config:
        extra = "ignore"


class PrivacyCenterConfig(FidesSchema):
    actions: List[PrivacyRequestOption]

    class Config:
        extra = "ignore"
