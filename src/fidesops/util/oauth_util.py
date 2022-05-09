import json
from datetime import datetime
from typing import Optional
from starlette.status import HTTP_404_NOT_FOUND
from pydantic import ValidationError

from fastapi import Depends, Security, HTTPException
from fastapi.security import SecurityScopes
from jose import jwe
from jose.constants import ALGORITHMS
from sqlalchemy.orm import Session

from fidesops.api import deps
from fidesops.api.v1.urn_registry import V1_URL_PREFIX, TOKEN
from fidesops.common_exceptions import AuthorizationError, AuthenticationFailure
from fidesops.core.config import config
from fidesops.models.client import ClientDetail
from fidesops.models.fidesops_user import FidesopsUser
from fidesops.models.policy import PolicyPreWebhook
from fidesops.schemas.external_https import WebhookJWE
from fidesops.schemas.oauth import OAuth2ClientCredentialsBearer
from fidesops.schemas.jwt import (
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
    JWE_ISSUED_AT,
)

__JWT_ENCRYPTION_ALGORITHM = ALGORITHMS.A256GCM


# TODO: include list of all scopes in the docs via the scopes={} dict
# (see https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)
oauth2_scheme = OAuth2ClientCredentialsBearer(
    tokenUrl=(V1_URL_PREFIX + TOKEN),
)


async def verify_oauth_client(
    security_scopes: SecurityScopes,
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(deps.get_db),
) -> ClientDetail:
    """
    Verifies that the access token provided in the authorization header contains
    the necessary scopes specified by the caller. Yields a 403 forbidden error
    if not
    """
    if authorization is None:
        raise AuthenticationFailure(detail="Authentication Failure")

    token_data = json.loads(extract_payload(authorization))

    issued_at = token_data.get(JWE_ISSUED_AT, None)
    if not issued_at:
        raise AuthorizationError(detail="Not Authorized for this action")

    if is_token_expired(datetime.fromisoformat(issued_at)):
        raise AuthorizationError(detail="Not Authorized for this action")

    assigned_scopes = token_data[JWE_PAYLOAD_SCOPES]
    if not set(security_scopes.scopes).issubset(assigned_scopes):
        raise AuthorizationError(detail="Not Authorized for this action")

    client_id = token_data.get(JWE_PAYLOAD_CLIENT_ID)
    if not client_id:
        raise AuthorizationError(detail="Not Authorized for this action")

    client = ClientDetail.get(db, id=client_id)
    if not client:
        raise AuthorizationError(detail="Not Authorized for this action")

    if not set(assigned_scopes).issubset(set(client.scopes)):
        # If the scopes on the token are not a subset of the scopes available
        # to the associated oauth client, this token is not valid
        raise AuthorizationError(detail="Not Authorized for this action")
    return client


async def get_current_user(
    security_scopes: SecurityScopes,
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(deps.get_db),
) -> FidesopsUser:
    """A wrapper around verify_oauth_client that returns that client's user if one exsits."""
    client = await verify_oauth_client(
        security_scopes=security_scopes,
        authorization=authorization,
        db=db,
    )
    return client.user


def is_token_expired(issued_at: Optional[datetime]) -> bool:
    """Returns True if the datetime is earlier than OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES ago"""
    if not issued_at:
        return True

    return (
        datetime.now() - issued_at
    ).total_seconds() / 60.0 > config.security.OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES


def generate_jwe(payload: str) -> str:
    """Generates a JWE with the provided payload. Returns a string representation"""
    return jwe.encrypt(
        payload,
        config.security.APP_ENCRYPTION_KEY,
        encryption=__JWT_ENCRYPTION_ALGORITHM,
    ).decode(config.security.ENCODING)


def extract_payload(jwe_string: str) -> str:
    """Given a jwe, extracts the payload and returns it in string form"""
    return jwe.decrypt(jwe_string, config.security.APP_ENCRYPTION_KEY)


def is_callback_token_expired(issued_at: Optional[datetime]) -> bool:
    """Returns True if the token is older than the expiration of the redis cache.  We
    can't resume executing the privacy request if the identity data is gone.
    """
    if not issued_at:
        return True

    return (
        datetime.now() - issued_at
    ).total_seconds() / 60.0 > config.execution.PRIVACY_REQUEST_DELAY_TIMEOUT


def verify_callback_oauth(
    security_scopes: SecurityScopes,
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(deps.get_db),
) -> PolicyPreWebhook:
    """
    Verifies the specific token that accompanies a request when a user wants to resume executing
    a PrivacyRequest after it was paused by a webhook. Note that this token was sent along with the
    request when calling the webhook originally.

    Verifies that the webhook token hasn't expired and loads the webhook from that token.

    Also verifies scopes, but note that this was given to the user in a request header and they've
    just returned it back.
    """
    if authorization is None:
        raise AuthenticationFailure(detail="Authentication Failure")

    token_data = json.loads(extract_payload(authorization))
    try:
        token = WebhookJWE(**token_data)
    except ValidationError:
        raise AuthorizationError(detail="Not Authorized for this action")

    assigned_scopes = token_data[JWE_PAYLOAD_SCOPES]
    if not set(security_scopes.scopes).issubset(assigned_scopes):
        raise AuthorizationError(detail="Not Authorized for this action")

    if is_callback_token_expired(datetime.fromisoformat(token.iat)):
        raise AuthorizationError(detail="Webhook token expired")

    webhook = PolicyPreWebhook.get_by(db, field="id", value=token.webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No Policy Pre-Execution Webhook found with id '{token.webhook_id}'.",
        )
    return webhook
