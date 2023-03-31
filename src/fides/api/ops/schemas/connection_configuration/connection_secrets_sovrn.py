from typing import Any, Dict

from pydantic import EmailStr, root_validator

from fides.api.ops.schemas.connection_configuration.connection_secrets_email import (
    AdvancedSettingsWithExtendedIdentityTypes,
    ExtendedEmailSchema,
    ExtendedIdentityTypes,
)
from fides.lib.schemas.base_class import NoValidationSchema

SOVRN_REQUIRED_IDENTITY: str = "ljt_readerID"


class SovrnSchema(ExtendedEmailSchema):
    """Schema to validate the secrets needed for the SovrnConnector

    Overrides the ExtendedEmailSchema to set the third_party_vendor_name
    and recipient_email_address.

    Also hardcodes the cookie_id for now.
    """

    third_party_vendor_name: str = "Sovrn"
    recipient_email_address: EmailStr = EmailStr("privacy@sovrn.com")

    @root_validator
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        For now, UI is disabled, so user cannot update advanced settings.
        Hardcode the Sovrn advanced settings, regardless of what is passed into the API.
        """
        values["advanced_settings"] = AdvancedSettingsWithExtendedIdentityTypes(
            identity_types=ExtendedIdentityTypes(
                email=False, phone_number=False, cookie_ids=[SOVRN_REQUIRED_IDENTITY]
            )
        )
        return values


class SovrnDocsSchema(SovrnSchema, NoValidationSchema):
    """SovrnDocsSchema Secrets Schema for API Docs"""
