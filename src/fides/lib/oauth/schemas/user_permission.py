from typing import List

from fides.lib.schemas.base_class import BaseSchema


class UserPermissionsCreate(BaseSchema):
    """Data required to create a FidesUserPermissions record.

    Users will generally be assigned role(s) directly which are associated with many scopes,
    but we also will continue to support the ability to be assigned specific individual scopes.
    """

    scopes: List[str] = []
    roles: List[str] = []


class UserPermissionsEdit(UserPermissionsCreate):
    """Data required to edit a FidesUserPermissions record."""

    id: str


class UserPermissionsResponse(UserPermissionsCreate):
    """Response after creating, editing, or retrieving a FidesUserPermissions record."""

    id: str
    user_id: str
