import pytest
from fastapi import HTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from fidesops.schemas.user_permission import UserPermissionsCreate
from fidesops.api.v1.scope_registry import USER_PERMISSION_CREATE, USER_DELETE


class TestUserPermissionsCreate:
    def test_scope_validation(self):
        valid_scopes = [USER_DELETE, USER_PERMISSION_CREATE]
        permissions = UserPermissionsCreate(scopes=valid_scopes)
        assert permissions.scopes == valid_scopes

    def test_catch_invalid_scopes(self):
        invalid_scopes = ["not a real scope", "invalid scope here"]
        with pytest.raises(HTTPException) as exc:
            UserPermissionsCreate(scopes=invalid_scopes)

        assert exc.value.status_code == HTTP_422_UNPROCESSABLE_ENTITY
        assert invalid_scopes[0] in exc.value.detail
        assert invalid_scopes[1] in exc.value.detail
