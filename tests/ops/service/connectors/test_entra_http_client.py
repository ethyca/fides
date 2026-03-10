"""Tests for Microsoft Entra ID HTTP client."""

from unittest.mock import MagicMock, patch

import pytest
import requests
from requests.adapters import HTTPAdapter

from fides.api.common_exceptions import ConnectionException
from fides.api.service.connectors.entra_http_client import (
    DEFAULT_REQUEST_TIMEOUT,
    GRAPH_BASE_URL,
    GRAPH_DEFAULT_SCOPE,
    SERVICE_PRINCIPALS_PAGE_SIZE,
    SERVICE_PRINCIPALS_SELECT,
    EntraHttpClient,
)

TEST_TENANT_ID = "11111111-2222-3333-4444-555555555555"
TEST_CLIENT_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
TEST_CLIENT_SECRET = "test-client-secret-value"


@pytest.fixture
def mock_session():
    """Mock requests.Session for testing."""
    return MagicMock(spec=requests.Session)


@pytest.fixture
def client(mock_session):
    """Create client with injected session for testing."""
    return EntraHttpClient(
        tenant_id=TEST_TENANT_ID,
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
        session=mock_session,
    )


def _token_response(token="test-access-token", expires_in=3600):
    """Helper to build a mock token response."""
    resp = MagicMock()
    resp.ok = True
    resp.json.return_value = {"access_token": token, "expires_in": expires_in}
    return resp


def _graph_response(value, next_link=None, status_code=200):
    """Helper to build a mock Graph API response."""
    resp = MagicMock()
    resp.ok = status_code == 200
    resp.status_code = status_code
    body = {"value": value}
    if next_link:
        body["@odata.nextLink"] = next_link
    resp.json.return_value = body
    return resp


class TestEntraHttpClientInit:
    def test_injected_session_set(self, client, mock_session):
        assert client._session is mock_session
        assert client.tenant_id == TEST_TENANT_ID
        assert client.client_id == TEST_CLIENT_ID
        assert client.client_secret == TEST_CLIENT_SECRET

    def test_init_strips_whitespace(self, mock_session):
        c = EntraHttpClient(
            tenant_id=f"  {TEST_TENANT_ID}  ",
            client_id=f"  {TEST_CLIENT_ID}  ",
            client_secret=TEST_CLIENT_SECRET,
            session=mock_session,
        )
        assert c.tenant_id == TEST_TENANT_ID
        assert c.client_id == TEST_CLIENT_ID

    def test_default_session_has_retry_adapter(self):
        c = EntraHttpClient(
            tenant_id=TEST_TENANT_ID,
            client_id=TEST_CLIENT_ID,
            client_secret=TEST_CLIENT_SECRET,
        )
        adapter = c._session.get_adapter("https://example.com")
        assert isinstance(adapter, HTTPAdapter)
        retry = adapter.max_retries
        assert retry.total == 3
        assert retry.backoff_factor == 1
        assert 429 in retry.status_forcelist
        assert 500 in retry.status_forcelist
        assert 502 in retry.status_forcelist
        assert 503 in retry.status_forcelist
        assert 504 in retry.status_forcelist

    def test_token_url(self, client):
        expected = (
            f"https://login.microsoftonline.com/{TEST_TENANT_ID}/oauth2/v2.0/token"
        )
        assert client._token_url() == expected


