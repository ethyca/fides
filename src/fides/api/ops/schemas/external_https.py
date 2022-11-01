from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from fides.api.ops.models.policy import WebhookDirection
from fides.api.ops.schemas.redis_cache import Identity


class CallbackType(Enum):
    """We currently have two types of Policy Webhooks: pre and post"""

    pre = "pre"
    post = "post"


class SecondPartyRequestFormat(BaseModel):
    """The request body we will use when calling a user's HTTP endpoint from fides.api"""

    privacy_request_id: str
    direction: WebhookDirection
    callback_type: CallbackType
    identity: Identity

    class Config:
        """Using enum values"""

        use_enum_values = True


class SecondPartyResponseFormat(BaseModel):
    """The expected response from a user's HTTP endpoint that receives callbacks from fides.api

    Responses are only expected (and considered) for two_way webhooks.
    """

    derived_identity: Optional[Identity] = None
    halt: bool

    class Config:
        """Using enum values"""

        use_enum_values = True


class PrivacyRequestResumeFormat(BaseModel):
    """Expected request body to resume a privacy request after it was paused by a webhook"""

    derived_identity: Optional[Identity] = {}  # type: ignore

    class Config:
        """Using enum values"""

        use_enum_values = True


class WebhookJWE(BaseModel):
    """Describes JWE that is given to the user that they need to send with their request
    to resume a privacy request"""

    webhook_id: str
    scopes: List[str]
    iat: str
