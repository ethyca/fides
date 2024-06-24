import json
from datetime import datetime
from typing import List, Optional

import jose.exceptions
from fastapi import Depends, HTTPException, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from fideslang.models import System as SystemSchema
from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.orm import Query, Session
from sqlalchemy_utils import escape_like
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from fides.api.api import deps
from fides.api.api.deps import get_db
from fides.api.api.v1.endpoints.user_permission_endpoints import validate_user_id
from fides.api.common_exceptions import AuthenticationError, AuthorizationError
from fides.api.cryptography.cryptographic_util import b64_str_to_str
from fides.api.cryptography.schemas.jwt import JWE_PAYLOAD_CLIENT_ID
from fides.api.models.client import ClientDetail
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.sql_models import System  # type: ignore[attr-defined]
from fides.api.oauth.roles import APPROVER, VIEWER
from fides.api.oauth.utils import (
    extract_payload,
    get_current_user,
    oauth2_scheme,
    verify_oauth_client,
)
from fides.api.schemas.oauth import AccessToken
from fides.api.schemas.user import (
    UserCreate,
    UserCreateResponse,
    UserForcePasswordReset,
    UserLogin,
    UserLoginResponse,
    UserPasswordReset,
    UserResponse,
    UserUpdate,
)
from fides.api.util.api_router import APIRouter
from fides.common.api.scope_registry import (
    SCOPE_REGISTRY,
    SYSTEM_MANAGER_DELETE,
    SYSTEM_MANAGER_READ,
    SYSTEM_MANAGER_UPDATE,
    USER_CREATE,
    USER_DELETE,
    USER_PASSWORD_RESET,
    USER_READ,
    USER_UPDATE,
)
from fides.common.api.v1 import urn_registry as urls
from fides.common.api.v1.urn_registry import V1_URL_PREFIX
from fides.config import CONFIG, FidesConfig, get_config

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
    dependencies=[Security(verify_oauth_client)],
    status_code=HTTP_200_OK,
    response_model=UserResponse,
)
async def update_user(
    *,
    db: Session = Depends(deps.get_db),
    authorization: str = Security(oauth2_scheme),
    current_user: FidesUser = Depends(get_current_user),
    user_id: str,
    data: UserUpdate,
) -> FidesUser:
    """
    Update a user given a `user_id`. If the user is not updating their own data,
    they need the USER_UPDATE scope
    """
    user = FidesUser.get(db=db, object_id=user_id)
    if not user:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"User with id {user_id} not found."
        )

    is_this_user = user.id == current_user.id
    if not is_this_user:
        await verify_oauth_client(
            security_scopes=Security(verify_oauth_client, scopes=[USER_UPDATE]),
            authorization=authorization,
            db=db,
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

    if not (user.permissions and user.permissions.roles):  # type: ignore
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"User {user_id} needs permissions before they can be assigned as system manager.",
        )

    if APPROVER in user.permissions.roles:  # type: ignore
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"User {user_id} is an {APPROVER} and cannot be assigned as a system manager.",
        )

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
        if user not in system.data_stewards:
            user.set_as_system_manager(db, system)

    # Removing systems for which the user in no longer a manager
    for system in user.systems.copy():
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


@router.post(
    urls.USERS,
    dependencies=[Security(verify_oauth_client, scopes=[USER_CREATE])],
    status_code=HTTP_201_CREATED,
    response_model=UserCreateResponse,
)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_data: UserCreate,
    config: FidesConfig = Depends(get_config),
) -> FidesUser:
    """
    Create a user given a username and password.
    If `password` is sent as a base64 encoded string, it will automatically be decoded
    server-side before being encrypted and persisted.
    If `password` is sent as a plaintext string, it will be encrypted and persisted as is.

    The user is given no roles by default.
    """

    # The root user is not stored in the database so make sure here that the user name
    # is not the same as the root user name.
    if (
        config.security.root_username
        and config.security.root_username == user_data.username
    ):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Username already exists."
        )

    user = FidesUser.get_by(db, field="username", value=user_data.username)

    if user:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Username already exists."
        )

    user = FidesUser.create(db=db, data=user_data.dict())
    logger.info("Created user with id: '{}'.", user.id)
    FidesUserPermissions.create(
        db=db,
        data={"user_id": user.id, "roles": [VIEWER]},
    )
    return user


@router.delete(
    urls.USER_DETAIL,
    status_code=HTTP_204_NO_CONTENT,
    dependencies=[Security(verify_oauth_client, scopes=[USER_DELETE])],
)
def delete_user(
    *,
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[USER_DELETE],
    ),
    db: Session = Depends(get_db),
    user_id: str,
) -> None:
    """Deletes the User and associated ClientDetail if applicable."""
    user = FidesUser.get_by(db, field="id", value=user_id)

    if not user:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"No user found with id {user_id}."
        )

    logger.info("User with id {} deleted by user with id {}", user_id, client.user_id)

    user.delete(db)


