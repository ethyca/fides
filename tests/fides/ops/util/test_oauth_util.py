from datetime import datetime, timezone

import pytest

from fides.api.common_exceptions import AuthorizationError
from fides.api.oauth.roles import OWNER, VIEWER
from fides.api.oauth.utils import (
    get_root_client,
    is_token_invalidated_offline,
    roles_have_scopes,
)
from fides.common.scope_registry import POLICY_READ, USER_CREATE, USER_READ


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


class TestIsTokenInvalidatedOffline:
    """Tests for stateless token invalidation checks using payload data only."""

    def test_is_token_invalidated_offline_no_reset(self):
        """Token valid when no password_reset_at in payload."""
        assert is_token_invalidated_offline(datetime.now(), None) is False

    def test_is_token_invalidated_offline_issued_after(self):
        """Token valid when issued after password reset."""
        reset_time = datetime(2024, 1, 1, 12, 0, 0)
        issued_time = datetime(2024, 1, 2, 12, 0, 0)  # After reset
        assert (
            is_token_invalidated_offline(issued_time, reset_time.isoformat()) is False
        )

    def test_is_token_invalidated_offline_issued_before(self):
        """Token invalid when issued before password reset."""
        reset_time = datetime(2024, 1, 2, 12, 0, 0)
        issued_time = datetime(2024, 1, 1, 12, 0, 0)  # Before reset
        assert is_token_invalidated_offline(issued_time, reset_time.isoformat()) is True

    def test_is_token_invalidated_offline_same_time(self):
        """Token valid when issued at exact same time as password reset."""
        same_time = datetime(2024, 1, 1, 12, 0, 0)
        # Not strictly before, so should be valid
        assert is_token_invalidated_offline(same_time, same_time.isoformat()) is False

    def test_is_token_invalidated_offline_invalid_format(self):
        """Graceful handling of invalid ISO format."""
        assert is_token_invalidated_offline(datetime.now(), "not-a-date") is False

    def test_is_token_invalidated_offline_empty_string(self):
        """Empty string treated as invalid format."""
        assert is_token_invalidated_offline(datetime.now(), "") is False

    def test_offline_check_insufficient_for_second_reset(self):
        """Offline check passes for tokens issued after the embedded reset.

        A second password reset (after the token was issued) can only be
        caught by the DB check — the embedded value is frozen at token
        creation time. This test documents the design boundary: the
        offline check alone is NOT sufficient for the fides server path.
        """
        first_reset = datetime(2024, 1, 1, 12, 0, 0)
        issued = datetime(2024, 1, 2, 12, 0, 0)  # After first reset
        # Offline check with first_reset embedded: issued > first_reset → valid
        assert is_token_invalidated_offline(issued, first_reset.isoformat()) is False
        # A second reset at 2024-01-03 would invalidate this token, but only
        # the DB check (is_token_invalidated) can catch it — the embedded
        # password-reset-at is still the first reset's timestamp.

    def test_timezone_aware_reset_with_naive_issued(self):
        """Timezone-aware password_reset_at compared to naive issued_at."""
        reset = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        issued = datetime(2024, 1, 1, 12, 0, 0)  # naive, before reset
        assert is_token_invalidated_offline(issued, reset.isoformat()) is True

    def test_naive_reset_with_timezone_aware_issued(self):
        """Naive password_reset_at compared to timezone-aware issued_at."""
        reset = datetime(2024, 1, 2, 12, 0, 0)  # naive
        issued = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert is_token_invalidated_offline(issued, reset.isoformat()) is True

    def test_both_timezone_aware(self):
        """Both timezone-aware datetimes compare correctly."""
        reset = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        issued = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert is_token_invalidated_offline(issued, reset.isoformat()) is True
