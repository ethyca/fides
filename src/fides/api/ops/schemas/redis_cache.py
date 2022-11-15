from re import compile as regex
from typing import Optional

from pydantic import Extra, validator

from fides.api.ops.schemas.base_class import BaseSchema


class Identity(BaseSchema):
    """Some PII grouping pertaining to a human"""

    phone_number: Optional[str] = None
    email: Optional[str] = None

    @validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        if value:
            pattern = regex(r"^\+[1-9]\d{1,14}$")
            if not pattern.search(value):
                raise ValueError(
                    "Identity phone number must be formatted in E.164 format. E.g +15558675309"
                )
        return value

    class Config:
        """Only allow phone_number and email to be supplied"""

        extra = Extra.forbid
