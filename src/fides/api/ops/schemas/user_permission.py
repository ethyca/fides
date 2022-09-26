from typing import List

from fastapi import HTTPException
from fideslib.oauth.schemas.user_permission import (
    UserPermissionsCreate as UserPermissionsCreateLib,
)
from fideslib.oauth.schemas.user_permission import (
    UserPermissionsEdit as UserPermissionsEditLib,
)
from fideslib.oauth.schemas.user_permission import (
    UserPermissionsResponse as UserPermissionsResponseLib,
)
from pydantic import validator
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from fidesops.ops.api.v1.scope_registry import SCOPE_REGISTRY


class UserPermissionsCreate(UserPermissionsCreateLib):
    """Data required to create a FidesUserPermissions record"""

    @validator("scopes")
    @classmethod
    def validate_scopes(cls, scopes: List[str]) -> List[str]:
        """Validates that all incoming scopes are valid"""
        diff = set(scopes).difference(set(SCOPE_REGISTRY))
        if len(diff) > 0:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid Scope(s) {diff}. Scopes must be one of {SCOPE_REGISTRY}.",
            )
        return scopes


class UserPermissionsEdit(UserPermissionsEditLib):
    """Data required to edit a FidesUserPermissions record"""


class UserPermissionsResponse(UserPermissionsResponseLib):
    """Response after creating, editing, or retrieving a FidesUserPermissions record"""
