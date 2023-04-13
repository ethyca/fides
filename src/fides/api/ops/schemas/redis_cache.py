from typing import Optional

from pydantic import EmailStr, Extra

from fides.api.custom_types import PhoneNumber
from fides.api.ops.schemas.base_class import BaseSchema


class Identity(BaseSchema):
    """Some PII grouping pertaining to a human"""

    phone_number: Optional[PhoneNumber] = None
    email: Optional[EmailStr] = None
    ga_client_id: Optional[str] = None
    ljt_readerID: Optional[str] = None

    class Config:
        """Only allow phone_number, email, and GA client id to be supplied"""

        extra = Extra.forbid
