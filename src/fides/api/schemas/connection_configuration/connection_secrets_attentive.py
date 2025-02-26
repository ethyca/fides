from pydantic import EmailStr

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets_email import (
    EmailSchema,
)


class AttentiveSchema(EmailSchema):
    third_party_vendor_name: str = "Attentive Email"
    recipient_email_address: EmailStr = "privacy@attentive.com"


class AttentiveDocsSchema(AttentiveSchema, NoValidationSchema):
    """AttentiveDocsSchema Secrets Schema for API Docs"""
