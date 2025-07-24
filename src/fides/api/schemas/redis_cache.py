import uuid
from typing import Any, ClassVar, Dict, List, Optional, Union

from fideslang.validation import FidesKey
from pydantic import (
    ConfigDict,
    EmailStr,
    Field,
    StrictInt,
    StrictStr,
    ValidationError,
    field_validator,
    model_validator,
)

from fides.api.common_exceptions import BadRequest
from fides.api.custom_types import PhoneNumber
from fides.api.schemas.base_class import FidesSchema

MultiValue = Union[StrictInt, StrictStr, List[Union[StrictInt, StrictStr]]]


class IdentityBase(FidesSchema):
    """The minimum fields required to represent an identity."""

    phone_number: Optional[PhoneNumber] = None
    email: Optional[EmailStr] = None
    model_config = ConfigDict(extra="forbid")


class LabeledIdentity(FidesSchema):
    """
    An identity value with its accompanying UI label
    """

    label: str
    value: MultiValue


class Identity(IdentityBase):
    """Some PII grouping pertaining to a human"""

    # These are repeated so we can continue to forbid extra fields
    phone_number: Optional[PhoneNumber] = Field(default=None, title="Phone number")
    email: Optional[EmailStr] = Field(default=None, title="Email")
    ga_client_id: Optional[str] = Field(default=None, title="GA client ID")
    ljt_readerID: Optional[str] = Field(default=None, title="LJT reader ID")
    fides_user_device_id: Optional[str] = Field(
        default=None, title="Fides user device ID"
    )
    external_id: Optional[str] = Field(default=None, title="External ID")

    model_config = ConfigDict(extra="allow")

    def __init__(self, **data: Any):
        for field, value in data.items():
            if field not in self.model_fields:
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

    @field_validator("fides_user_device_id")
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
        for key, value in d.items():
            if key in self.model_fields:
                d[key] = value
            else:
                # Turn LabeledIdentity into simple values
                # 'customer_id': {'label': 'Customer ID', 'value': '123'} -> 'customer_id': '123'
                d[key] = value.get("value")
        return d

    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Returns a dictionary with LabeledIdentity values returned as simple values.
        In pydantic v2, model_dump is preferred over dict
        """
        d = super().model_dump(*args, **kwargs)
        for key, value in d.items():
            if key in self.model_fields:
                d[key] = value
            else:
                # Turn LabeledIdentity into simple values
                # 'customer_id': {'label': 'Customer ID', 'value': '123'} -> 'customer_id': '123'
                d[key] = value.get("value")
        return d

    def labeled_dict(
        self, include_default_labels: Optional[bool] = False
    ) -> Dict[str, Any]:
        """Returns a dictionary that preserves the labels for all custom/labeled identities."""
        d = super().model_dump()
        for field, _ in self.model_fields.items():
            value = getattr(self, field, None)
            if include_default_labels:
                d[field] = {
                    "label": self.model_fields[field].title,
                    "value": value,
                }
            else:
                d[field] = value
        for field in self.__pydantic_extra__ or {}:  # pylint:disable=not-an-iterable
            value = getattr(self, field, None)
            if isinstance(value, LabeledIdentity):
                d[field] = value.model_dump(mode="json")
            else:
                d[field] = value
        return d


class UnverifiedIdentity(Identity):
    """Exclude email and phone number from the identity"""

    email: ClassVar[Optional[EmailStr]] = Field(exclude=True)  # type: ignore[misc]
    phone_number: ClassVar[Optional[PhoneNumber]] = Field(exclude=True)  # type: ignore[misc]

    def __init__(self, **data: Any):
        for field, _ in data.items():
            if field in self.__class_vars__:
                raise ValueError(f'Identity "{field}" not allowed')
        super().__init__(**data)


class UnlabeledIdentities(FidesSchema):
    """
    A model for validating identity dictionaries where standard fields use Identity's validation
    but custom fields just need to be valued.
    """

    data: Dict[str, Any]

    @model_validator(mode="before")
    @classmethod
    def validate_identities(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(values, dict):
            raise BadRequest("Inputs must be JSON formatted")

        if not values:
            raise BadRequest("No inputs provided")

        standard_fields = {}
        custom_fields = {}

        # Separate standard and custom fields
        for field, value in values.items():
            if field in Identity.model_fields:
                if value is None:
                    raise BadRequest(f'Input "{field}" cannot be empty')
                standard_fields[field] = value
            else:
                if value is None:
                    raise BadRequest(f'Input "{field}" cannot be empty')
                custom_fields[field] = value

        # Validate standard fields using Identity
        try:
            Identity(**standard_fields)
        except ValidationError as e:
            error_detail = e.errors()[0]
            field = error_detail.get("loc")[0]  # type: ignore[assignment, index]
            clean_message = error_detail.get("msg")
            raise BadRequest(f'"{field}" {clean_message}')

        # Return the combined validated data
        return {"data": {**standard_fields, **custom_fields}}


class DatasetTestRequest(FidesSchema):
    """The policy key and inputs required to run a dataset test."""

    policy_key: FidesKey
    identities: UnlabeledIdentities


class CustomPrivacyRequestField(FidesSchema):
    """Schema for custom privacy request fields."""

    label: str
    # use StrictInt and StrictStr to avoid type coercion and maintain the original types
    value: MultiValue
