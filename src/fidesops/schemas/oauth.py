from typing import Dict, Optional

from fastapi import Form, HTTPException
from fastapi.openapi.models import OAuthFlows
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED


class AccessToken(BaseModel):
    """A wrapper for the access_code returned upon successful authentication"""

    access_token: str


# NOTE: Adapted from https://github.com/tiangolo/fastapi/blob/master/fastapi/security/oauth2.py#L140
class OAuth2ClientCredentialsBearer(OAuth2):
    """
    Requires a valid OAuth2 bearer token using the client credentials flow, e.g.
    "Authorization: Bearer <token>". See /oauth/token for details on how to
    authenticate and receive a valid token.
    """

    # pylint: disable=R0913
    # NOTE: Disable this lint rule, as this argument list needs to be consistent with FastAPI
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlows(clientCredentials={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )

    # pylint: enable=R0913

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        return param


# NOTE: Adapted from https://github.com/tiangolo/fastapi/blob/master/fastapi/security/oauth2.py#L13
# NOTE: This uses application/x-www-form-urlencoded (form encoding) instead of JSON to follow the
# OAuth2 spec: https://datatracker.ietf.org/doc/html/rfc6749#section-4.4.2
class OAuth2ClientCredentialsRequestForm:
    """
    Request model used to authenticate via OAuth2 client credentials
    """

    def __init__(
        self,
        grant_type: str = Form(None, regex="client_credentials"),
        scope: str = Form(""),
        client_id: Optional[str] = Form(None),
        client_secret: Optional[str] = Form(None),
    ):
        self.grant_type = grant_type
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret
