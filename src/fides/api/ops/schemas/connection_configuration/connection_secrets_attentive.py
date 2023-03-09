from fides.api.ops.schemas.connection_configuration.connection_secrets_email import (
    EmailSchema,
)


class AttentiveSchema(EmailSchema):
    third_party_vendor_name = "Attentive"
    recipient_email_address = "privacy@attentive.com"
