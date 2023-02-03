from typing import Any, Dict

from pydantic import root_validator

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets_email_consent import (
    AdvancedSettings,
    ConsentEmailSchema,
    CookieIds,
)


class SovrnEmailSchema(ConsentEmailSchema):
    """Schema to validate the secrets needed for the SovrnEmailConnector"""

    # Overrides ConsentEmailSchema.third_party_vendor_name and recipient_email_address to set defaults
    third_party_vendor_name: str = "Sovrn"
    recipient_email_address: str

    @root_validator
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        For now, UI is disabled, so user cannot update advanced settings.
        Hardcode the Sovrn advanced settings.
        """
        values["advanced_settings"] = AdvancedSettings(
            identity_types=[], browser_identity_types=[CookieIds.ljt_readerID]
        )

        return values


class ConsentEmailDocsSchema(SovrnEmailSchema, NoValidationSchema):
    """SovrnDocsSchema Secrets Schema for API Docs"""
