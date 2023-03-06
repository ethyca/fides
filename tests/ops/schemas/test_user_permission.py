import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from fides.api.ops.api.v1.scope_registry import USER_DELETE, USER_PERMISSION_CREATE
from fides.api.ops.schemas.user_permission import UserPermissionsCreate


class TestUserPermissionsCreate:
    def test_scope_validation(self):
        valid_scopes = [USER_DELETE, USER_PERMISSION_CREATE]
        permissions = UserPermissionsCreate(scopes=valid_scopes)
        assert permissions.scopes == valid_scopes

    def test_catch_invalid_scopes(self):
        invalid_scopes = ["not a real scope", "invalid scope here"]
        with pytest.raises(ValidationError) as exc:
            UserPermissionsCreate(scopes=invalid_scopes)

        assert len(exc.value.errors()) == 2
