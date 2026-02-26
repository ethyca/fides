"""Unit tests for EntraHttpClient.

Uses a mock requests.Session injected via the constructor so no real HTTP calls
are made.  Tests cover token acquisition, list_applications, and
list_service_principals — including pagination, custom $select, error handling,
and the max-page-size cap.
"""

import json
from unittest.mock import MagicMock

import pytest
import requests

from fides.api.common_exceptions import ConnectionException
from fides.api.service.connectors.entra_http_client import (
    APPLICATIONS_PAGE_SIZE,
    APPLICATIONS_SELECT,
    SERVICE_PRINCIPALS_PAGE_SIZE,
    SERVICE_PRINCIPALS_SELECT,
    EntraHttpClient,
)

TENANT_ID = "11111111-2222-3333-4444-555555555555"
CLIENT_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
CLIENT_SECRET = "test-client-secret"
FAKE_TOKEN = "fake-access-token"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(status_code: int, body: dict) -> MagicMock:
    """Return a mock response with .ok, .status_code, .json(), and .text."""
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.ok = status_code < 400
    resp.json.return_value = body
    resp.text = json.dumps(body)
    return resp


def _token_response() -> MagicMock:
    return _make_response(200, {"access_token": FAKE_TOKEN})


@pytest.fixture
def mock_session() -> MagicMock:
    return MagicMock(spec=requests.Session)


@pytest.fixture
def client(mock_session: MagicMock) -> EntraHttpClient:
    return EntraHttpClient(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        session=mock_session,
    )


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


class TestEntraHttpClientInit:
    def test_injected_session_used(self, client, mock_session):
        assert client._session is mock_session

    def test_tenant_id_stripped(self, mock_session):
        c = EntraHttpClient(
            tenant_id=f"  {TENANT_ID}  ",
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            session=mock_session,
        )
        assert c.tenant_id == TENANT_ID

    def test_token_url_contains_tenant(self, client):
        assert TENANT_ID in client._token_url()
        assert client._token_url().startswith("https://login.microsoftonline.com/")


# ---------------------------------------------------------------------------
# Token acquisition
# ---------------------------------------------------------------------------


class TestGetToken:
    def test_successful_token(self, client, mock_session):
        mock_session.post.return_value = _token_response()
        token = client._get_token()
        assert token == FAKE_TOKEN

    def test_token_cached_after_first_call(self, client, mock_session):
        mock_session.post.return_value = _token_response()
        client._get_token()
        client._get_token()
        assert mock_session.post.call_count == 1

    def test_failed_token_raises_connection_exception(self, client, mock_session):
        mock_session.post.return_value = _make_response(
            401, {"error": "invalid_client", "error_description": "Bad credentials"}
        )
        with pytest.raises(ConnectionException, match="Failed to obtain Entra access token"):
            client._get_token()

    def test_missing_access_token_in_response_raises(self, client, mock_session):
        mock_session.post.return_value = _make_response(200, {})
        with pytest.raises(ConnectionException, match="missing access_token"):
            client._get_token()

    def test_error_description_included_in_message(self, client, mock_session):
        mock_session.post.return_value = _make_response(
            401,
            {
                "error": "invalid_client",
                "error_description": "AADSTS70011: Invalid scope",
            },
        )
        with pytest.raises(ConnectionException, match="AADSTS70011"):
            client._get_token()


# ---------------------------------------------------------------------------
# list_applications
# ---------------------------------------------------------------------------


