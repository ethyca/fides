import pytest

from fides.api.common_exceptions import AuthorizationError
from fides.api.oauth.roles import OWNER, VIEWER
from fides.api.oauth.utils import get_root_client, roles_have_scopes
from fides.common.api.scope_registry import POLICY_READ, USER_CREATE, USER_READ


class TestGetRootClient:
    @pytest.mark.asyncio
    async def test_get_root_client_default(self, db) -> None:
        """Get the root client with default values. Expect success."""
        client = await get_root_client(db=db)
        assert client

    @pytest.mark.asyncio
    async def test_get_root_client_error(self, db) -> None:
        """Feed a bad client_id in and expect an AuthorizationError."""
        with pytest.raises(AuthorizationError):
            await get_root_client(db=db, client_id="badclientid")


class TestRolesHaveScopes:
    @pytest.mark.parametrize(
        "roles,required_scopes,expected",
        [
            # Owner role has broad permissions
            ([OWNER], {USER_READ}, True),
            ([OWNER], {USER_CREATE}, True),
            # Viewer role has read-only permissions
            ([VIEWER], {USER_READ}, True),
            ([VIEWER], {POLICY_READ}, True),
            ([VIEWER], {USER_CREATE}, False),
            # Multiple roles combine their scopes
            ([VIEWER, OWNER], {USER_CREATE}, True),
            # Empty roles have no scopes
            ([], {USER_READ}, False),
            # Empty required scopes is always satisfied
            ([VIEWER], set(), True),
            ([], set(), True),
        ],
        ids=[
            "owner_has_user_read",
            "owner_has_user_create",
            "viewer_has_user_read",
            "viewer_has_policy_read",
            "viewer_lacks_user_create",
            "combined_roles_have_user_create",
            "empty_roles_lack_scopes",
            "empty_required_scopes_with_role",
            "empty_required_scopes_without_role",
        ],
    )
    def test_roles_have_scopes(self, roles, required_scopes, expected):
        """Test that roles_have_scopes correctly checks if roles have required scopes."""
        assert roles_have_scopes(roles, required_scopes) == expected