class TestTokenAcquisition:
    def test_get_token_success(self, client, mock_session):
        mock_session.post.return_value = _token_response("my-token", 3600)

        token = client._get_token()

        assert token == "my-token"
        mock_session.post.assert_called_once_with(
            client._token_url(),
            data={
                "grant_type": "client_credentials",
                "client_id": TEST_CLIENT_ID,
                "client_secret": TEST_CLIENT_SECRET,
                "scope": GRAPH_DEFAULT_SCOPE,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )

    def test_get_token_caches(self, client, mock_session):
        mock_session.post.return_value = _token_response("cached-token", 3600)

        token1 = client._get_token()
        token2 = client._get_token()

        assert token1 == token2 == "cached-token"
        assert mock_session.post.call_count == 1

    def test_get_token_refreshes_when_expired(self, client, mock_session):
        mock_session.post.return_value = _token_response("token1", 3600)
        client._get_token()

        # Force expiry
        client._token_expiry = 0
        mock_session.post.return_value = _token_response("token2", 3600)
        token = client._get_token()

        assert token == "token2"
        assert mock_session.post.call_count == 2

    def test_get_token_short_expiry_clamped_to_zero(self, client, mock_session):
        """Token with expires_in < 600 should not produce negative expiry."""
        mock_session.post.return_value = _token_response("short-token", 60)

        with patch("fides.api.service.connectors.entra_http_client.time") as mock_time:
            mock_time.monotonic.return_value = 1000.0
            client._get_token()

        # max(60 - 600, 0) == 0, so expiry = 1000.0 + 0 = 1000.0
        assert client._token_expiry == 1000.0

    def test_get_token_http_error(self, client, mock_session):
        resp = MagicMock()
        resp.ok = False
        resp.status_code = 401
        resp.json.return_value = {"error_description": "Invalid client secret"}
        mock_session.post.return_value = resp

        with pytest.raises(
            ConnectionException, match="Failed to obtain Entra access token: 401"
        ):
            client._get_token()

    def test_get_token_http_error_no_json(self, client, mock_session):
        resp = MagicMock()
        resp.ok = False
        resp.status_code = 500
        resp.json.side_effect = ValueError("not json")
        mock_session.post.return_value = resp

        with pytest.raises(
            ConnectionException, match="Failed to obtain Entra access token: 500"
        ):
            client._get_token()

    def test_get_token_missing_access_token(self, client, mock_session):
        resp = MagicMock()
        resp.ok = True
        resp.json.return_value = {"token_type": "bearer"}
        mock_session.post.return_value = resp

        with pytest.raises(ConnectionException, match="missing access_token"):
            client._get_token()


class TestListServicePrincipals:
    def test_single_page(self, client, mock_session):
        mock_session.post.return_value = _token_response()
        apps = [{"id": "sp1"}, {"id": "sp2"}]
        mock_session.get.return_value = _graph_response(apps)

        result, next_link = client.list_service_principals()

        assert result == apps
        assert next_link is None
        mock_session.get.assert_called_once()
        call_url = mock_session.get.call_args[0][0]
        assert "/v1.0/servicePrincipals" in call_url
        assert f"$top={SERVICE_PRINCIPALS_PAGE_SIZE}" in call_url
        assert f"$select={SERVICE_PRINCIPALS_SELECT}" in call_url

    def test_with_pagination(self, client, mock_session):
        mock_session.post.return_value = _token_response()
        next_url = f"{GRAPH_BASE_URL}/v1.0/servicePrincipals?$skiptoken=abc123"
        mock_session.get.return_value = _graph_response(
            [{"id": "sp1"}], next_link=next_url
        )

        result, next_link = client.list_service_principals()

        assert result == [{"id": "sp1"}]
        assert next_link == next_url

    def test_follows_next_link(self, client, mock_session):
        mock_session.post.return_value = _token_response()
        pagination_url = f"{GRAPH_BASE_URL}/v1.0/servicePrincipals?$skiptoken=page2"
        mock_session.get.return_value = _graph_response([{"id": "sp3"}])

        result, next_link = client.list_service_principals(next_link=pagination_url)

        assert result == [{"id": "sp3"}]
        # Should use the next_link URL directly
        mock_session.get.assert_called_once_with(
            pagination_url,
            headers={"Authorization": "Bearer test-access-token"},
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )

    def test_next_link_ssrf_rejected(self, client, mock_session):
        mock_session.post.return_value = _token_response()

        with pytest.raises(ConnectionException, match="Invalid pagination URL"):
            client.list_service_principals(
                next_link="https://evil.example.com/steal-token"
            )

    def test_next_link_http_scheme_rejected(self, client, mock_session):
        mock_session.post.return_value = _token_response()

        with pytest.raises(ConnectionException, match="Invalid pagination URL"):
            client.list_service_principals(
                next_link="http://graph.microsoft.com/v1.0/servicePrincipals"
            )

    def test_top_clamped_to_max(self, client, mock_session):
        mock_session.post.return_value = _token_response()
        mock_session.get.return_value = _graph_response([])

        client.list_service_principals(top=500)

        call_url = mock_session.get.call_args[0][0]
        assert f"$top={SERVICE_PRINCIPALS_PAGE_SIZE}" in call_url

    def test_custom_select(self, client, mock_session):
        mock_session.post.return_value = _token_response()
        mock_session.get.return_value = _graph_response([])

        client.list_service_principals(select="id,displayName")

        call_url = mock_session.get.call_args[0][0]
        assert "$select=id,displayName" in call_url

    def test_graph_api_error(self, client, mock_session):
        mock_session.post.return_value = _token_response()
        resp = MagicMock()
        resp.ok = False
        resp.status_code = 500
        resp.json.return_value = {
            "error": {"code": "InternalError", "message": "Something broke"}
        }
        mock_session.get.return_value = resp

        with pytest.raises(
            ConnectionException,
            match="Microsoft Graph request failed: 500. Something broke",
        ):
            client.list_service_principals()

    def test_graph_403_permission_hint(self, client, mock_session):
        mock_session.post.return_value = _token_response()
        resp = MagicMock()
        resp.ok = False
        resp.status_code = 403
        resp.json.return_value = {
            "error": {
                "code": "Authorization_RequestDenied",
                "message": "Insufficient privileges",
            }
        }
        mock_session.get.return_value = resp

        with pytest.raises(
            ConnectionException, match="Insufficient Microsoft Graph permissions"
        ):
            client.list_service_principals()

    def test_graph_error_non_json(self, client, mock_session):
        mock_session.post.return_value = _token_response()
        resp = MagicMock()
        resp.ok = False
        resp.status_code = 502
        resp.json.side_effect = ValueError("not json")
        mock_session.get.return_value = resp

        with pytest.raises(
            ConnectionException, match="Microsoft Graph request failed: 502"
        ):
            client.list_service_principals()

    def test_non_list_value_returns_empty(self, client, mock_session):
        """If Graph returns non-list 'value', treat as empty."""
        mock_session.post.return_value = _token_response()
        resp = MagicMock()
        resp.ok = True
        resp.json.return_value = {"value": "not-a-list"}
        mock_session.get.return_value = resp

        result, _ = client.list_service_principals()
        assert result == []
