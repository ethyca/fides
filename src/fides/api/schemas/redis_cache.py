import uuid
from typing import Optional

from pydantic import EmailStr, Extra, validator

from fides.api.custom_types import PhoneNumber
from fides.api.schemas.base_class import FidesSchema


class IdentityBase(FidesSchema):
    """The minimum fields required to represent an identity."""

    phone_number: Optional[PhoneNumber] = None
    email: Optional[EmailStr] = None

    class Config:
        """Only allow phone_number, and email."""

        extra = Extra.forbid


class Identity(IdentityBase):
    """Some PII grouping pertaining to a human"""

    # These are repeated so we can continue to forbid extra fields
    phone_number: Optional[PhoneNumber] = None
    email: Optional[EmailStr] = None
    ga_client_id: Optional[str] = None
    ljt_readerID: Optional[str] = None
    fides_user_device_id: Optional[str] = None

    class Config:
        """Only allow phone_number, and email."""

        extra = Extra.forbid

    @validator("fides_user_device_id")
    @classmethod
    def validate_fides_user_device_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate the uuid format of the fides user device id"""
        if not v:
            return v
        uuid.UUID(v, version=4)
        return v
