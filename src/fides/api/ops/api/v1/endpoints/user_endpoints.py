import json
from typing import List, Optional

import jose.exceptions
from fastapi import Depends, HTTPException, Security
from fideslang.models import System as SystemSchema
from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.orm import Query, Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from fides.api.ctl.sql_models import System  # type: ignore[attr-defined]
from fides.api.ops.api import deps
from fides.api.ops.api.deps import get_db
from fides.api.ops.api.v1 import urn_registry as urls
from fides.api.ops.api.v1.endpoints.user_permission_endpoints import validate_user_id
from fides.api.ops.api.v1.scope_registry import (
    SCOPE_REGISTRY,
    SYSTEM_MANAGER_DELETE,
    SYSTEM_MANAGER_READ,
    SYSTEM_MANAGER_UPDATE,
    USER_PASSWORD_RESET,
    USER_UPDATE,
)
from fides.api.ops.api.v1.urn_registry import V1_URL_PREFIX
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.oauth_util import (
    get_current_user,
    oauth2_scheme,
    verify_oauth_client,
)
from fides.core.config import CONFIG
from fides.lib.cryptography.cryptographic_util import b64_str_to_str
from fides.lib.cryptography.schemas.jwt import JWE_PAYLOAD_CLIENT_ID
from fides.lib.exceptions import AuthenticationError
from fides.lib.models.client import ClientDetail
from fides.lib.models.fides_user import FidesUser
from fides.lib.oauth.oauth_util import extract_payload
from fides.lib.oauth.schemas.user import (
    UserForcePasswordReset,
    UserPasswordReset,
    UserResponse,
    UserUpdate,
)

router = APIRouter(tags=["Users"], prefix=V1_URL_PREFIX)


def get_system_by_fides_key(db: Session, system_key: FidesKey) -> System:
    """Load a system by FidesKey or throw a 404"""
    system = System.get_by(db, field="fides_key", value=system_key)

    if not system:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No system found with fides_key {system_key}.",
        )
    return system


def _validate_current_user(user_id: str, user_from_token: FidesUser) -> None:
    if not user_from_token:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} does not exist.",
        )

    if user_id != user_from_token.id:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="You are only authorised to update your own user data.",
        )


@router.put(
    urls.USER_DETAIL,
    dependencies=[Security(verify_oauth_client, scopes=[USER_UPDATE])],
    status_code=HTTP_200_OK,
    response_model=UserResponse,
)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: str,
    data: UserUpdate,
) -> FidesUser:
    """
    Update a user given a `user_id`. By default this is limited to users
    updating their own data.
    """
    user = FidesUser.get(db=db, object_id=user_id)
    if not user:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"User with id {user_id} not found."
        )

    user.update(db=db, data=data.dict())
    logger.info("Updated user with id: '{}'.", user.id)
    return user


@router.post(
    urls.USER_PASSWORD_RESET,
    dependencies=[Security(verify_oauth_client)],
    status_code=HTTP_200_OK,
    response_model=UserResponse,
)
def update_user_password(
    *,
    db: Session = Depends(deps.get_db),
    current_user: FidesUser = Depends(get_current_user),
    user_id: str,
    data: UserPasswordReset,
) -> FidesUser:
    """
    Update a user's password given a `user_id`. By default this is limited to users
    updating their own data.
    """
    _validate_current_user(user_id, current_user)

    if not current_user.credentials_valid(
        b64_str_to_str(data.old_password), CONFIG.security.encoding
    ):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect password."
        )

    current_user.update_password(db=db, new_password=b64_str_to_str(data.new_password))

    logger.info("Updated user with id: '{}'.", current_user.id)
    return current_user


@router.post(
    urls.USER_FORCE_PASSWORD_RESET,
    dependencies=[Security(verify_oauth_client, scopes=[USER_PASSWORD_RESET])],
    status_code=HTTP_200_OK,
    response_model=UserResponse,
)
def force_update_password(
    *,
    db: Session = Depends(deps.get_db),
    user_id: str,
    data: UserForcePasswordReset,
) -> FidesUser:
    """
    Update any user's password given a `user_id` without needing to know the user's
    previous password.
    """
    user: Optional[FidesUser] = FidesUser.get(db=db, object_id=user_id)
    if not user:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} does not exist.",
        )

    user.update_password(db=db, new_password=b64_str_to_str(data.new_password))
    logger.info("Updated user with id: '{}'.", user.id)
    return user


