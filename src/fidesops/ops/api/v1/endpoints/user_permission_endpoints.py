import logging

from fastapi import Depends, HTTPException, Security
from fideslib.models.fides_user import FidesUser
from fideslib.models.fides_user_permissions import FidesUserPermissions
from sqlalchemy.orm import Session
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from fidesops.ops.api import deps
from fidesops.ops.api.v1 import urn_registry as urls
from fidesops.ops.api.v1.scope_registry import (
    USER_PERMISSION_CREATE,
    USER_PERMISSION_READ,
    USER_PERMISSION_UPDATE,
)
from fidesops.ops.api.v1.urn_registry import V1_URL_PREFIX
from fidesops.ops.schemas.user_permission import (
    UserPermissionsCreate,
    UserPermissionsEdit,
    UserPermissionsResponse,
)
from fidesops.ops.util.api_router import APIRouter
from fidesops.ops.util.oauth_util import verify_oauth_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["User Permissions"], prefix=V1_URL_PREFIX)


def validate_user_id(db: Session, user_id: str) -> FidesUser:
    user = FidesUser.get_by(db, field="id", value=user_id)

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
) -> FidesUserPermissions:
    user = validate_user_id(db, user_id)
    if user.permissions is not None:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="This user already has permissions set.",
        )
    logger.info("Created FidesUserPermission record")
    return FidesUserPermissions.create(
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
) -> FidesUserPermissions:
    user = validate_user_id(db, user_id)
    logger.info("Updated FidesUserPermission record")
    if user.client:
        user.client.update(db=db, data={"scopes": permissions.scopes})
    return user.permissions.update(
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
) -> FidesUserPermissions:
    validate_user_id(db, user_id)
    logger.info("Retrieved FidesUserPermission record")
    return FidesUserPermissions.get_by(db, field="user_id", value=user_id)
