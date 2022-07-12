import logging

from fastapi import Depends, HTTPException, Security
from fideslib.cryptography.cryptographic_util import b64_str_to_str
from fideslib.models.client import ClientDetail
from fideslib.models.fides_user import FidesUser
from fideslib.oauth.schemas.user import UserPasswordReset, UserResponse, UserUpdate
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from fidesops.api import deps
from fidesops.api.v1 import urn_registry as urls
from fidesops.api.v1.scope_registry import USER_PASSWORD_RESET, USER_UPDATE
from fidesops.api.v1.urn_registry import V1_URL_PREFIX
from fidesops.core.config import config
from fidesops.util.api_router import APIRouter
from fidesops.util.oauth_util import get_current_user, verify_oauth_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Users"], prefix=V1_URL_PREFIX)


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
        b64_str_to_str(data.old_password), config.security.ENCODING
    ):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect password."
        )

    current_user.update_password(db=db, new_password=b64_str_to_str(data.new_password))

    logger.info(f"Updated user with id: '{current_user.id}'.")
    return current_user


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
