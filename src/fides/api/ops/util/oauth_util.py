from __future__ import annotations

import json
from datetime import datetime

from fastapi import Depends, HTTPException, Security
from fastapi.security import SecurityScopes
from fideslib.cryptography.schemas.jwt import JWE_PAYLOAD_SCOPES
from fideslib.exceptions import AuthenticationError, AuthorizationError
from fideslib.models.client import ClientDetail
from fideslib.models.fides_user import FidesUser
from fideslib.oauth.oauth_util import extract_payload
from fideslib.oauth.oauth_util import verify_oauth_client as verify
from fideslib.oauth.schemas.oauth import OAuth2ClientCredentialsBearer
from jose.constants import ALGORITHMS
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND

from fides.api.ops.api.deps import get_db
from fides.api.ops.api.v1.urn_registry import TOKEN, V1_URL_PREFIX
from fides.api.ops.models.policy import PolicyPreWebhook
from fides.api.ops.schemas.external_https import WebhookJWE
from fides.ctl.core.config import get_config

CONFIG = get_config()
JWT_ENCRYPTION_ALGORITHM = ALGORITHMS.A256GCM


oauth2_scheme = OAuth2ClientCredentialsBearer(
    tokenUrl=(V1_URL_PREFIX + TOKEN),
)


async def get_current_user(
    security_scopes: SecurityScopes,
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(get_db),
) -> FidesUser:
    """A wrapper around verify_oauth_client that returns that client's user if one exsits."""
    client = await verify_oauth_client(
        security_scopes=security_scopes,
        authorization=authorization,
        db=db,
    )
    return client.user


def is_callback_token_expired(issued_at: datetime | None) -> bool:
    """Returns True if the token is older than the expiration of the redis cache.  We
    can't resume executing the privacy request if the identity data is gone.
    """
    if not issued_at:
        return True

    return (
        datetime.now() - issued_at
    ).total_seconds() / 60.0 > CONFIG.execution.privacy_request_delay_timeout


def verify_callback_oauth(
    security_scopes: SecurityScopes,
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(get_db),
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
        raise AuthenticationError(detail="Authentication Failure")

    token_data = json.loads(
        extract_payload(authorization, CONFIG.security.app_encryption_key)
    )
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


def verify_oauth_client(
    security_scopes: SecurityScopes,
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(get_db),
) -> ClientDetail:
    """Calls fideslib oauth_util.verify_oauth_client.

    This override is needed because we have to pass in the config.
    """
    return verify(security_scopes, authorization, db=db, config=CONFIG)
