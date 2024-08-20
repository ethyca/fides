from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from fides.api.schemas.redis_cache import Identity


class SecondPartyResponseFormat(BaseModel):
    """The expected response from a user's HTTP endpoint that receives callbacks from fides.api

    Responses are only expected (and considered) for two_way webhooks.
    """

    derived_identity: Optional[Identity] = None
    halt: bool
    model_config = ConfigDict(use_enum_values=True)


class PrivacyRequestResumeFormat(BaseModel):
    """Expected request body to resume a privacy request after it was paused by a webhook"""

    derived_identity: Optional[Identity] = {}  # type: ignore
    model_config = ConfigDict(use_enum_values=True)


class WebhookJWE(BaseModel):
    """Describes JWE that is given to the user that they need to send with their request
    to resume or pre-approve a privacy request"""

    webhook_id: str
    scopes: List[str]
    iat: str


class RequestTaskJWE(BaseModel):
    """Describes JWE that is given to the user that they need to send to the request
    task callback endpoint to re-queue that request task"""

    request_task_id: str
    scopes: List[str]
    iat: str
