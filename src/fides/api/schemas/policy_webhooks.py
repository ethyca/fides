from typing import List, Optional

from fideslang.validation import FidesKey

from fides.api.models.policy import WebhookDirection
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.connection_configuration.connection_config import (
    ConnectionConfigurationResponse,
)


class WebhookBase(FidesSchema):
    """Base schema for Webhooks"""

    direction: WebhookDirection
    key: Optional[FidesKey]
    name: Optional[str]


class PolicyWebhookCreate(WebhookBase):
    """Request schema for creating/updating a Policy Webhook"""

    connection_config_key: FidesKey

    class Config:
        """Populate models with the raw value of enum fields, rather than the enum itself"""

        use_enum_values = True


class PolicyWebhookResponse(WebhookBase):
    """Response schema after creating a PolicyWebhook"""

    connection_config: Optional[ConnectionConfigurationResponse]
    order: int

    class Config:
        """Set orm_mode to True"""

        orm_mode = True


class PolicyWebhookUpdate(FidesSchema):
    """Request schema for updating a single webhook - fields are optional"""

    direction: Optional[WebhookDirection]
    name: Optional[str]
    connection_config_key: Optional[FidesKey]
    order: Optional[int]

    class Config:
        """Only the included attributes will be used"""

        orm_mode = True
        extra = "forbid"
        use_enum_values = True


class WebhookOrder(FidesSchema):
    """Schema for displaying a minimal amount of information about the webhook and its order"""

    key: FidesKey
    order: int

    class Config:
        """Set orm_mode to True"""

        orm_mode = True


class PolicyWebhookUpdateResponse(FidesSchema):
    """Response schema after a PATCH to a single webhook - because updating the order of this webhook can update the
    order of other webhooks, new_order will include the new order if order was adjusted at all
    """

    resource: PolicyWebhookResponse
    new_order: List[WebhookOrder]


class PolicyWebhookDeleteResponse(FidesSchema):
    """Response schema after deleting a webhook; new_order includes remaining reordered webhooks if applicable"""

    new_order: List[WebhookOrder]

    class Config:
        """Set orm_mode to True"""

        orm_mode = True
