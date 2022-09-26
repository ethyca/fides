from fastapi import Depends, HTTPException, Security
from fideslib.cryptography.cryptographic_util import b64_str_to_str
from fideslib.models.client import ClientDetail
from fideslib.models.fides_user import FidesUser
from fideslib.oauth.api import urn_registry
from fideslib.oauth.schemas.user import UserPasswordReset, UserResponse, UserUpdate
from fideslib.oauth.scopes import USER_PASSWORD_RESET, USER_UPDATE
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from fidesctl.api.ctl.deps import get_current_user, get_db, verify_oauth_client
from fidesctl.api.ctl.routes.util import API_PREFIX
from fidesctl.api.ctl.utils.api_router import APIRouter
from fidesctl.ctl.core.config import FidesctlConfig, get_config

router = APIRouter(tags=["Users"], prefix=f"{API_PREFIX}")


def _validate_current_user(user_id: str, user_from_token: FidesUser) -> None:
    if not user_from_token:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} does not exist.",
        )

    if user_id != user_from_token.id:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="You are only authorised to update your own user data.",
        )


@router.put(
    urn_registry.USER_DETAIL,
    dependencies=[Security(verify_oauth_client, scopes=[USER_UPDATE])],
    status_code=HTTP_200_OK,
    response_model=UserResponse,
)
def update_user(
    *,
    db: Session = Depends(get_db),  # pylint: disable=invalid-name
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
            status_code=HTTP_404_NOT_FOUND, detail=f"user with id {user_id} not found."
        )

    user.update(db=db, data=data.dict())
    return user


@router.post(
    urn_registry.USER_PASSWORD_RESET,
    dependencies=[Security(verify_oauth_client, scopes=[USER_PASSWORD_RESET])],
    status_code=HTTP_200_OK,
    response_model=UserResponse,
)
def update_user_password(
    *,
    db: Session = Depends(get_db),  # pylint: disable=invalid-name
    current_user: FidesUser = Depends(get_current_user),
    user_id: str,
    data: UserPasswordReset,
    config: FidesctlConfig = Depends(get_config),
) -> FidesUser:
    """
    Update a user's password given a `user_id`. By default this is limited to users
    updating their own data.
    """
    _validate_current_user(user_id, current_user)

    if not current_user.credentials_valid(
        b64_str_to_str(data.old_password), config.security.encoding
    ):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect password."
        )

    current_user.update_password(db=db, new_password=b64_str_to_str(data.new_password))

    return current_user


@router.post(
    "/logout",
    status_code=HTTP_204_NO_CONTENT,
)
def user_logout(
    *,
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[],
    ),
    db: Session = Depends(get_db),  # pylint: disable=invalid-name
) -> None:
    """logout the user by deleting its client"""

    client.delete(db)
