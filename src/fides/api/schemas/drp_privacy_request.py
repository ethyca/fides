from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, EmailStr, field_validator

from fides.api.custom_types import PhoneNumber
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.policy import DrpAction

DRP_VERSION = "0.5"


class DrpMeta(FidesSchema):
    """Enum to hold Drp metadata. Only version is supported at this time"""

    version: str


class DrpRegime(Enum):
    """Enum to hold Drp Regime. Only ccpa supported at this time"""

    ccpa = "ccpa"


class DrpPrivacyRequestCreate(FidesSchema):
    """Data required to create a DRP PrivacyRequest"""

    meta: DrpMeta
    regime: Optional[DrpRegime] = None
    exercise: List[DrpAction]
    relationships: Optional[List[str]] = None
    identity: str
    status_callback: Optional[str] = None
    model_config = ConfigDict(use_enum_values=True)

    @field_validator("exercise")
    @classmethod
    def check_exercise_length(cls, exercise: List[DrpAction]) -> List[DrpAction]:
        """Validate the only one exercise action is provided"""
        if len(exercise) > 1:
            raise ValueError("Multiple exercise actions are not supported at this time")
        return exercise


class DrpIdentity(FidesSchema):
    """Drp identity props"""

    aud: Optional[str] = None
    sub: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    email_verified: Optional[bool] = None
    phone_number: Optional[PhoneNumber] = None
    phone_number_verified: Optional[bool] = None
    address: Optional[str] = None
    address_verified: Optional[bool] = None
    owner_of_attorney: Optional[str] = None


class DrpDataRightsResponse(FidesSchema):
    """Drp data rights response"""

    version: str
    api_base: Optional[str] = None
    actions: List[DrpAction]
    user_relationships: Optional[List[str]] = None


class DrpRevokeRequest(FidesSchema):
    """DRP Data Rights Revoke Request Body"""

    request_id: str
    reason: Optional[str] = None
