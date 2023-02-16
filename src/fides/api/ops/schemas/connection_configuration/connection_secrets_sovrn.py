from typing import Any, Dict

from pydantic import root_validator

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets_email_consent import (
    AdvancedSettingsWithExtendedIdentityTypes,
    ExtendedConsentEmailSchema,
    ExtendedIdentityTypes,
)

SOVRN_REQUIRED_IDENTITY: str = "ljt_readerID"


class SovrnEmailSchema(ExtendedConsentEmailSchema):
    """Schema to validate the secrets needed for the SovrnEmailConnector

    Overrides the ExtendedConsentEmailSchema to set the third_party_vendor_name
    and recipient_email_address.

    Also hardcodes the cookie_id for now.
    """

    third_party_vendor_name: str = "Sovrn"
    recipient_email_address: str  # In production, use: privacy@sovrn.com

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


class SovrnEmailDocsSchema(SovrnEmailSchema, NoValidationSchema):
    """SovrnDocsSchema Secrets Schema for API Docs"""
