import abc
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Extra, root_validator

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class EmailSchema(BaseModel, abc.ABC):
    """Abstract base schema for updating email configuration secrets"""

    third_party_vendor_name: str
    recipient_email_address: str
    test_email_address: Optional[str]  # Email to send a connection test email

    _required_components: List[str] = [
        "third_party_vendor_name",
        "recipient_email_address",
    ]

    def __init_subclass__(cls: BaseModel, **kwargs: Any):  # type: ignore
        super().__init_subclass__(**kwargs)  # type: ignore
        if not getattr(cls, "_required_components"):
            raise TypeError(f"Class {cls.__name__} must define '_required_components.'")  # type: ignore

    @root_validator
    @classmethod
    def required_components_supplied(  # type: ignore
        cls: ConnectionConfigSecretsSchema, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that the minimum required components have been supplied."""
        min_fields_present = all(
            values.get(component) for component in cls._required_components
        )
        if not min_fields_present:
            raise ValueError(
                f"{cls.__name__} must be supplied all of: {cls._required_components}."  # type: ignore
            )

        return values

    class Config:
        """Only permit selected secret fields to be stored."""

        extra = Extra.ignore
        orm_mode = True


class EmailDocsSchema(EmailSchema, NoValidationSchema):
    """EmailDocsSchema Secrets Schema for API Docs"""
