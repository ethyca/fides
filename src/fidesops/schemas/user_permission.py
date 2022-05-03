from typing import List
from pydantic import validator
from fastapi import HTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from fidesops.schemas.base_class import BaseSchema
from fidesops.api.v1.scope_registry import SCOPE_REGISTRY


class UserPermissionsCreate(BaseSchema):
    """Data required to create a FidesopsUserPermissions record"""

    scopes: List[str]

    @validator("scopes")
    def validate_scopes(cls, scopes: List[str]) -> List[str]:
        """Validates that all incoming scopes are valid"""
        diff = set(scopes).difference(set(SCOPE_REGISTRY))
        if len(diff) > 0:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid Scope(s) {diff}. Scopes must be one of {SCOPE_REGISTRY}.",
            )
        return scopes


class UserPermissionsEdit(UserPermissionsCreate):
    """Data required to edit a FidesopsUserPermissions record"""

    id: str


class UserPermissionsResponse(UserPermissionsCreate):
    """Response after creating, editing, or retrieving a FidesopsUserPermissions record"""

    id: str
    user_id: str
