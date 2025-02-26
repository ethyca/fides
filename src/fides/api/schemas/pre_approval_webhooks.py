from typing import Optional

from fideslang.validation import FidesKey
from pydantic import ConfigDict

from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.connection_configuration.connection_config import (
    ConnectionConfigurationResponse,
)


class WebhookBase(FidesSchema):
    """Base schema for Webhooks"""

    key: Optional[FidesKey] = None
    name: str


class PreApprovalWebhookCreate(WebhookBase):
    """Request schema for creating/updating a Pre Approval Webhook"""

    connection_config_key: FidesKey
    model_config = ConfigDict(use_enum_values=True)


class PreApprovalWebhookResponse(WebhookBase):
    """Response schema after creating/updating/getting a PreApprovalWebhook"""

    connection_config: Optional[ConnectionConfigurationResponse] = None
    model_config = ConfigDict(from_attributes=True)


class PreApprovalWebhookUpdate(FidesSchema):
    """Request schema for updating a single webhook - fields are optional"""

    name: Optional[str] = None
    connection_config_key: Optional[FidesKey] = None
    model_config = ConfigDict(
        from_attributes=True, extra="forbid", use_enum_values=True
    )
