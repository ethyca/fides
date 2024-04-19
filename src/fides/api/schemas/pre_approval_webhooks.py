from typing import Optional

from fideslang.validation import FidesKey

from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.connection_configuration.connection_config import (
    ConnectionConfigurationResponse,
)


class WebhookBase(FidesSchema):
    """Base schema for Webhooks"""

    key: Optional[FidesKey]
    name: str


class PreApprovalWebhookCreate(WebhookBase):
    """Request schema for creating/updating a Pre Approval Webhook"""

    connection_config_key: FidesKey

    class Config:
        """Populate models with the raw value of enum fields, rather than the enum itself"""

        use_enum_values = True


class PreApprovalWebhookResponse(WebhookBase):
    """Response schema after creating/updating/getting a PreApprovalWebhook"""

    connection_config: Optional[ConnectionConfigurationResponse]

    class Config:
        """Set orm_mode to True"""

        orm_mode = True


class PreApprovalWebhookUpdate(FidesSchema):
    """Request schema for updating a single webhook - fields are optional"""

    name: Optional[str]
    connection_config_key: Optional[FidesKey]

    class Config:
        """Only the included attributes will be used"""

        orm_mode = True
        extra = "forbid"
        use_enum_values = True