def logout_oauth_client(
    authorization: str = Security(oauth2_scheme), db: Session = Depends(get_db)
) -> Optional[ClientDetail]:
    """
    Streamlined oauth checks for logout.  Only raises an error if no authorization is supplied.
    Otherwise, regardless if the token is malformed or expired, still return a 204.
    Returns a client if we can extract one from the token.
    """
    if authorization is None:
        raise AuthenticationError(detail="Authentication Failure")

    try:
        token_data = json.loads(
            extract_payload(authorization, CONFIG.security.app_encryption_key)
        )
    except jose.exceptions.JWEParseError:
        return None

    client_id = token_data.get(JWE_PAYLOAD_CLIENT_ID)
    if (
        not client_id or client_id == CONFIG.security.oauth_root_client_id
    ):  # The root client is not a persisted object
        return None

    client = ClientDetail.get(
        db, object_id=client_id, config=CONFIG, scopes=SCOPE_REGISTRY
    )

    return client


@router.post(
    urls.LOGOUT,
    status_code=HTTP_204_NO_CONTENT,
)
def user_logout(
    *,
    client: Optional[ClientDetail] = Security(
        logout_oauth_client,
    ),
    db: Session = Depends(deps.get_db),
) -> None:
    """Logout the user by deleting its client where applicable"""

    logger.info("Logging out user.")
    if client:
        client.delete(db)


@router.put(
    urls.SYSTEM_MANAGER,
    dependencies=[Security(verify_oauth_client, scopes=[SYSTEM_MANAGER_UPDATE])],
    response_model=List[SystemSchema],
)
def update_managed_systems(
    *,
    db: Session = Depends(deps.get_db),
    user_id: str,
    systems: List[FidesKey],
) -> List[SystemSchema]:
    """
    Endpoint to override the systems for which a user is "system manager".
    All systems the user manages are replaced with those in the request body.
    """
    user = validate_user_id(db, user_id)

    if len(set(systems)) != len(systems):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Cannot add user {user_id} as system manager. Duplicate systems in request body.",
        )

    retrieved_systems: Query = db.query(System).filter(System.fides_key.in_(systems))
    if retrieved_systems.count() != len(systems):
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Cannot add user {user_id} as system manager. System(s) not found.",
        )

    logger.info("Updating systems for which user {} is system manager", user_id)

    # Adding new systems for which the user is not already a manager
    for system in retrieved_systems:
        if user not in system.users:
            user.set_as_system_manager(db, system)

    # Removing systems for which the user in no longer a manager
    for system in user.systems:
        if system not in retrieved_systems:
            user.remove_as_system_manager(db, system)

    return user.systems


@router.get(
    urls.SYSTEM_MANAGER,
    response_model=List[SystemSchema],
)
async def get_managed_systems(
    *,
    db: Session = Depends(deps.get_db),
    authorization: str = Security(oauth2_scheme),
    current_user: FidesUser = Depends(get_current_user),
    user_id: str,
) -> List[SystemSchema]:
    """
    Endpoint to retrieve all the systems for which a user is "system manager".
    """
    # A user is able to retrieve their own systems
    if current_user and current_user.id == user_id:
        logger.info(
            "Retrieving current user's {} systems for which they are system manager",
            user_id,
        )
        return current_user.systems

    # User must have a specific scope to be able to read another user's systems
    user = validate_user_id(db, user_id)
    await verify_oauth_client(
        security_scopes=Security(verify_oauth_client, scopes=[SYSTEM_MANAGER_READ]),
        authorization=authorization,
        db=db,
    )
    logger.info("Getting systems for which user {} is system manager", user_id)
    return user.systems


@router.get(
    urls.SYSTEM_MANAGER_DETAIL,
    response_model=SystemSchema,
)
async def get_managed_system_details(
    *,
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(deps.get_db),
    user_id: str,
    system_key: FidesKey,
    current_user: FidesUser = Depends(get_current_user),
) -> SystemSchema:
    """
    Endpoint to retrieve a single system managed by the given user.
    """
    system: System = get_system_by_fides_key(db, system_key)

    if current_user and current_user.id == user_id:
        user = current_user
    else:
        await verify_oauth_client(
            security_scopes=Security(verify_oauth_client, scopes=[SYSTEM_MANAGER_READ]),
            authorization=authorization,
            db=db,
        )
        user = validate_user_id(db, user_id)

    if not system in user.systems:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"User {user_id} is not a manager of system {system.fides_key}",
        )

    logger.info(
        "Getting system {} for which user {} is system manager",
        system.fides_key,
        user_id,
    )

    return system


@router.delete(
    urls.SYSTEM_MANAGER_DETAIL,
    dependencies=[Security(verify_oauth_client, scopes=[SYSTEM_MANAGER_DELETE])],
    status_code=HTTP_204_NO_CONTENT,
)
def remove_user_as_system_manager(
    *, db: Session = Depends(deps.get_db), user_id: str, system_key: FidesKey
) -> None:
    """
    Endpoint to remove user as system manager from the given system
    """
    user = validate_user_id(db, user_id)
    system: System = get_system_by_fides_key(db, system_key)

    if not system in user.systems:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Cannot delete user as system manager. User {user_id} is not a manager of system {system.fides_key}.",
        )

    user.remove_as_system_manager(db, system)
    logger.info("Removed user {} as system manager of {}", user_id, system.fides_key)
