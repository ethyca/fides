from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from fidesops.models.policy import WebhookDirection
from fidesops.schemas.redis_cache import PrivacyRequestIdentity


class CallbackType(Enum):
    """We currently have two types of Policy Webhooks: pre and post"""

    pre = "pre"
    post = "post"


class SecondPartyRequestFormat(BaseModel):
    """The request body we will use when calling a user's HTTP endpoint from Fidesops"""

    privacy_request_id: str
    direction: WebhookDirection
    callback_type: CallbackType
    identity: PrivacyRequestIdentity

    class Config:
        """Using enum values"""

        use_enum_values = True


class SecondPartyResponseFormat(BaseModel):
    """The expected response from a user's HTTP endpoint that receives callbacks from Fidesops

    Responses are only expected (and considered) for two_way webhooks.
    """

    derived_identity: Optional[PrivacyRequestIdentity] = None
    halt: bool

    class Config:
        """Using enum values"""

        use_enum_values = True


class PrivacyRequestResumeFormat(BaseModel):
    """Expected request body to resume a privacy request after it was paused by a webhook"""

    derived_identity: Optional[PrivacyRequestIdentity] = {}

    class Config:
        """Using enum values"""

        use_enum_values = True


class WebhookJWE(BaseModel):
    """Describes JWE that is given to the user that they need to send with their request
    to resume a privacy request"""

    webhook_id: str
    scopes: List[str]
    iat: str
