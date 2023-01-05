from typing import Optional

from fastapi import Depends, HTTPException, Security
from fastapi.security import SecurityScopes
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from fides.api.ops.api import deps
from fides.api.ops.api.v1 import urn_registry as urls
from fides.api.ops.api.v1.scope_registry import (
    SCOPE_REGISTRY,
    USER_PERMISSION_CREATE,
    USER_PERMISSION_READ,
    USER_PERMISSION_UPDATE,
)
from fides.api.ops.api.v1.urn_registry import V1_URL_PREFIX
from fides.api.ops.schemas.user_permission import (
    UserPermissionsCreate,
    UserPermissionsEdit,
    UserPermissionsResponse,
)
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.oauth_util import (
    get_current_user,
    oauth2_scheme,
    verify_oauth_client,
)
from fides.core.config import get_config
from fides.lib.models.fides_user import FidesUser
from fides.lib.models.fides_user_permissions import FidesUserPermissions

CONFIG = get_config()
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
    if user.permissions is not None:  # type: ignore[attr-defined]
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
    return user.permissions.update(  # type: ignore[attr-defined]
        db=db,
        data={"id": user.permissions.id, "user_id": user_id, **permissions.dict()},  # type: ignore[attr-defined]
    )


@router.get(
    urls.USER_PERMISSIONS,
    response_model=UserPermissionsResponse,
)
async def get_user_permissions(
    *,
    db: Session = Depends(deps.get_db),
    authorization: str = Security(oauth2_scheme),
    current_user: FidesUser = Depends(get_current_user),
    user_id: str,
) -> Optional[FidesUserPermissions]:
    # A user is able to retrieve their own permissions.
    if current_user.id == user_id:
        # The root user is a special case because they aren't persisted in the database.
        if current_user.id == CONFIG.security.oauth_root_client_id:
            logger.info("Created FidesUserPermission for root user")
            return FidesUserPermissions(
                id=CONFIG.security.oauth_root_client_id,
                user_id=CONFIG.security.oauth_root_client_id,
                scopes=SCOPE_REGISTRY,
            )

        logger.info("Retrieved FidesUserPermission record for current user")
        return FidesUserPermissions.get_by(db, field="user_id", value=current_user.id)

    # To look up the permissions of another user, that user must exist and the current user must
    # have permission to read users.
    validate_user_id(db, user_id)
    await verify_oauth_client(
        security_scopes=SecurityScopes([USER_PERMISSION_READ]),
        authorization=authorization,
        db=db,
    )

    logger.info("Retrieved FidesUserPermission record")
    return FidesUserPermissions.get_by(db, field="user_id", value=user_id)
