from typing import List, Optional

from pydantic import validator

from fides.api.oauth.roles import RoleRegistryEnum
from fides.api.schemas.base_class import FidesSchema
from fides.common.api.scope_registry import SCOPE_REGISTRY, ScopeRegistryEnum


class UserPermissionsCreate(FidesSchema):
    """Data required to create a FidesUserPermissions record

    Users will be assigned role(s) directly which are associated with a list of scopes. Scopes
    cannot be assigned directly to users.
    """

    roles: List[RoleRegistryEnum]

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
    total_scopes: List[
        ScopeRegistryEnum
    ]  # Returns a list of scopes inherited via roles

    class Config:
        use_enum_values = True

    @validator("total_scopes", pre=True)
    def validate_obsolete_total_scopes(
        cls, total_scopes: List[ScopeRegistryEnum]
    ) -> List[ScopeRegistryEnum]:
        """Filter out obsolete total scopes if the scope registry has changed"""
        return [scope for scope in total_scopes or [] if scope in SCOPE_REGISTRY]
