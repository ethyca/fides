"""Unit tests for fides.api.request_context."""

import pytest

from fides.api.request_context import (
    get_client_id,
    get_request_id,
    get_user_id,
    reset_request_context,
    set_client_id,
    set_request_id,
    set_user_id,
)


@pytest.fixture(autouse=True)
def clean_context():
    """Reset the request context before and after every test."""
    reset_request_context()
    yield
    reset_request_context()


class TestClientIdHelpers:
    def test_get_client_id_default_is_none(self):
        assert get_client_id() is None

    def test_set_and_get_client_id(self):
        set_client_id("client_abc")
        assert get_client_id() == "client_abc"

    def test_set_client_id_does_not_clobber_user_id(self):
        set_user_id("user_xyz")
        set_client_id("client_abc")
        assert get_user_id() == "user_xyz"
        assert get_client_id() == "client_abc"

    def test_set_user_id_does_not_clobber_client_id(self):
        set_client_id("client_abc")
        set_user_id("user_xyz")
        assert get_client_id() == "client_abc"
        assert get_user_id() == "user_xyz"

    def test_set_client_id_does_not_clobber_request_id(self):
        set_request_id("req_123")
        set_client_id("client_abc")
        assert get_request_id() == "req_123"
        assert get_client_id() == "client_abc"

    def test_reset_clears_client_id(self):
        set_client_id("client_abc")
        reset_request_context()
        assert get_client_id() is None

    def test_reset_clears_all_fields(self):
        set_user_id("user_xyz")
        set_client_id("client_abc")
        set_request_id("req_123")
        reset_request_context()
        assert get_user_id() is None
        assert get_client_id() is None
        assert get_request_id() is None

    def test_overwrite_client_id(self):
        set_client_id("client_first")
        set_client_id("client_second")
        assert get_client_id() == "client_second"
