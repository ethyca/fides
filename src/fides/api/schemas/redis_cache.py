import uuid
from typing import Any, Dict, List, Optional, Union

from pydantic import EmailStr, Extra, Field, StrictInt, StrictStr, validator

from fides.api.custom_types import PhoneNumber
from fides.api.schemas.base_class import FidesSchema

MultiValue = Union[StrictInt, StrictStr, List[Union[StrictInt, StrictStr]]]


class IdentityBase(FidesSchema):
    """The minimum fields required to represent an identity."""

    phone_number: Optional[PhoneNumber] = None
    email: Optional[EmailStr] = None

    class Config:
        """Only allow phone_number, and email."""

        extra = Extra.forbid


class LabeledIdentity(FidesSchema):
    """
    An identity value with its accompanying UI label
    """

    label: str
    value: MultiValue


class Identity(IdentityBase):
    """Some PII grouping pertaining to a human"""

    # These are repeated so we can continue to forbid extra fields
    phone_number: Optional[PhoneNumber] = Field(None, title="Phone number")
    email: Optional[EmailStr] = Field(None, title="Email")
    ga_client_id: Optional[str] = Field(None, title="GA client ID")
    ljt_readerID: Optional[str] = Field(None, title="LJT reader ID")
    fides_user_device_id: Optional[str] = Field(None, title="Fides user device ID")
    external_id: Optional[str] = Field(None, title="External ID")

    class Config:
        """Allows extra fields to be provided but they must have a value of type LabeledIdentity."""

        extra = Extra.allow

    def __init__(self, **data: Any):
        for field, value in data.items():
            if field not in self.__fields__:
                if isinstance(value, LabeledIdentity):
                    data[field] = value
                elif isinstance(value, dict) and "label" in value and "value" in value:
                    data[field] = LabeledIdentity(**value)
                else:
                    raise ValueError(
                        f'Custom identity "{field}" must be an instance of LabeledIdentity '
                        '(e.g. {"label": "Field label", "value": "123"})'
                    )
        super().__init__(**data)

    @validator("fides_user_device_id")
    @classmethod
    def validate_fides_user_device_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate the uuid format of the fides user device id while still keeping the data type a string"""
        if not v:
            return v
        uuid.UUID(v, version=4)
        return v

    def dict(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Returns a dictionary with LabeledIdentity values returned as simple values.
        """
        d = super().dict(*args, **kwargs)
        for key, value in self.__dict__.items():
            if isinstance(value, LabeledIdentity):
                d[key] = value.value
            else:
                d[key] = value
        return d

    def labeled_dict(
        self, include_default_labels: Optional[bool] = False
    ) -> Dict[str, Any]:
        """Returns a dictionary that preserves the labels for all custom/labeled identities."""
        d = {}
        for key, value in self.__dict__.items():
            if key in self.__fields__:
                if include_default_labels:
                    d[key] = {
                        "label": self.__fields__[key].field_info.title,
                        "value": value,
                    }
                else:
                    d[key] = value
            else:
                if isinstance(value, LabeledIdentity):
                    d[key] = value.dict()
                else:
                    d[key] = value
        return d


class CustomPrivacyRequestField(FidesSchema):
    """Schema for custom privacy request fields."""

    label: str
    # use StrictInt and StrictStr to avoid type coercion and maintain the original types
    value: MultiValue
