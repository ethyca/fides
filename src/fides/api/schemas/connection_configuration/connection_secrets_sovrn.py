from pydantic import EmailStr

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets_email import (
    AdvancedSettingsWithExtendedIdentityTypes,
    ExtendedEmailSchema,
    ExtendedIdentityTypes,
)

SOVRN_REQUIRED_IDENTITY: str = "ljt_readerID"


class SovrnSchema(ExtendedEmailSchema):
    """Schema to validate the secrets needed for the SovrnConnector

    Overrides the ExtendedEmailSchema to set the third_party_vendor_name
    and recipient_email_address.

    Also hardcodes the cookie_id for now.
    """

    third_party_vendor_name: str = "Sovrn"
    recipient_email_address: EmailStr = "privacy@sovrn.com"
    advanced_settings: AdvancedSettingsWithExtendedIdentityTypes = (
        AdvancedSettingsWithExtendedIdentityTypes(
            identity_types=ExtendedIdentityTypes(
                email=False, phone_number=False, cookie_ids=[SOVRN_REQUIRED_IDENTITY]
            )
        )
    )


class SovrnDocsSchema(SovrnSchema, NoValidationSchema):
    """SovrnDocsSchema Secrets Schema for API Docs"""
