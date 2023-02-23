from typing import List, Optional, Set

from fastapi import HTTPException
from pydantic import validator
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from fides.api.ops.api.v1.scope_registry import SCOPE_REGISTRY
from fides.api.ops.schemas.base_class import BaseSchema
from fides.lib.oauth.roles import ROLE_REGISTRY


class UserPermissionsCreate(BaseSchema):
    """Data required to create a FidesUserPermissions record

    Users will generally be assigned role(s) directly which are associated with many scopes,
    but we also will continue to support the ability to be assigned specific individual scopes.
    """

    scopes: List[str] = []
    roles: List[str] = []

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

    @validator("roles")
    @classmethod
    def validate_roles(cls, roles: List[str]) -> List[str]:
        """Validates that all incoming roles are valid"""
        diff: Set = set(roles).difference(set(ROLE_REGISTRY))
        if len(diff) > 0:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid Role(s) {diff}. Roles must be one of {ROLE_REGISTRY}.",
            )
        return roles


class UserPermissionsEdit(UserPermissionsCreate):
    """Data required to edit a FidesUserPermissions record."""

    id: Optional[
        str
    ]  # I don't think this should be in the request body, so making it optional.


class UserPermissionsResponse(UserPermissionsCreate):
    """Response after creating, editing, or retrieving a FidesUserPermissions record."""

    id: str
    user_id: str