class TestListApplications:
    def _setup(self, mock_session, apps, next_link=None):
        """Prime mock_session with a token response then a list response."""
        mock_session.post.return_value = _token_response()
        mock_session.get.return_value = _make_response(
            200, {"value": apps, "@odata.nextLink": next_link}
        )

    def test_returns_apps_and_no_next_link(self, client, mock_session):
        self._setup(mock_session, [{"id": "app-1"}])
        apps, next_link = client.list_applications()
        assert apps == [{"id": "app-1"}]
        assert next_link is None

    def test_returns_next_link_when_present(self, client, mock_session):
        next_url = "https://graph.microsoft.com/v1.0/applications?$skiptoken=abc"
        self._setup(mock_session, [{"id": "app-1"}], next_link=next_url)
        _, next_link = client.list_applications()
        assert next_link == next_url

    def test_default_url_uses_applications_endpoint(self, client, mock_session):
        self._setup(mock_session, [])
        client.list_applications()
        url = mock_session.get.call_args[0][0]
        assert "/v1.0/applications" in url

    def test_default_select_in_url(self, client, mock_session):
        self._setup(mock_session, [])
        client.list_applications()
        url = mock_session.get.call_args[0][0]
        assert "$select=" in url
        assert "displayName" in url

    def test_custom_select_passed_through(self, client, mock_session):
        self._setup(mock_session, [])
        client.list_applications(select="id,appId")
        url = mock_session.get.call_args[0][0]
        assert "$select=id,appId" in url

    def test_top_capped_at_max_page_size(self, client, mock_session):
        self._setup(mock_session, [])
        client.list_applications(top=9999)
        url = mock_session.get.call_args[0][0]
        assert f"$top={APPLICATIONS_PAGE_SIZE}" in url

    def test_next_link_used_directly_without_rebuilding_url(self, client, mock_session):
        next_url = "https://graph.microsoft.com/v1.0/applications?$skiptoken=xyz"
        mock_session.post.return_value = _token_response()
        mock_session.get.return_value = _make_response(200, {"value": []})
        client.list_applications(next_link=next_url)
        called_url = mock_session.get.call_args[0][0]
        assert called_url == next_url

    def test_empty_value_returns_empty_list(self, client, mock_session):
        mock_session.post.return_value = _token_response()
        mock_session.get.return_value = _make_response(200, {})
        apps, _ = client.list_applications()
        assert apps == []

    def test_non_list_value_normalised_to_empty(self, client, mock_session):
        mock_session.post.return_value = _token_response()
        mock_session.get.return_value = _make_response(200, {"value": "bad"})
        apps, _ = client.list_applications()
        assert apps == []

    def test_401_clears_cached_token_and_raises(self, client, mock_session):
        mock_session.post.return_value = _token_response()
        client._token = FAKE_TOKEN
        mock_session.get.return_value = _make_response(401, {"error": "Unauthorized"})
        with pytest.raises(ConnectionException):
            client.list_applications()
        assert client._token is None

    def test_403_authorization_denied_friendly_message(self, client, mock_session):
        mock_session.post.return_value = _token_response()
        mock_session.get.return_value = _make_response(
            403,
            {"error": {"code": "Authorization_RequestDenied", "message": "Forbidden"}},
        )
        with pytest.raises(ConnectionException, match="Insufficient Microsoft Graph permissions"):
            client.list_applications()

    def test_403_other_error_generic_message(self, client, mock_session):
        mock_session.post.return_value = _token_response()
        mock_session.get.return_value = _make_response(
            403, {"error": {"code": "SomeOtherCode"}}
        )
        with pytest.raises(ConnectionException, match="Microsoft Graph request failed: 403"):
            client.list_applications()

    def test_500_raises_connection_exception(self, client, mock_session):
        mock_session.post.return_value = _token_response()
        mock_session.get.return_value = _make_response(500, {"error": "Server Error"})
        with pytest.raises(ConnectionException, match="500"):
            client.list_applications()

    def test_bearer_token_in_request_header(self, client, mock_session):
        self._setup(mock_session, [])
        client.list_applications()
        headers = mock_session.get.call_args[1]["headers"]
        assert headers["Authorization"] == f"Bearer {FAKE_TOKEN}"


# ---------------------------------------------------------------------------
# list_service_principals
# ---------------------------------------------------------------------------


class TestListServicePrincipals:
    def _setup(self, mock_session, principals, next_link=None):
        mock_session.post.return_value = _token_response()
        mock_session.get.return_value = _make_response(
            200, {"value": principals, "@odata.nextLink": next_link}
        )

    def test_returns_principals_and_no_next_link(self, client, mock_session):
        self._setup(mock_session, [{"id": "sp-1"}])
        principals, next_link = client.list_service_principals()
        assert principals == [{"id": "sp-1"}]
        assert next_link is None

    def test_default_url_uses_service_principals_endpoint(self, client, mock_session):
        self._setup(mock_session, [])
        client.list_service_principals()
        url = mock_session.get.call_args[0][0]
        assert "/v1.0/servicePrincipals" in url

    def test_default_select_includes_sp_specific_fields(self, client, mock_session):
        self._setup(mock_session, [])
        client.list_service_principals()
        url = mock_session.get.call_args[0][0]
        assert "preferredSingleSignOnMode" in url

    def test_custom_select_passed_through(self, client, mock_session):
        self._setup(mock_session, [])
        client.list_service_principals(select="id,accountEnabled")
        url = mock_session.get.call_args[0][0]
        assert "$select=id,accountEnabled" in url

    def test_top_capped_at_max_page_size(self, client, mock_session):
        self._setup(mock_session, [])
        client.list_service_principals(top=9999)
        url = mock_session.get.call_args[0][0]
        assert f"$top={SERVICE_PRINCIPALS_PAGE_SIZE}" in url

    def test_next_link_used_directly(self, client, mock_session):
        next_url = "https://graph.microsoft.com/v1.0/servicePrincipals?$skiptoken=xyz"
        mock_session.post.return_value = _token_response()
        mock_session.get.return_value = _make_response(200, {"value": []})
        client.list_service_principals(next_link=next_url)
        called_url = mock_session.get.call_args[0][0]
        assert called_url == next_url

    def test_returns_next_link_when_present(self, client, mock_session):
        next_url = "https://graph.microsoft.com/v1.0/servicePrincipals?$skiptoken=abc"
        self._setup(mock_session, [{"id": "sp-1"}], next_link=next_url)
        _, next_link = client.list_service_principals()
        assert next_link == next_url
