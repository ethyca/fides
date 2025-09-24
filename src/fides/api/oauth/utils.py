from __future__ import annotations

import json
from datetime import datetime
from functools import update_wrapper
from types import FunctionType
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import SecurityScopes
from jose import exceptions, jwe
from jose.constants import ALGORITHMS
from loguru import logger
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from fides.api.api.deps import get_db
from fides.api.common_exceptions import AuthenticationError, AuthorizationError
from fides.api.cryptography.cryptographic_util import generate_secure_random_string
from fides.api.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_ROLES,
    JWE_PAYLOAD_SCOPES,
)
from fides.api.models.client import ClientDetail
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.policy import PolicyPreWebhook
from fides.api.models.pre_approval_webhook import PreApprovalWebhook
from fides.api.models.privacy_request import RequestTask
from fides.api.oauth.roles import ROLES_TO_SCOPES_MAPPING, get_scopes_from_roles
from fides.api.request_context import set_user_id
from fides.api.schemas.external_https import (
    DownloadTokenJWE,
    RequestTaskJWE,
    WebhookJWE,
)
from fides.api.schemas.oauth import OAuth2ClientCredentialsBearer
from fides.common.api.v1.urn_registry import TOKEN, V1_URL_PREFIX
from fides.config import CONFIG, FidesConfig

JWT_ENCRYPTION_ALGORITHM = ALGORITHMS.A256GCM


# TODO: include list of all scopes in the docs via the scopes={} dict
# (see https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)
oauth2_scheme = OAuth2ClientCredentialsBearer(
    tokenUrl=(V1_URL_PREFIX + TOKEN),
)


def extract_payload(jwe_string: str, encryption_key: str) -> str:
    """Given a jwe, extracts the payload and returns it in string form."""
    try:
        decrypted_payload = jwe.decrypt(jwe_string, encryption_key)
        return decrypted_payload.decode("utf-8")
    except exceptions.JWEError as e:
        logger.debug("Failed to decrypt JWE: {}", e)
        raise e


def is_token_expired(
    issued_at: Optional[datetime], token_duration_minutes: int
) -> bool:
    """Check if a token has expired based on its issued_at timestamp and duration."""
    if issued_at is None:
        return True
    return (datetime.now() - issued_at).total_seconds() / 60.0 > token_duration_minutes


def is_callback_token_expired(issued_at: Optional[datetime]) -> bool:
    """Check if a callback token has expired (24 hours)."""
    if not issued_at:
        return True

    return (
        datetime.now() - issued_at
    ).total_seconds() / 60.0 > CONFIG.execution.privacy_request_delay_timeout


def is_token_invalidated(issued_at: datetime, client: ClientDetail) -> bool:
    """
    Return True if the token should be considered invalid due to security events
    (e.g., user password reset) that occurred after the token was issued.

    Any errors accessing related objects are logged and treated as non-invalidating.
    """
    try:
        if (
            client.user is not None
            and client.user.password_reset_at is not None
            and issued_at < client.user.password_reset_at
        ):
            return True
        return False
    except Exception as exc:
        logger.exception(
            "Unable to evaluate password reset timestamp for client user: {}", exc
        )
        return False


def _get_webhook_jwe_or_error(
    security_scopes: SecurityScopes, authorization: str = Security(oauth2_scheme)
) -> WebhookJWE:
    if authorization is None:
        raise AuthenticationError(detail="Authentication Failure")

    try:
        token_data = json.loads(
            extract_payload(authorization, CONFIG.security.app_encryption_key)
        )
    except exceptions.JWEError:
        raise AuthorizationError(detail="Not Authorized for this action")

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


