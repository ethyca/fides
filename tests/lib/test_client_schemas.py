import pytest
from pydantic import ValidationError

from fides.api.schemas.client import (
    ClientCreateRequest,
    ClientResponse,
    ClientSecretRotateResponse,
    ClientUpdateRequest,
)
from fides.common.scope_registry import CLIENT_READ, PRIVACY_REQUEST_READ


class TestClientCreateRequest:
    def test_name_is_optional(self):
        # name is optional at the API level; the UI form enforces it
        req = ClientCreateRequest(scopes=[CLIENT_READ])
        assert req.name is None

    def test_scopes_default_to_empty(self):
        req = ClientCreateRequest(name="My Client")
        assert req.scopes == []

    def test_description_is_optional(self):
        req = ClientCreateRequest(name="My Client")
        assert req.description is None

    def test_valid_full_request(self):
        req = ClientCreateRequest(
            name="My Client",
            description="Used for DSR automation",
            scopes=[CLIENT_READ, PRIVACY_REQUEST_READ],
        )
        assert req.name == "My Client"
        assert req.description == "Used for DSR automation"
        assert CLIENT_READ in req.scopes

    def test_name_cannot_be_empty_string(self):
        with pytest.raises(ValidationError):
            ClientCreateRequest(name="")


class TestClientUpdateRequest:
    def test_all_fields_optional(self):
        # Should not raise — partial updates are valid
        req = ClientUpdateRequest()
        assert req.name is None
        assert req.description is None
        assert req.scopes is None

    def test_can_update_name_only(self):
        req = ClientUpdateRequest(name="New Name")
        assert req.name == "New Name"
        assert req.scopes is None

    def test_can_update_scopes_only(self):
        req = ClientUpdateRequest(scopes=[CLIENT_READ])
        assert req.scopes == [CLIENT_READ]
        assert req.name is None

    def test_can_clear_description(self):
        req = ClientUpdateRequest(description=None)
        assert req.description is None


class TestClientResponse:
    def test_valid_response(self):
        resp = ClientResponse(
            client_id="mock_client_id",
            name="My Client",
            description="A description",
            scopes=[CLIENT_READ],
        )
        assert resp.client_id == "mock_client_id"
        assert resp.name == "My Client"
        assert resp.scopes == [CLIENT_READ]

    def test_name_and_description_can_be_none(self):
        resp = ClientResponse(client_id="mock_client_id", scopes=[])
        assert resp.name is None
        assert resp.description is None

    def test_no_secret_field(self):
        # ClientResponse must never expose a client_secret
        resp = ClientResponse(client_id="mock_client_id", scopes=[])
        assert not hasattr(resp, "client_secret")


class TestClientSecretRotateResponse:
    def test_valid_response(self):
        resp = ClientSecretRotateResponse(
            client_id="mock_client_id", client_secret="mock_client_secret"
        )
        assert resp.client_id == "mock_client_id"
        assert resp.client_secret == "mock_client_secret"
