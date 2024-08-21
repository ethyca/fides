from __future__ import annotations

import json
from datetime import datetime
from functools import update_wrapper
from types import FunctionType
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import Depends, HTTPException, Security
from fastapi.security import SecurityScopes
from jose import exceptions, jwe
from jose.constants import ALGORITHMS
from loguru import logger
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND

from fides.api.api.deps import get_db
from fides.api.common_exceptions import AuthenticationError, AuthorizationError
from fides.api.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_ROLES,
    JWE_PAYLOAD_SCOPES,
)
from fides.api.models.client import ClientDetail
from fides.api.models.fides_user import FidesUser
from fides.api.models.policy import PolicyPreWebhook
from fides.api.models.pre_approval_webhook import PreApprovalWebhook
from fides.api.models.privacy_request import RequestTask
from fides.api.oauth.roles import get_scopes_from_roles
from fides.api.schemas.external_https import RequestTaskJWE, WebhookJWE
from fides.api.schemas.oauth import OAuth2ClientCredentialsBearer
from fides.common.api.v1.urn_registry import TOKEN, V1_URL_PREFIX
from fides.config import CONFIG

JWT_ENCRYPTION_ALGORITHM = ALGORITHMS.A256GCM


# TODO: include list of all scopes in the docs via the scopes={} dict
# (see https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)
oauth2_scheme = OAuth2ClientCredentialsBearer(
    tokenUrl=(V1_URL_PREFIX + TOKEN),
)


def extract_payload(jwe_string: str, encryption_key: str) -> str:
    """Given a jwe, extracts the payload and returns it in string form."""
    return jwe.decrypt(jwe_string, encryption_key)


def is_token_expired(issued_at: datetime | None, token_duration_min: int) -> bool:
    """Returns True if the datetime is earlier than token_duration_min ago."""
    if not issued_at:
        return True

    return (datetime.now() - issued_at).total_seconds() / 60.0 > token_duration_min


def copy_func(source_function: Callable) -> Callable:
    """Based on http://stackoverflow.com/a/6528148/190597 (Glenn Maynard)"""
    target_function = FunctionType(
        source_function.__code__,
        source_function.__globals__,
        name=source_function.__name__,
        argdefs=source_function.__defaults__,
        closure=source_function.__closure__,
    )
    updated_target_function: Callable = update_wrapper(target_function, source_function)
    updated_target_function.__kwdefaults__ = source_function.__kwdefaults__
    return updated_target_function


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


def _get_webhook_jwe_or_error(
    security_scopes: SecurityScopes, authorization: str = Security(oauth2_scheme)
) -> WebhookJWE:
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

    return token


def _get_request_task_jwe_or_error(
    security_scopes: SecurityScopes, authorization: str = Security(oauth2_scheme)
) -> RequestTaskJWE:
    if authorization is None:
        raise AuthenticationError(detail="Authentication Failure")

    try:
        token_data = json.loads(
            extract_payload(authorization, CONFIG.security.app_encryption_key)
        )
    except exceptions.JWEError:
        raise AuthorizationError(detail="Not Authorized for this action")

    try:
        token = RequestTaskJWE(**token_data)
    except ValidationError:
        raise AuthorizationError(detail="Not Authorized for this action")

    assigned_scopes = token_data[JWE_PAYLOAD_SCOPES]
    if not set(security_scopes.scopes).issubset(assigned_scopes):
        raise AuthorizationError(detail="Not Authorized for this action")

    if is_callback_token_expired(datetime.fromisoformat(token.iat)):
        raise AuthorizationError(detail="Request Task token expired")

    return token


def verify_callback_oauth_policy_pre_webhook(
    security_scopes: SecurityScopes,
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(get_db),
) -> PolicyPreWebhook:
    """
    Verifies the specific token that accompanies a request when the caller wants to resume executing a
    PrivacyRequest after it was paused by a webhook.

    Note that this token was sent along with the request when calling the webhook originally.
    Verifies that the webhook token hasn't expired and loads the webhook from that token.
    Also verifies scopes, but note that this was given to the user in a request header and they've
    just returned it back.
    """
    token = _get_webhook_jwe_or_error(security_scopes, authorization)

    webhook = PolicyPreWebhook.get_by(db, field="id", value=token.webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No Policy Pre-Execution Webhook found with id '{token.webhook_id}'.",
        )
    return webhook


def verify_callback_oauth_pre_approval_webhook(
    security_scopes: SecurityScopes,
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(get_db),
) -> PreApprovalWebhook:
    """
    Verifies the specific token that accompanies a request when the caller wants to mark a PrivacyRequest
    as eligible or not eligible for pre-approval.

    Note that this token was sent along with the request when calling the webhook originally.
    Verifies that the webhook token hasn't expired and loads the webhook from that token.
    Also verifies scopes, but note that this was given to the user in a request header and they've
    just returned it back.
    """
    token = _get_webhook_jwe_or_error(security_scopes, authorization)

    webhook = PreApprovalWebhook.get_by(db, field="id", value=token.webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No Pre-Approval Webhook found with id '{token.webhook_id}'.",
        )
    return webhook


