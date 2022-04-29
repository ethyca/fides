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
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from fidesops.api import deps
from fidesops.api.v1 import urn_registry as urls
from fidesops.api.v1.urn_registry import V1_URL_PREFIX
from fidesops.models.client import ADMIN_UI_ROOT, ClientDetail
from fidesops.models.fidesops_user import FidesopsUser
from fidesops.schemas.oauth import AccessToken
from fidesops.schemas.user import (
    UserCreate,
    UserCreateResponse,
    UserLogin,
    UserResponse,
)

from fidesops.util.oauth_util import verify_oauth_client

from fidesops.api.v1.scope_registry import (
    USER_CREATE,
    USER_READ,
    USER_DELETE,
    SCOPE_REGISTRY,
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
            db, SCOPE_REGISTRY, user_id=user.id
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
    return user


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
