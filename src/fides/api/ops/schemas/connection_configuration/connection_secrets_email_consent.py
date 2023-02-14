from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Extra, root_validator

from fides.api.ops.schemas.base_class import NoValidationSchema


class IdentityTypes(BaseModel):
    email: bool
    phone_number: bool


class AdvancedSettings(BaseModel):
    identity_types: IdentityTypes


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
        if not identities.email and not identities.phone_number:
            raise ValueError("Must supply at least one identity_type")
        return values


class ConsentEmailDocsSchema(ConsentEmailSchema, NoValidationSchema):
    """ConsentEmailDocsSchema Secrets Schema for API Docs"""


class ExtendedIdentityTypes(IdentityTypes):
    """Overrides basic IdentityTypes to add cookie_ids"""

    cookie_ids: List[str] = []


class AdvancedSettingsWithExtendedIdentityTypes(AdvancedSettings):
    """Overrides base AdvancedSettings to have extended IdentityTypes"""

    identity_types: ExtendedIdentityTypes


class ExtendedConsentEmailSchema(ConsentEmailSchema):
    """Email schema used to unpack secrets for all Consent Email Types (Both Generic, Sovrn, etc)"""

    advanced_settings: AdvancedSettingsWithExtendedIdentityTypes

    @root_validator
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """At least one identity or browser identity needs to be specified on setup"""
        advanced_settings = values.get("advanced_settings")
        if not advanced_settings:
            raise ValueError("Must supply advanced settings.")

        identities = advanced_settings.identity_types
        if (
            not identities.email
            and not identities.phone_number
            and not identities.cookie_ids
        ):
            raise ValueError("Must supply at least one identity_type")
        return values
