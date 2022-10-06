from fides.api.ops.schemas.base_class import BaseSchema, NoValidationSchema


class ManualWebhookSchema(BaseSchema):
    """Secrets for manual webhooks. No secrets needed at this time."""


class ManualWebhookSchemaforDocs(ManualWebhookSchema, NoValidationSchema):
    """Manual Webhooks Secrets Schema for API Docs"""
