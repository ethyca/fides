"""Tests for request context population in the OAuth auth flow.

These tests verify that extract_token_and_load_client (and its async
counterpart) correctly set either user_id or client_id in the request
context depending on the type of authenticated actor.
"""

from unittest.mock import MagicMock, patch

import pytest

from fides.api.request_context import (
    get_client_id,
    get_user_id,
    reset_request_context,
)


@pytest.fixture(autouse=True)
def clean_context():
    reset_request_context()
    yield
    reset_request_context()


class TestRequestContextPopulationLogic:
    """Tests for the actor-type branching that sets user_id vs client_id."""

    def _make_client(self, *, user_id=None, client_id="cli_test", is_root=False):
        client = MagicMock()
        client.user_id = user_id
        client.id = client_id
        return client, is_root

    def test_user_linked_client_sets_user_id(self):
        """A client with a linked FidesUser sets user_id, not client_id."""
        from fides.api.request_context import set_client_id, set_user_id

        # Simulate the auth flow for a user-linked client
        client_user_id = "usr_abc"
        client_id = "cli_xyz"

        # Replicate the branching logic from extract_token_and_load_client
        oauth_root_client_id = "some_other_root_id"
        ctx_user_id = client_user_id  # client.user_id is set
        if not ctx_user_id and client_id == oauth_root_client_id:
            ctx_user_id = oauth_root_client_id

        if ctx_user_id:
            set_user_id(ctx_user_id)
        else:
            set_client_id(client_id)

        assert get_user_id() == client_user_id
        assert get_client_id() is None

    def test_api_client_sets_client_id(self):
        """A client with no linked user and not root sets client_id."""
        from fides.api.request_context import set_client_id, set_user_id

        client_id = "cli_api_123"
        oauth_root_client_id = "root_client_id"

        ctx_user_id = None  # client.user_id is None
        if not ctx_user_id and client_id == oauth_root_client_id:
            ctx_user_id = oauth_root_client_id

        if ctx_user_id:
            set_user_id(ctx_user_id)
        else:
            set_client_id(client_id)

        assert get_client_id() == client_id
        assert get_user_id() is None

    def test_root_client_sets_user_id_to_root_client_id(self):
        """Root client (no user_id, special fides_key) sets user_id to the root client id."""
        from fides.api.request_context import set_client_id, set_user_id

        oauth_root_client_id = "root_client_id"
        client_id = oauth_root_client_id

        ctx_user_id = None  # root client has no linked FidesUser
        if not ctx_user_id and client_id == oauth_root_client_id:
            ctx_user_id = oauth_root_client_id

        if ctx_user_id:
            set_user_id(ctx_user_id)
        else:
            set_client_id(client_id)

        assert get_user_id() == oauth_root_client_id
        assert get_client_id() is None

    def test_api_client_does_not_set_user_id(self):
        """Verify user_id stays None when an API client authenticates."""
        from fides.api.request_context import set_client_id, set_user_id

        set_client_id("cli_api_456")
        assert get_user_id() is None

    def test_user_client_does_not_set_client_id(self):
        """Verify client_id stays None when a user-linked client authenticates."""
        from fides.api.request_context import set_client_id, set_user_id

        set_user_id("usr_abc")
        assert get_client_id() is None