@router.get(
    urls.USER_DETAIL,
    dependencies=[Security(verify_oauth_client, scopes=[USER_READ])],
    response_model=UserResponse,
)
def get_user(*, db: Session = Depends(get_db), user_id: str) -> FidesUser:
    """Returns a User based on an Id"""
    user: Optional[FidesUser] = FidesUser.get_by_key_or_id(db, data={"id": user_id})
    if user is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")

    logger.info("Returning user with id: '{}'.", user_id)
    return user


@router.get(
    urls.USERS,
    dependencies=[Security(verify_oauth_client, scopes=[USER_READ])],
    response_model=Page[UserResponse],
)
def get_users(
    *,
    db: Session = Depends(get_db),
    params: Params = Depends(),
    username: Optional[str] = None,
) -> AbstractPage[FidesUser]:
    """Returns a paginated list of all users"""
    query = FidesUser.query(db)
    if username:
        query = query.filter(FidesUser.username.ilike(f"%{escape_like(username)}%"))

    logger.info("Returning a paginated list of users.")

    return paginate(query.order_by(FidesUser.created_at.desc()), params=params)


@router.post(
    urls.LOGIN,
    status_code=HTTP_200_OK,
    response_model=UserLoginResponse,
)
def user_login(
    *,
    db: Session = Depends(get_db),
    config: FidesConfig = Depends(get_config),
    user_data: UserLogin,
) -> UserLoginResponse:
    """Login the user by creating a client if it doesn't exist, and have that client
    generate a token."""
    user: FidesUser
    client: ClientDetail
    if (
        config.security.root_username
        and config.security.root_password
        and config.security.root_username == user_data.username
        and config.security.root_password == user_data.password
    ):
        client_check = ClientDetail.get(
            db,
            object_id=config.security.oauth_root_client_id,
            config=config,
            scopes=config.security.root_user_scopes,
            roles=config.security.root_user_roles,
        )

        if not client_check:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="No root client found."
            )

        # We have already checked for None but mypy still complains. This prevents mypy
        # from complaining.
        client = client_check
        user = FidesUser(
            id=config.security.oauth_root_client_id,
            username=config.security.root_username,
            created_at=datetime.utcnow(),
        )

        logger.warning(
            "Root Username & Password were used to login! If unexpected, review security settings (FIDES__SECURITY__ROOT_USERNAME and FIDES__SECURITY__ROOT_PASSWORD)"
        )

    else:
        user_check: Optional[FidesUser] = FidesUser.get_by(
            db, field="username", value=user_data.username
        )

        invalid_user_error_msg = "Incorrect username or password."

        if not user_check:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail=invalid_user_error_msg
            )

        if not user_check.credentials_valid(user_data.password):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail=invalid_user_error_msg,
            )

        # We have already checked for None but mypy still complains. This prevents mypy
        # from complaining.
        user = user_check

        client = perform_login(
            db,
            config.security.oauth_client_id_length_bytes,
            config.security.oauth_client_secret_length_bytes,
            user,
        )

    logger.info("Creating login access token")
    access_code = client.create_access_code_jwe(config.security.app_encryption_key)
    return UserLoginResponse(
        user_data=user,
        token_data=AccessToken(access_token=access_code),
    )


def perform_login(
    db: Session,
    client_id_byte_length: int,
    client_secret_btye_length: int,
    user: FidesUser,
) -> ClientDetail:
    """Performs a login by updating the FidesUser instance and creating and returning
    an associated ClientDetail.
    """

    client = user.client
    if not client:
        logger.info("Creating client for login")
        client, _ = ClientDetail.create_client_and_secret(
            db,
            client_id_byte_length,
            client_secret_btye_length,
            scopes=[],  # type: ignore
            roles=user.permissions.roles,  # type: ignore
            systems=user.system_ids,  # type: ignore
            user_id=user.id,
        )
    else:
        # Refresh the client just in case - for example, scopes and roles were added via the db directly.
        client.roles = user.permissions.roles  # type: ignore
        client.systems = user.system_ids  # type: ignore
        client.save(db)

    if not user.permissions.roles and not user.systems:  # type: ignore
        logger.warning("User {} needs roles or systems to login.", user.id)
        raise AuthorizationError(detail="Not Authorized for this action")

    user.last_login_at = datetime.utcnow()
    user.save(db)

    return client
