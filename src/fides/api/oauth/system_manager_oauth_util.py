from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from fastapi import Depends, Security
from fastapi.security import SecurityScopes
from fideslang.models import System as SystemSchema
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.api.deps import get_db
from fides.api.common_exceptions import AuthorizationError
from fides.api.cryptography.schemas.jwt import JWE_PAYLOAD_SYSTEMS
from fides.api.models.client import ClientDetail
from fides.api.models.sql_models import System  # type: ignore[attr-defined]
from fides.api.oauth.system_manager import SYSTEM_MANAGER_SCOPES
from fides.api.oauth.utils import (
    copy_func,
    extract_token_and_load_client,
    has_permissions,
    has_scope_subset,
    oauth2_scheme,
)


class SystemAuthContainer:
    """Data class to store the original request data containing the information to retrieve the system,
    plus the System(s) themselves.

    We're returning the original request body or path param so we can continue to use all the current
    checks that exist for the crud endpoints without modification.  For example, we need to run additional
    checks that the system exists downstream for other purposes.
    """

    def __init__(
        self,
        original_data: Union[str, SystemSchema],
        system: Optional[System],
    ):
        self.original_data = original_data
        self.system = system


def _get_system_from_request_body(
    system_data: SystemSchema, db: Session = Depends(get_db)
) -> SystemAuthContainer:
    """Returns the fetched System (retrieved from the *request body*) along with the original request body.

    This function is passed as a *dependency* into verify_oauth_client_for_system_from_request_body.
    """
    resp = SystemAuthContainer(original_data=system_data, system=None)
    resource_dict = system_data.model_dump(mode="json")
    if resource_dict.get("fides_key"):
        system = (
            db.query(System)
            .filter(System.fides_key == resource_dict.get("fides_key"))
            .first()
        )
        resp.system = system
    return resp


def _get_system_from_fides_key(
    fides_key: str, db: Session = Depends(get_db)
) -> SystemAuthContainer:
    """Returns the fetched System (retrieved from the *fides_key* path parameter) along with the original fides_key.

    This function is passed as a *dependency* into verify_oauth_client_for_system_from_fides_key.
    """
    resp = SystemAuthContainer(original_data=fides_key, system=None)
    system = db.query(System).filter(System.fides_key == fides_key).first()
    resp.system = system
    return resp


async def verify_oauth_client_for_system_from_request_body(
    security_scopes: SecurityScopes,
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(get_db),
    system_auth_data: SystemAuthContainer = Depends(_get_system_from_request_body),
) -> Union[str, System]:
    """
    Verifies that the access token provided in the authorization header contains the necessary scopes to be
    able to access the System found in the *request body*

    The user must either have 1) the correct scope(s) 2) a role encompassing the necessary scope or 3) the user
    is a system manager of the given system which gives them the proper scope.

    Yields a 403 forbidden error if not.
    """

    system = has_system_permissions(
        system_auth_data=system_auth_data,
        authorization=authorization,
        security_scopes=security_scopes,
        db=db,
    )
    return system


async def verify_oauth_client_for_system_from_fides_key(
    security_scopes: SecurityScopes,
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(get_db),
    system_auth_data: SystemAuthContainer = Depends(_get_system_from_fides_key),
) -> str:
    """
    Verifies that the access token provided in the authorization header contains the necessary scopes to be
    able to access the System from the given *fides_key* in the path parameter.

    The user must either have 1) the correct scope(s) 2) a role encompassing the necessary scope or 3) the user
    is a system manager of the given system which gives them the proper scope.

    Yields a 403 forbidden error if not.
    """
    system = has_system_permissions(
        system_auth_data=system_auth_data,
        authorization=authorization,
        security_scopes=security_scopes,
        db=db,
    )
    assert isinstance(system, str)
    return system


def has_system_permissions(
    system_auth_data: SystemAuthContainer,
    authorization: str,
    security_scopes: SecurityScopes,
    db: Session,
) -> Union[str, System]:
    """
    Helper method that verifies that the token has the proper permissions to access the system(s).

    This method is shared between methods that use different dependency injections, depending on whether the system
    data is located in the path parameter or in the request body.
    """
    token_data, client = extract_token_and_load_client(
        authorization, db
    )  # Can raise permission errors if issues with client or token

    has_model_level_permissions: bool = (
        has_permissions(  # Token has the correct scope(s) or role(s) associated with the correct scopes
            token_data, client, security_scopes
        )
    )
    has_system_manager_permissions: bool = (
        _has_scope_as_system_manager(  # Token indicates system manager permissions of the current system(s)
            token_data, client, security_scopes, system_auth_data.system
        )
    )

    has_perms: bool = has_model_level_permissions or has_system_manager_permissions

    if not has_perms:
        raise AuthorizationError(detail="Not Authorized for this action")

    return system_auth_data.original_data


def _has_scope_as_system_manager(
    token_data: Dict[str, Any],
    client: ClientDetail,
    endpoint_scopes: SecurityScopes,
    system: Optional[System],
) -> bool:
    """Does the user have the proper scope as system manager?

    Returns True if the 1) system(s) exist, 2) the system(s) are on the user's token, 3) the token is still valid, meaning
    the system(s) are still on the user's client and 4) system manager scopes contain the necessary scope(s) for this endpoint.
    """
    if not system:
        logger.debug("System resource not found.")
        return False

    assigned_systems: List[str] = token_data.get(JWE_PAYLOAD_SYSTEMS, [])
    if not system.id in assigned_systems:
        logger.debug("Systems are not on the user's token.")
        return False

    if not set(assigned_systems).issubset(set(client.systems or [])):
        # If the system on the token is not included on the client, this token is no longer valid
        logger.debug("Client no longer allowed to issue this system.")
        return False

    if not has_scope_subset(
        user_scopes=SYSTEM_MANAGER_SCOPES, endpoint_scopes=endpoint_scopes
    ):
        logger.debug(
            "System manager scopes don't include required scopes to access this endpoint."
        )
        return False

    return True


# This is a workaround so that we can override CLI-related endpoints and
# all other endpoints separately.
verify_oauth_client_for_system_from_request_body_cli = copy_func(
    verify_oauth_client_for_system_from_request_body
)
verify_oauth_client_for_system_from_fides_key_cli = copy_func(
    verify_oauth_client_for_system_from_fides_key
)


async def get_system_schema(system_data: SystemSchema) -> SystemSchema:
    """
    Return system request body directly.  An override to bypass authentication for updating systems in dev mode.
    """
    return system_data


async def get_system_fides_key(fides_key: str) -> str:
    """
    Return system fides_key path parameter directly.  An override to bypass authentication for deleting systems in dev mode.
    """
    return fides_key
