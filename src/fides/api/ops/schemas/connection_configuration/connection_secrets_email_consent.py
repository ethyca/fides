from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Extra, root_validator

from fides.api.ops.schemas.base_class import NoValidationSchema

SVORN_REQUIRED_IDENTITY: str = "ljt_readerID"


class CookieIds(str, Enum):
    ljt_readerID = SVORN_REQUIRED_IDENTITY


class IdentityTypes(str, Enum):
    email = "email"
    phone_number = "phone_number"


class AdvancedSettings(BaseModel):
    identity_types: List[IdentityTypes] = []
    browser_identity_types: List[CookieIds] = []


class ConsentEmailSchema(BaseModel):
    """Schema to validate the secrets needed for the generic ConsentEmailConnector

    Does not inherit from ConnectionConfigSecretsSchema as there is no url
    required here.
    """

    third_party_vendor_name: str
    recipient_email_address: str
    test_email_address: Optional[str]
    advanced_settings: AdvancedSettings

    class Config:
        """Only permit selected secret fields to be stored."""

        extra = Extra.forbid
        orm_mode = True

    @root_validator
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """At least one identity or browser identity needs to be specified on setup"""
        advanced_settings = values.get("advanced_settings")
        if not advanced_settings:
            raise ValueError("Must supply advanced settings.")
        identities = advanced_settings.identity_types
        cookies = advanced_settings.browser_identity_types
        if not identities and not cookies:
            raise ValueError(
                "Must supply at least one identity_type or one browser_identity_type"
            )
        return values


class ConsentEmailDocsSchema(ConsentEmailSchema, NoValidationSchema):
    """ConsentEmailDocsSchema Secrets Schema for API Docs"""
