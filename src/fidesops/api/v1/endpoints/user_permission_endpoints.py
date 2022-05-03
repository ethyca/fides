import logging
from fastapi import Security, Depends, APIRouter, HTTPException
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from fidesops.api import deps
from fidesops.api.v1 import urn_registry as urls
from fidesops.api.v1.urn_registry import V1_URL_PREFIX
from fidesops.models.fidesops_user import FidesopsUser
from fidesops.models.fidesops_user_permissions import FidesopsUserPermissions
from fidesops.schemas.oauth import AccessToken
from fidesops.util.oauth_util import verify_oauth_client
from sqlalchemy.orm import Session
from fidesops.api.v1.scope_registry import (
    USER_PERMISSION_CREATE,
    USER_PERMISSION_UPDATE,
    USER_PERMISSION_READ,
)
from fidesops.schemas.user_permission import (
    UserPermissionsResponse,
    UserPermissionsCreate,
    UserPermissionsEdit,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["User Permissions"], prefix=V1_URL_PREFIX)


def validate_user_id(db: Session, user_id: str) -> FidesopsUser:
    user = FidesopsUser.get_by(db, field="id", value=user_id)

    if not user:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"No user found with id {user_id}."
        )
    return user


@router.post(
    urls.USER_PERMISSIONS,
    dependencies=[Security(verify_oauth_client, scopes=[USER_PERMISSION_CREATE])],
    status_code=HTTP_201_CREATED,
    response_model=UserPermissionsResponse,
)
def create_user_permissions(
    *,
    db: Session = Depends(deps.get_db),
    user_id: str,
    permissions: UserPermissionsCreate,
) -> FidesopsUserPermissions:
    user = validate_user_id(db, user_id)
    if user.permissions is not None:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"This user already has permissions set.",
        )
    logger.info("Created FidesopsUserPermission record")
    return FidesopsUserPermissions.create(
        db=db, data={"user_id": user_id, **permissions.dict()}
    )


@router.put(
    urls.USER_PERMISSIONS,
    dependencies=[Security(verify_oauth_client, scopes=[USER_PERMISSION_UPDATE])],
    response_model=UserPermissionsResponse,
)
def update_user_permissions(
    *,
    db: Session = Depends(deps.get_db),
    user_id: str,
    permissions: UserPermissionsEdit,
) -> FidesopsUserPermissions:
    user = validate_user_id(db, user_id)
    logger.info("Updated FidesopsUserPermission record")
    if user.client:
        user.client.update(db=db, data={"scopes": permissions.scopes})
    return FidesopsUserPermissions.create_or_update(
        db=db,
        data={"id": user.permissions.id, "user_id": user_id, **permissions.dict()},
    )


@router.get(
    urls.USER_PERMISSIONS,
    dependencies=[Security(verify_oauth_client, scopes=[USER_PERMISSION_READ])],
    response_model=UserPermissionsResponse,
)
def get_user_permissions(
    *, db: Session = Depends(deps.get_db), user_id: str
) -> FidesopsUserPermissions:
    validate_user_id(db, user_id)
    logger.info("Retrieved FidesopsUserPermission record")
    return FidesopsUserPermissions.get_by(db, field="user_id", value=user_id)
