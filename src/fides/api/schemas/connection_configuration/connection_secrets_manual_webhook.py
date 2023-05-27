from fides.api.schemas.base_class import FidesSchema, NoValidationSchema


class ManualWebhookSchema(FidesSchema):
    """Secrets for manual webhooks. No secrets needed at this time."""


class ManualWebhookSchemaforDocs(ManualWebhookSchema, NoValidationSchema):
    """Manual Webhooks Secrets Schema for API Docs"""
