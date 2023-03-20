from typing import List, Optional

from pydantic import validator

from fides.api.ops.api.v1.scope_registry import SCOPE_REGISTRY, ScopeRegistryEnum
from fides.api.ops.schemas.base_class import BaseSchema
from fides.lib.oauth.roles import RoleRegistryEnum


class UserPermissionsCreate(BaseSchema):
    """Data required to create a FidesUserPermissions record

    Users will be assigned a role(s) directly which are associated with a list of scopes. Scopes
    cannot be assigned directly to users.
    """

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
    scopes: List[
        ScopeRegistryEnum
    ]  # This should be removed once the UI is not using.  Currently returning scopes inherited via roles here.
    total_scopes: List[ScopeRegistryEnum]  # Scopes inherited via roles

    class Config:
        use_enum_values = True

    @validator("scopes", pre=True)
    def validate_obsolete_scopes(
        cls, scopes: List[ScopeRegistryEnum]
    ) -> List[ScopeRegistryEnum]:
        """Filter out obsolete scopes if the scope registry has changed
        This is just for backwards-compatibility. Scopes will no longer be assigned directly.
        """
        return [scope for scope in scopes or [] if scope in SCOPE_REGISTRY]

    @validator("total_scopes", pre=True)
    def validate_obsolete_total_scopes(
        cls, total_scopes: List[ScopeRegistryEnum]
    ) -> List[ScopeRegistryEnum]:
        """Filter out obsolete total scopes if the scope registry has changed"""
        return [scope for scope in total_scopes or [] if scope in SCOPE_REGISTRY]
