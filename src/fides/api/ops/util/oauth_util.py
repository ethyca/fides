from __future__ import annotations

import json
from datetime import datetime

from fastapi import Depends, HTTPException, Security
from fastapi.security import SecurityScopes
from jose import exceptions
from jose.constants import ALGORITHMS
from loguru import logger
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND

from fides.api.ops.api.deps import get_db
from fides.api.ops.api.v1.scope_registry import SCOPE_REGISTRY
from fides.api.ops.api.v1.urn_registry import TOKEN, V1_URL_PREFIX
from fides.api.ops.models.policy import PolicyPreWebhook
from fides.api.ops.schemas.external_https import WebhookJWE
from fides.core.config import get_config
from fides.lib.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fides.lib.exceptions import AuthenticationError, AuthorizationError
from fides.lib.models.client import ClientDetail
from fides.lib.models.fides_user import FidesUser
from fides.lib.oauth.oauth_util import extract_payload, is_token_expired
from fides.lib.oauth.schemas.oauth import OAuth2ClientCredentialsBearer

CONFIG = get_config()
JWT_ENCRYPTION_ALGORITHM = ALGORITHMS.A256GCM


# TODO: include list of all scopes in the docs via the scopes={} dict
# (see https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)
oauth2_scheme = OAuth2ClientCredentialsBearer(
    tokenUrl=(V1_URL_PREFIX + TOKEN),
)


async def get_current_user(
    security_scopes: SecurityScopes,
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(get_db),
) -> FidesUser:
    """A wrapper around verify_oauth_client that returns that client's user if one exists."""
    client = await verify_oauth_client(
        security_scopes=security_scopes,
        authorization=authorization,
        db=db,
    )

    if client.id == CONFIG.security.oauth_root_client_id:
        return FidesUser(
            id=CONFIG.security.oauth_root_client_id,
            username=CONFIG.security.root_username,
            created_at=datetime.utcnow(),
        )

    return client.user  # type: ignore[attr-defined]


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


async def verify_oauth_client(
    security_scopes: SecurityScopes,
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(get_db),
) -> ClientDetail:
    """
    Verifies that the access token provided in the authorization header contains
    the necessary scopes specified by the caller. Yields a 403 forbidden error
    if not
    """
    if authorization is None:
        logger.debug("No authorization supplied.")
        raise AuthenticationError(detail="Authentication Failure")

    try:
        token_data = json.loads(
            extract_payload(authorization, CONFIG.security.app_encryption_key)
        )
    except exceptions.JWEParseError as exc:
        logger.debug("Unable to parse auth token.")
        raise AuthorizationError(detail="Not Authorized for this action") from exc

    issued_at = token_data.get(JWE_ISSUED_AT, None)
    if not issued_at:
        logger.debug("Auth token expired.")
        raise AuthorizationError(detail="Not Authorized for this action")

    if is_token_expired(
        datetime.fromisoformat(issued_at),
        CONFIG.security.oauth_access_token_expire_minutes,
    ):
        raise AuthorizationError(detail="Not Authorized for this action")

    assigned_scopes = token_data[JWE_PAYLOAD_SCOPES]
    if not set(security_scopes.scopes).issubset(assigned_scopes):
        scopes_required = ",".join(security_scopes.scopes)
        scopes_provided = ",".join(assigned_scopes)
        logger.debug(
            "Auth token missing required scopes: {}. Scopes provided: {}.",
            scopes_required,
            scopes_provided,
        )
        raise AuthorizationError(detail="Not Authorized for this action")

    client_id = token_data.get(JWE_PAYLOAD_CLIENT_ID)
    if not client_id:
        logger.debug("No client_id included in auth token.")
        raise AuthorizationError(detail="Not Authorized for this action")

    # scopes param is only used if client is root client, otherwise we use the client's associated scopes
    client = ClientDetail.get(
        db, object_id=client_id, config=CONFIG, scopes=SCOPE_REGISTRY
    )

    if not client:
        logger.debug("Auth token belongs to an invalid client_id.")
        raise AuthorizationError(detail="Not Authorized for this action")

    if not set(assigned_scopes).issubset(set(client.scopes)):
        # If the scopes on the token are not a subset of the scopes available
        # to the associated oauth client, this token is not valid
        logger.debug("Client no longer allowed to issue these scopes.")
        raise AuthorizationError(detail="Not Authorized for this action")
    return client
