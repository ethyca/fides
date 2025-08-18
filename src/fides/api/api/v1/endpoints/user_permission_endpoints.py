from typing import List, Optional

from fastapi import Depends, HTTPException, Security
from fastapi.security import SecurityScopes
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from fides.api.api import deps
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.oauth.roles import APPROVER, OWNER, RoleRegistryEnum
from fides.api.oauth.utils import get_current_user, oauth2_scheme, verify_oauth_client
from fides.api.schemas.user_permission import (
    UserPermissionsCreate,
    UserPermissionsEdit,
    UserPermissionsResponse,
)
from fides.api.util.api_router import APIRouter
from fides.common.api.scope_registry import (
    USER_PERMISSION_ASSIGN_OWNERS,
    USER_PERMISSION_CREATE,
    USER_PERMISSION_READ,
    USER_PERMISSION_UPDATE,
)
from fides.common.api.v1 import urn_registry as urls
from fides.common.api.v1.urn_registry import V1_URL_PREFIX
from fides.config import CONFIG

router = APIRouter(tags=["User Permissions"], prefix=V1_URL_PREFIX)


def validate_user_id(db: Session, user_id: str) -> FidesUser:
    """Get the user by id, otherwise throw a 404"""
    user = FidesUser.get_by(db, field="id", value=user_id)

    if not user:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"No user found with id {user_id}."
        )
    return user


async def owner_role_permission_check(
    db: Session, roles: List[RoleRegistryEnum], authorization: str
) -> None:
    """Extra permissions check to assert that the token possesses the USER_PERMISSION_ASSIGN_OWNERS scope
    if attempting to make another user an owner.
    """
    if OWNER in roles:
        await verify_oauth_client(
            security_scopes=SecurityScopes([USER_PERMISSION_ASSIGN_OWNERS]),
            authorization=authorization,
            db=db,
        )


@router.post(
    urls.USER_PERMISSIONS,
    dependencies=[Security(verify_oauth_client, scopes=[USER_PERMISSION_CREATE])],
    status_code=HTTP_201_CREATED,
    response_model=UserPermissionsResponse,
)
async def create_user_permissions(
    *,
    db: Session = Depends(deps.get_db),
    user_id: str,
    authorization: str = Security(oauth2_scheme),
    permissions: UserPermissionsCreate,
) -> FidesUserPermissions:
    """Create user permissions with associated roles."""
    user = validate_user_id(db, user_id)
    if user.permissions is not None:  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="This user already has permissions set.",
        )

    await owner_role_permission_check(db, permissions.roles, authorization)
    if user.client:
        # Just in case - this shouldn't happen in practice.
        user.client.update(db=db, data=permissions.model_dump(mode="json"))
    logger.info("Created FidesUserPermission record")
    return FidesUserPermissions.create(
        db=db, data={"user_id": user_id, **permissions.model_dump(mode="json")}
    )


@router.put(
    urls.USER_PERMISSIONS,
    dependencies=[Security(verify_oauth_client, scopes=[USER_PERMISSION_UPDATE])],
    response_model=UserPermissionsResponse,
)
async def update_user_permissions(
    *,
    db: Session = Depends(deps.get_db),
    user_id: str,
    authorization: str = Security(oauth2_scheme),
    permissions: UserPermissionsEdit,
) -> FidesUserPermissions:
    """Update a user's role(s).  The UI assigns one role at a time, but multiple
    roles are technically supported.

    Users inherit numerous scopes that are associated with their role(s).
    """
    user = validate_user_id(db, user_id)
    logger.info("Updated FidesUserPermission record")

    await owner_role_permission_check(db, permissions.roles, authorization)

    if user.client:
        user.client.update(db=db, data={"roles": permissions.roles})

    updated_user_perms = user.permissions.update(  # type: ignore[attr-defined]
        db=db,
        data={"id": user.permissions.id, "user_id": user_id, "roles": permissions.roles},  # type: ignore[attr-defined]
    )

    if user.systems and APPROVER in user.permissions.roles:  # type: ignore[attr-defined]
        for system in user.systems.copy():
            logger.info(
                "Approvers cannot be system managers. Removing user {} as system manager of {}.",
                user.id,
                system.fides_key,
            )
            user.remove_as_system_manager(db, system)

    return updated_user_perms


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
    if current_user and current_user.id == user_id:
        # The root user is a special case because they aren't persisted in the database.
        if current_user.id == CONFIG.security.oauth_root_client_id:
            logger.info("Created FidesUserPermission for root user")
            return FidesUserPermissions(
                id=CONFIG.security.oauth_root_client_id,
                user_id=CONFIG.security.oauth_root_client_id,
                roles=CONFIG.security.root_user_roles,
            )

        logger.debug("Retrieved FidesUserPermission record for current user")
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
