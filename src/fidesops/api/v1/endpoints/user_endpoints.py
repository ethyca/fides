import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage


from datetime import datetime

from sqlalchemy.orm import Session
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

from fidesops.api import deps
from fidesops.api.v1 import urn_registry as urls
from fidesops.api.v1.urn_registry import V1_URL_PREFIX
from fidesops.models.client import ADMIN_UI_ROOT, ClientDetail
from fidesops.models.fidesops_user import FidesopsUser
from fidesops.models.fidesops_user_permissions import FidesopsUserPermissions
from fidesops.schemas.oauth import AccessToken
from fidesops.schemas.user import (
    UserCreate,
    UserCreateResponse,
    UserUpdate,
    UserLogin,
    UserPasswordReset,
    UserResponse,
)

from fidesops.util.oauth_util import (
    get_current_user,
    verify_oauth_client,
)

from fidesops.api.v1.scope_registry import (
    USER_CREATE,
    USER_UPDATE,
    PRIVACY_REQUEST_READ,
    USER_READ,
    USER_DELETE,
    USER_PASSWORD_RESET,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Users"], prefix=V1_URL_PREFIX)


def perform_login(db: Session, user: FidesopsUser) -> ClientDetail:
    """Performs a login by updating the FidesopsUser instance and
    creating and returning an associated ClientDetail."""

    client: ClientDetail = user.client
    if not client:
        logger.info("Creating client for login")
        client, _ = ClientDetail.create_client_and_secret(
            db, user.permissions.scopes, user_id=user.id
        )

    user.last_login_at = datetime.utcnow()
    user.save(db)

    return client


@router.post(
    urls.USERS,
    dependencies=[Security(verify_oauth_client, scopes=[USER_CREATE])],
    status_code=HTTP_201_CREATED,
    response_model=UserCreateResponse,
)
def create_user(
    *, db: Session = Depends(deps.get_db), user_data: UserCreate
) -> FidesopsUser:
    """Create a user given a username and password"""
    user = FidesopsUser.get_by(db, field="username", value=user_data.username)

    if user:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Username already exists."
        )

    user = FidesopsUser.create(db=db, data=user_data.dict())
    logger.info(f"Created user with id: '{user.id}'.")
    FidesopsUserPermissions.create(
        db=db, data={"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]}
    )
    return user


def _validate_current_user(user_id: str, user_from_token: FidesopsUser) -> None:
    if not user_from_token:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} does not exist.",
        )

    if user_id != user_from_token.id:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=f"You are only authorised to update your own user data.",
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
) -> FidesopsUser:
    """
    Update a user given a `user_id`. By default this is limited to users
    updating their own data.
    """
    user = FidesopsUser.get(db=db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"User with id {user_id} not found."
        )

    user.update(db=db, data=data.dict())
    logger.info(f"Updated user with id: '{user.id}'.")
    return user


@router.post(
    urls.USER_PASSWORD_RESET,
    dependencies=[Security(verify_oauth_client, scopes=[USER_PASSWORD_RESET])],
    status_code=HTTP_200_OK,
    response_model=UserResponse,
)
def update_user_password(
    *,
    db: Session = Depends(deps.get_db),
    current_user: FidesopsUser = Depends(get_current_user),
    user_id: str,
    data: UserPasswordReset,
) -> FidesopsUser:
    """
    Update a user's password given a `user_id`. By default this is limited to users
    updating their own data.
    """
    _validate_current_user(user_id, current_user)

    if not current_user.credentials_valid(data.old_password):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect password."
        )

    current_user.update_password(db=db, new_password=data.new_password)

    logger.info(f"Updated user with id: '{current_user.id}'.")
    return current_user


@router.get(
    urls.USERS,
    dependencies=[Security(verify_oauth_client, scopes=[USER_READ])],
    response_model=Page[UserResponse],
)
def get_users(
    *,
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
    username: Optional[str] = None,
) -> AbstractPage[FidesopsUser]:
    """Returns a paginated list of all users"""
    logger.info(f"Returned a paginated list of all users.")
    query = FidesopsUser.query(db)
    if username:
        query = query.filter(FidesopsUser.username.ilike(f"%{escape_like(username)}%"))

    return paginate(query.order_by(FidesopsUser.created_at.desc()), params=params)


@router.get(
    urls.USER_DETAIL,
    dependencies=[Security(verify_oauth_client, scopes=[USER_READ])],
    response_model=UserResponse,
)
def get_user(*, db: Session = Depends(deps.get_db), user_id: str) -> FidesopsUser:
    """Returns a User based on an Id"""
    logger.info(f"Returned a User based on Id")
    user = FidesopsUser.get_by(db, field="id", value=user_id)
    if user is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")

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
    db: Session = Depends(deps.get_db),
    user_id: str,
) -> None:
    """Deletes the User and associated ClientDetail if applicable"""
    user = FidesopsUser.get_by(db, field="id", value=user_id)

    if not user:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"No user found with id {user_id}."
        )

    if not (client.fides_key == ADMIN_UI_ROOT or client.user_id == user.id):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f"Users can only remove themselves, or be the Admin UI Root User.",
        )

    logger.info(f"Deleting user with id: '{user_id}'.")

    user.delete(db)


@router.post(
    urls.LOGIN,
    status_code=HTTP_200_OK,
    response_model=AccessToken,
)
def user_login(
    *, db: Session = Depends(deps.get_db), user_data: UserLogin
) -> AccessToken:
    """Login the user by creating a client if it doesn't exist, and have that client generate a token"""
    user: FidesopsUser = FidesopsUser.get_by(
        db, field="username", value=user_data.username
    )

    if not user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No user found.")

    if not user.credentials_valid(user_data.password):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Incorrect password."
        )

    client: ClientDetail = perform_login(db, user)

    logger.info("Creating login access token")
    access_code = client.create_access_code_jwe()
    return AccessToken(access_token=access_code)


@router.post(
    urls.LOGOUT,
    status_code=HTTP_204_NO_CONTENT,
)
def user_logout(
    *,
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[],
    ),
    db: Session = Depends(deps.get_db),
) -> None:
    """Logout the user by deleting its client"""

    logger.info("Logging out user.")
    client.delete(db)
