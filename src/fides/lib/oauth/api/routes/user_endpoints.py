from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy_utils import escape_like
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from fides.api.ops.util.oauth_util import verify_oauth_client
from fides.core.config import FidesConfig, get_config
from fides.lib.models.client import ADMIN_UI_ROOT, ClientDetail
from fides.lib.models.fides_user import FidesUser
from fides.lib.models.fides_user_permissions import FidesUserPermissions
from fides.lib.oauth.api import urn_registry as urls
from fides.lib.oauth.api.deps import get_db
from fides.lib.oauth.schemas.oauth import AccessToken
from fides.lib.oauth.schemas.user import (
    UserCreate,
    UserCreateResponse,
    UserLogin,
    UserLoginResponse,
    UserResponse,
)
from fides.lib.oauth.scopes import (
    PRIVACY_REQUEST_READ,
    USER_CREATE,
    USER_DELETE,
    USER_READ,
)

router = APIRouter()


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
        db=db, data={"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]}
    )
    return user


@router.delete(
    urls.USER_DETAIL,
    status_code=HTTP_204_NO_CONTENT,
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

    if not (client.fides_key == ADMIN_UI_ROOT or client.user_id == user.id):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Users can only remove themselves, or be the Admin UI Root User.",
        )

    logger.info("Deleting user with id: '{}'.", user_id)

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
    else:
        user_check: Optional[FidesUser] = FidesUser.get_by(
            db, field="username", value=user_data.username
        )

        if not user_check:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No user found.")

        if not user_check.credentials_valid(user_data.password):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="Incorrect user name or password.",
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
            scopes=user.permissions.scopes,  # type: ignore
            user_id=user.id,
        )

    user.last_login_at = datetime.utcnow()
    user.save(db)

    return client
