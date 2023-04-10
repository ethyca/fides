from typing import Any, Dict

from pydantic import EmailStr, root_validator

from fides.api.ops.schemas.connection_configuration.connection_secrets_email import (
    AdvancedSettings,
    EmailSchema,
    IdentityTypes,
)
from fides.lib.schemas.base_class import NoValidationSchema


class AttentiveSchema(EmailSchema):
    third_party_vendor_name: str = "Attentive"
    recipient_email_address: EmailStr = EmailStr("privacy@attentive.com")

    @root_validator
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        For now, UI is disabled, so user cannot update advanced settings.
        Hardcode the Attentive advanced settings, regardless of what is passed into the API.
        """
        values["advanced_settings"] = AdvancedSettings(
            identity_types=IdentityTypes(email=True, phone_number=False)
        )
        return values


class AttentiveDocsSchema(AttentiveSchema, NoValidationSchema):
    """AttentiveDocsSchema Secrets Schema for API Docs"""
