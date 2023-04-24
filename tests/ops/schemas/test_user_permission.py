import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from fides.api.ops.api.v1.scope_registry import USER_DELETE, USER_PERMISSION_CREATE
from fides.api.ops.oauth.roles import OWNER
from fides.api.ops.schemas.user_permission import UserPermissionsCreate


class TestUserPermissionsCreate:
    def test_role_validation(self):
        permissions = UserPermissionsCreate(roles=[OWNER])
        assert permissions.roles == [OWNER]

    def test_catch_invalid_roles(self):
        invalid_roles = ["bad_role"]
        with pytest.raises(ValidationError) as exc:
            UserPermissionsCreate(roles=invalid_roles)

        assert len(exc.value.errors()) == 1
