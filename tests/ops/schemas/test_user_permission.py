import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from fides.api.oauth.roles import OWNER
from fides.api.schemas.user_permission import UserPermissionsCreate
from fides.common.api.scope_registry import USER_DELETE, USER_PERMISSION_CREATE


class TestUserPermissionsCreate:
    def test_role_validation(self):
        permissions = UserPermissionsCreate(roles=[OWNER])
        assert permissions.roles == [OWNER]

    def test_catch_invalid_roles(self):
        invalid_roles = ["bad_role"]
        with pytest.raises(ValidationError) as exc:
            UserPermissionsCreate(roles=invalid_roles)

        assert len(exc.value.errors()) == 1