def validate_download_token(token: str, privacy_request_id: str) -> DownloadTokenJWE:
    """
    Validate a download token for accessing privacy request packages.

    Args:
        token: The JWE token to validate
        privacy_request_id: The privacy request ID the token should grant access to

    Returns:
        The validated DownloadTokenJWE object

    Raises:
        AuthenticationError: If token is invalid or expired
        AuthorizationError: If token doesn't grant access to the requested privacy request
    """
    if not token:
        raise AuthenticationError(detail="Download token is required")

    # Check if token looks like a JWE (should have 5 parts separated by dots)
    if token.count(".") != 4:
        raise AuthenticationError(detail="Invalid download token format")

    try:
        token_data = json.loads(
            extract_payload(token, CONFIG.security.app_encryption_key)
        )
    except exceptions.JWEError:
        raise AuthenticationError(detail="Invalid download token format")

    try:
        download_token = DownloadTokenJWE(**token_data)
    except ValidationError:
        raise AuthenticationError(detail="Invalid download token structure")

    # Verify the token grants access to the requested privacy request
    if download_token.privacy_request_id != privacy_request_id:
        raise AuthorizationError(
            detail="Download token does not grant access to this privacy request"
        )

    # Verify the token has the required scope
    required_scope = "privacy-request-access-results:read"
    if required_scope not in download_token.scopes:
        raise AuthorizationError(detail="Download token lacks required permissions")

    # Check if the token has expired
    try:
        expiration_time = datetime.fromisoformat(download_token.exp)
        if datetime.now() > expiration_time:
            raise AuthenticationError(detail="Download token has expired")
    except (ValueError, TypeError):
        raise AuthenticationError(detail="Invalid token expiration format")

    return download_token


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

    return cast(FidesUser, client.user)


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

    issued_at_dt = datetime.fromisoformat(issued_at)

    if is_token_expired(
        issued_at_dt,
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

    # Invalidate tokens issued prior to the user's most recent password reset.
    # This ensures any existing sessions are expired immediately after a password change.
    if is_token_invalidated(issued_at_dt, client):
        logger.debug("Auth token issued before latest password reset.")
        raise AuthorizationError(detail="Not Authorized for this action")

    # Populate request-scoped context with the authenticated user identifier.
    # Prefer the linked user_id; fall back to the client id when this is the
    # special root client (which has no associated FidesUser row).
    ctx_user_id = client.user_id
    if not ctx_user_id and client.id == CONFIG.security.oauth_root_client_id:
        ctx_user_id = CONFIG.security.oauth_root_client_id

    if ctx_user_id:
        set_user_id(ctx_user_id)

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

    has_required_permissions = has_direct_scope or has_role
    if not has_required_permissions:
        scopes_required = ",".join(endpoint_scopes.scopes)
        logger.debug(
            "Authorization failed. Missing required scopes: {}. Neither direct scopes nor role-derived scopes were sufficient.",
            scopes_required,
        )

    return has_required_permissions


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
    return set(endpoint_scopes.scopes).issubset(user_scopes)


def get_client_effective_scopes(client: "ClientDetail") -> List[str]:
    """
    Get all scopes available to a client, including both direct scopes and role-derived scopes.

    Args:
        client: The ClientDetail instance

    Returns:
        List of scope strings that the client has access to
    """
    effective_scopes = set()

    # Add direct scopes
    if client.scopes:
        effective_scopes.update(client.scopes)

    # Add role-derived scopes
    if client.roles:
        for role in client.roles:
            role_scopes = ROLES_TO_SCOPES_MAPPING.get(role, [])
            effective_scopes.update(role_scopes)

    # Add user permission scopes if client is associated with a user
    # Note: client.user is available via SQLAlchemy backref from FidesUser.client relationship
    user = getattr(client, "user", None)  # Use getattr to avoid mypy attr-defined error
    if user and hasattr(user, "permissions") and user.permissions:
        effective_scopes.update(user.permissions.total_scopes)

    return sorted(list(effective_scopes))


def verify_client_can_assign_scopes(
    request: "Request",
    requesting_client: "ClientDetail",
    scopes: List[str],
    db: "Session",
) -> None:
    """
    Verify that a requesting client has permission to assign the given scopes.

    Raises HTTPException if the client lacks permission.
    Root client is exempt from this check.

    Args:
        request: FastAPI request object containing Authorization header
        requesting_client: The client making the request
        scopes: List of scopes to be assigned
        db: Database session

    Raises:
        HTTPException: If the client lacks permission to assign the scopes
    """
    # Root client can assign any scope
    if requesting_client.id == CONFIG.security.oauth_root_client_id:
        return

    # Get the actual token scopes (not the client's database scopes)
    authorization = request.headers.get("Authorization", "").replace("Bearer ", "")
    token_data, _ = extract_token_and_load_client(authorization, db)

    # Get token's effective scopes
    token_scopes = token_data.get("scopes", [])

    # Check if user has the scopes via roles as well
    has_scope_via_role = has_permissions(
        token_data=token_data,
        client=requesting_client,
        endpoint_scopes=SecurityScopes(scopes),
    )

    # If they don't have all scopes via direct assignment or roles, check individual scopes
    if not has_scope_via_role:
        unauthorized_scopes = set(scopes) - set(token_scopes)

        if unauthorized_scopes:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail=f"Cannot assign scopes that you do not have. Missing scopes: {sorted(unauthorized_scopes)}",
            )


def create_temporary_user_for_login_flow(config: FidesConfig) -> FidesUser:
    """
    Create a temporary FidesUser in-memory with an attached in-memory ClientDetail
    and attached in-memory FidesUserPermissions

    This is for reducing the time differences in the user login flow between a
    valid and an invalid user
    """
    hashed_password, salt = FidesUser.hash_password(generate_secure_random_string(16))
    user = FidesUser(
        **{
            "salt": salt,
            "hashed_password": hashed_password,
            "username": "temp_user",
            "email_address": "temp_user@example.com",
            "first_name": "temp_first_name",
            "last_name": "temp_surname",
            "disabled": True,
        }
    )

    # Create in-memory user permissions
    user.permissions = FidesUserPermissions(  # type: ignore[attr-defined]
        id="temp_user_id",
        user_id="temp_user_id",
        roles=["fake_role"],
    )

    # Create in-memory client, not persisted to db
    client, _ = ClientDetail.create_client_and_secret(
        None,  # type: ignore[arg-type]
        config.security.oauth_client_id_length_bytes,
        config.security.oauth_client_secret_length_bytes,
        scopes=[],  # type: ignore
        roles=user.permissions.roles,  # type: ignore
        systems=user.system_ids,  # type: ignore
        user_id="temp_user_id",
        in_memory=True,
    )

    user.client = client

    return user


# This allows us to selectively enforce auth depending on user environment settings
verify_oauth_client_prod = copy_func(verify_oauth_client)
