from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Extra, root_validator

from fides.api.schemas.base_class import NoValidationSchema


class IdentityTypes(BaseModel):
    email: bool
    phone_number: bool


class AdvancedSettings(BaseModel):
    identity_types: IdentityTypes


class EmailSchema(BaseModel):
    """Schema to validate the secrets needed for a generic email connector"""

    third_party_vendor_name: str
    recipient_email_address: EmailStr
    test_email_address: Optional[EmailStr]  # Email to send a connection test email

    # the default value is temporary until we allow users to customize the identity types from the front-end
    advanced_settings: AdvancedSettings = AdvancedSettings(
        identity_types=IdentityTypes(email=True, phone_number=False)
    )

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
            raise ValueError("Must supply at least one identity_type.")
        return values


class EmailDocsSchema(EmailSchema, NoValidationSchema):
    """EmailDocsSchema Secrets Schema for API Docs"""


class ExtendedIdentityTypes(IdentityTypes):
    """Overrides basic IdentityTypes to add cookie_ids"""

    cookie_ids: List[str] = []


class AdvancedSettingsWithExtendedIdentityTypes(AdvancedSettings):
    """Overrides base AdvancedSettings to have extended IdentityTypes"""

    identity_types: ExtendedIdentityTypes


class ExtendedEmailSchema(EmailSchema):
    """Email schema used to unpack secrets for all email connector types (both generic, Sovrn, etc.)"""

    # the default value is temporary until we allow users to customize the identity types from the front-end
    advanced_settings: AdvancedSettingsWithExtendedIdentityTypes = (
        AdvancedSettingsWithExtendedIdentityTypes(
            identity_types=ExtendedIdentityTypes(
                email=True, phone_number=False, cookie_ids=[]
            )
        )
    )

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
            raise ValueError("Must supply at least one identity_type.")
        return values