def verify_request_task_callback(
    security_scopes: SecurityScopes,
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(get_db),
) -> RequestTask:
    """
    Verifies that the specific token when the request task callback endpoint is hit is valid.
    Loads the Request Task included in the token
    """
    token = _get_request_task_jwe_or_error(security_scopes, authorization)

    request_task = RequestTask.get_by(db, field="id", value=token.request_task_id)

    if not request_task:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No Request Task found with id '{token.request_task_id}'.",
        )
    return request_task


async def get_root_client(
    db: Session = Depends(get_db), client_id: str = CONFIG.security.oauth_root_client_id
) -> ClientDetail:
    """
    Gets the root_client directly.

    This function is primarily used to let users bypass endpoint authorization
    """
    client = ClientDetail.get(
        db,
        object_id=client_id,
        config=CONFIG,
        scopes=CONFIG.security.root_user_scopes,
        roles=CONFIG.security.root_user_roles,
    )
    if not client:
        logger.debug("Auth token belongs to an invalid client_id.")
        raise AuthorizationError(detail="Not Authorized for this action")
    return client


async def verify_oauth_client(
    security_scopes: SecurityScopes,
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(get_db),
) -> ClientDetail:
    """
    Verifies that the access token provided in the authorization header contains
    the necessary scopes or roles specified by the caller. Yields a 403 forbidden error
    if not.

    NOTE: This function may be overwritten in `main.py` when changing
    the security environment.
    """
    token_data, client = extract_token_and_load_client(authorization, db)
    if not has_permissions(
        token_data=token_data, client=client, endpoint_scopes=security_scopes
    ):
        raise AuthorizationError(
            detail=f"Not Authorized for this action. Required scope(s): [{', '.join(security_scopes.scopes)}]"
        )

    return client


def extract_token_and_load_client(
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(get_db),
    *,
    token_duration_override: Optional[int] = None,
) -> Tuple[Dict, ClientDetail]:
    """Extract the token, verify it's valid, and likewise load the client as part of authorization"""
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
        token_duration_override or CONFIG.security.oauth_access_token_expire_minutes,
    ):
        raise AuthorizationError(detail="Not Authorized for this action")

    client_id = token_data.get(JWE_PAYLOAD_CLIENT_ID)
    if not client_id:
        logger.debug("No client_id included in auth token.")
        raise AuthorizationError(detail="Not Authorized for this action")

    # scopes/roles param is only used if client is root client, otherwise we use the client's associated scopes
    client = ClientDetail.get(
        db,
        object_id=client_id,
        config=CONFIG,
        scopes=CONFIG.security.root_user_scopes,
        roles=CONFIG.security.root_user_roles,
    )

    if not client:
        logger.debug("Auth token belongs to an invalid client_id.")
        raise AuthorizationError(detail="Not Authorized for this action")

    return token_data, client


def has_permissions(
    token_data: Dict[str, Any], client: ClientDetail, endpoint_scopes: SecurityScopes
) -> bool:
    """Does the user have the necessary scopes, either via a scope they were assigned directly,
    or a scope associated with their role(s)?"""
    has_direct_scope: bool = _has_direct_scopes(
        token_data=token_data, client=client, endpoint_scopes=endpoint_scopes
    )
    has_role: bool = _has_scope_via_role(
        token_data=token_data, client=client, endpoint_scopes=endpoint_scopes
    )
    return has_direct_scope or has_role


def _has_scope_via_role(
    token_data: Dict[str, Any], client: ClientDetail, endpoint_scopes: SecurityScopes
) -> bool:
    """Does the user have the required scopes indirectly via a role and is the token valid?"""
    assigned_roles: List[str] = token_data.get(JWE_PAYLOAD_ROLES, [])
    associated_scopes: List[str] = get_scopes_from_roles(assigned_roles)

    if not has_scope_subset(
        user_scopes=associated_scopes, endpoint_scopes=endpoint_scopes
    ):
        return False

    if not set(assigned_roles).issubset(set(client.roles or [])):
        # If the roles on the token are not a subset of the roles available
        # one the associated oauth client, this token is not valid
        logger.debug("Client no longer allowed to issue these roles.")
        return False

    return True


def _has_direct_scopes(
    token_data: Dict[str, Any], client: ClientDetail, endpoint_scopes: SecurityScopes
) -> bool:
    """Does the token have the required scopes directly and is the token still valid?"""
    assigned_scopes: List[str] = token_data.get(JWE_PAYLOAD_SCOPES, [])

    if not has_scope_subset(
        user_scopes=assigned_scopes, endpoint_scopes=endpoint_scopes
    ):
        return False

    if not set(assigned_scopes).issubset(set(client.scopes or [])):
        # If the scopes on the token are not a subset of the scopes available
        # to the associated oauth client, this token is not valid
        logger.debug("Client no longer allowed to issue these scopes.")
        return False

    return True


def has_scope_subset(user_scopes: List[str], endpoint_scopes: SecurityScopes) -> bool:
    """Are the required scopes a subset of the scopes belonging to the user?"""
    if not set(endpoint_scopes.scopes).issubset(user_scopes):
        scopes_required = ",".join(endpoint_scopes.scopes)
        scopes_provided = ",".join(user_scopes)
        logger.debug(
            "Auth token missing required scopes: {}. Scopes provided: {}.",
            scopes_required,
            scopes_provided,
        )
        return False
    return True


# This allows us to selectively enforce auth depending on user environment settings
verify_oauth_client_prod = copy_func(verify_oauth_client)
