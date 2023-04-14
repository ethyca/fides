from typing import Optional

from pydantic import EmailStr, Extra

from fides.api.custom_types import PhoneNumber
from fides.api.ops.schemas.base_class import BaseSchema


class IdentityBase(BaseSchema):
    """The minimum fields required to represent an identity."""

    phone_number: Optional[PhoneNumber] = None
    email: Optional[EmailStr] = None

    class Config:
        """Only allow phone_number, and email."""

        extra = Extra.forbid


class Identity(IdentityBase):
    """Some PII grouping pertaining to a human"""

    ga_client_id: Optional[str] = None
    ljt_readerID: Optional[str] = None
