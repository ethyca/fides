import logging
from fastapi import Security, Depends, APIRouter, HTTPException
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_403_FORBIDDEN,
)

from fidesops.api import deps
from fidesops.api.v1 import urn_registry as urls
from fidesops.api.v1.urn_registry import V1_URL_PREFIX
from fidesops.models.client import ClientDetail, ADMIN_UI_ROOT
from fidesops.models.fidesops_user import FidesopsUser
from fidesops.schemas.user import UserCreate, UserCreateResponse

from fidesops.util.oauth_util import verify_oauth_client
from sqlalchemy.orm import Session

from fidesops.api.v1.scope_registry import USER_CREATE, USER_DELETE

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Users"], prefix=V1_URL_PREFIX)


@router.post(
    urls.USERS,
    dependencies=[Security(verify_oauth_client, scopes=[USER_CREATE])],
    status_code=201,
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


@router.delete(
    urls.USER_DETAIL,
    status_code=204,
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
