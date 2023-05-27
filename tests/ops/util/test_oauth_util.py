import pytest

from fides.api.common_exceptions import AuthorizationError
from fides.api.oauth.utils import get_root_client


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
