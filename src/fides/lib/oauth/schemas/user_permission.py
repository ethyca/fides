from typing import List

from fideslib.schemas.base_class import BaseSchema


class UserPermissionsCreate(BaseSchema):
    """Data required to create a FidessUserPermissions record."""

    scopes: List[str]


class UserPermissionsEdit(UserPermissionsCreate):
    """Data required to edit a FidesUserPermissions record."""

    id: str


class UserPermissionsResponse(UserPermissionsCreate):
    """Response after creating, editing, or retrieving a FidesUserPermissions record."""

    id: str
    user_id: str
