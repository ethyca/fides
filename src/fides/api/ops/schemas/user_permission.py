from typing import List, Optional

from pydantic import validator

from fides.api.ops.api.v1.scope_registry import SCOPE_REGISTRY, ScopeRegistryEnum
from fides.api.ops.schemas.base_class import BaseSchema
from fides.lib.oauth.roles import RoleRegistryEnum


class UserPermissionsCreate(BaseSchema):
    """Data required to create a FidesUserPermissions record

    Users will generally be assigned role(s) directly which are associated with many scopes,
    but we also will continue to support the ability to be assigned specific individual scopes.
    """

    scopes: List[ScopeRegistryEnum] = []
    roles: List[RoleRegistryEnum] = []

    class Config:
        """So roles are strings when we add to the db"""

        use_enum_values = True


class UserPermissionsEdit(UserPermissionsCreate):
    """Data required to edit a FidesUserPermissions record."""

    id: Optional[
        str
    ]  # I don't think this should be in the request body, so making it optional.


class UserPermissionsResponse(UserPermissionsCreate):
    """Response after creating, editing, or retrieving a FidesUserPermissions record."""

    id: str
    user_id: str
    scopes: List[ScopeRegistryEnum]
    total_scopes: List[ScopeRegistryEnum]

    class Config:
        use_enum_values = True

    @validator("scopes", pre=True)
    def validate_obsolete_scopes(
        cls, scopes: List[ScopeRegistryEnum]
    ) -> List[ScopeRegistryEnum]:
        """Filter out obsolete scopes if the scope registry has changed"""
        return [scope for scope in scopes or [] if scope in SCOPE_REGISTRY]

    @validator("total_scopes", pre=True)
    def validate_obsolete_total_scopes(
        cls, total_scopes: List[ScopeRegistryEnum]
    ) -> List[ScopeRegistryEnum]:
        """Filter out obsolete total scopes if the scope registry has changed"""
        return [scope for scope in total_scopes or [] if scope in SCOPE_REGISTRY]
