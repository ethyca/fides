from typing import Dict, List, Optional

from fides.api.schemas.base_class import FidesSchema


class IdentityInputs(FidesSchema):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class CustomPrivacyRequestField(FidesSchema):
    label: str
    required: Optional[bool] = False
    default_value: Optional[str] = None
    hidden: Optional[bool] = False


class PrivacyRequestOption(FidesSchema):
    policy_key: str
    title: str
    identity_inputs: Optional[IdentityInputs] = None
    custom_privacy_request_fields: Optional[Dict[str, CustomPrivacyRequestField]] = None

    class Config:
        extra = "allow"


class PrivacyCenterConfig(FidesSchema):
    actions: List[PrivacyRequestOption]

    class Config:
        extra = "allow"


class SupportedPrivacyRequestOption(PrivacyRequestOption):

    class Config:
        extra = "ignore"


class SupportedPrivacyCenterConfig(PrivacyCenterConfig):
    actions: List[SupportedPrivacyRequestOption]

    class Config:
        extra = "ignore"
