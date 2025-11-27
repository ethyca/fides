import json
import sys
from unittest.mock import MagicMock, patch

import pytest
import requests
from requests.adapters import HTTPAdapter

from fides.api.common_exceptions import ConnectionException
from fides.api.service.connectors.okta_http_client import (
    DEFAULT_API_LIMIT,
    DEFAULT_MAX_PAGES,
    DEFAULT_OKTA_SCOPES,
    DEFAULT_REQUEST_TIMEOUT,
    OktaHttpClient,
)

RSA_JWK = {
    "kty": "RSA",
    "kid": "test-kid-rsa",
    "n": "test-modulus",
    "e": "AQAB",
    "d": "test-private-exponent",
}
EC_JWK = {
    "kty": "EC",
    "crv": "P-256",
    "kid": "test-kid-ec",
    "x": "test-x",
    "y": "test-y",
    "d": "test-d-ec",
}

TEST_ORG_URL = "https://test.okta.com"
TEST_CLIENT_ID = "test-client-id"
TEST_PRIVATE_KEY_STR = "not-used-when-injected"


@pytest.fixture
def mock_session():
    """Mock requests.Session for testing."""
    session = MagicMock(spec=requests.Session)
    return session


@pytest.fixture
def client_with_injection(mock_session):
    """Create client with injected session for testing."""
    return OktaHttpClient(
        org_url=TEST_ORG_URL,
        client_id=TEST_CLIENT_ID,
        private_key=TEST_PRIVATE_KEY_STR,
        session=mock_session,
    )


class TestOktaHttpClientInit:
    def test_injected_session_set(self, client_with_injection, mock_session):
        assert client_with_injection._session is mock_session
        assert client_with_injection.org_url == TEST_ORG_URL

    def test_init_strips_trailing_slash(self, mock_session):
        client = OktaHttpClient(
            org_url=f"{TEST_ORG_URL}/",
            client_id=TEST_CLIENT_ID,
            private_key=TEST_PRIVATE_KEY_STR,
            session=mock_session,
        )
        assert client.org_url == TEST_ORG_URL

    def test_default_scopes_are_tuple(self, client_with_injection):
        assert client_with_injection.scopes == DEFAULT_OKTA_SCOPES
        assert isinstance(client_with_injection.scopes, tuple)

    def test_custom_scopes_coerced_to_tuple(self, mock_session):
        scopes = ["okta.apps.read", "okta.users.read"]
        client = OktaHttpClient(
            org_url=TEST_ORG_URL,
            client_id=TEST_CLIENT_ID,
            private_key=TEST_PRIVATE_KEY_STR,
            scopes=scopes,
            session=mock_session,
        )
        assert client.scopes == tuple(scopes)

    @patch(
        "fides.api.service.connectors.okta_http_client.OktaHttpClient._determine_alg_from_jwk"
    )
    @patch("fides.api.service.connectors.okta_http_client.OktaHttpClient._parse_jwk")
    @patch("requests_oauth2client.PrivateKeyJwt")
    @patch("requests_oauth2client.OAuth2Client")
    @patch("requests_oauth2client.OAuth2ClientCredentialsAuth")
    @patch("requests_oauth2client.DPoPKey")
    def test_full_initialization_without_injection(
        self,
        mock_dpop_class,
        mock_auth_class,
        mock_oauth_class,
        mock_private_key_jwt,
        mock_parse_jwk,
        mock_determine_alg,
    ):
        mock_parse_jwk.return_value = RSA_JWK
        mock_determine_alg.return_value = "RS256"
        mock_dpop_instance = MagicMock()
        mock_dpop_class.generate.return_value = mock_dpop_instance
        mock_oauth_instance = MagicMock()
        mock_oauth_class.return_value = mock_oauth_instance

        client = OktaHttpClient(
            org_url=TEST_ORG_URL,
            client_id=TEST_CLIENT_ID,
            private_key=json.dumps(RSA_JWK),
        )

        mock_parse_jwk.assert_called_once_with(json.dumps(RSA_JWK))
        mock_determine_alg.assert_called_once_with(RSA_JWK)
        mock_dpop_class.generate.assert_called_once_with(alg="ES256")
        mock_private_key_jwt.assert_called_once_with(
            TEST_CLIENT_ID, RSA_JWK, alg="RS256"
        )
        mock_oauth_class.assert_called_once_with(
            token_endpoint=f"{TEST_ORG_URL}/oauth2/v1/token",
            auth=mock_private_key_jwt.return_value,
            dpop_bound_access_tokens=True,
        )
        mock_auth_class.assert_called_once_with(
            client=mock_oauth_instance,
            scope="okta.apps.read",
            dpop_key=mock_dpop_instance,
            leeway=600,
        )
        # Verify session has auth and adapters configured
        assert hasattr(client, "_session")

    def test_invalid_key_raises_connection_exception(self):
        with pytest.raises(ConnectionException) as exc_info:
            OktaHttpClient(
                org_url=TEST_ORG_URL,
                client_id=TEST_CLIENT_ID,
                private_key="not-valid-json",
            )
        assert "Invalid private key format" in str(exc_info.value)

    def test_public_key_raises_connection_exception(self):
        public_jwk = RSA_JWK.copy()
        del public_jwk["d"]
        with pytest.raises(ConnectionException) as exc_info:
            OktaHttpClient(
                org_url=TEST_ORG_URL,
                client_id=TEST_CLIENT_ID,
                private_key=json.dumps(public_jwk),
            )
        assert "Invalid private key format" in str(exc_info.value)

    def test_import_error_raises_connection_exception(self):
        with patch.dict(sys.modules, {"requests_oauth2client": None}):
            with pytest.raises(ConnectionException) as exc_info:
                OktaHttpClient(
                    org_url=TEST_ORG_URL,
                    client_id=TEST_CLIENT_ID,
                    private_key=json.dumps(RSA_JWK),
                )
        assert "requests-oauth2client' library is required" in str(exc_info.value)


class TestOktaHttpClientMethods:
    @pytest.fixture
    def mock_rate_limiter(self):
        """Mock rate limiter to avoid Redis dependency in tests."""
        with patch("fides.api.service.connectors.okta_http_client.RateLimiter") as mock:
            mock.return_value.limit.return_value = None
            yield mock

    def test_list_applications_single_page(
        self,
        client_with_injection,
        mock_session,
        mock_rate_limiter,
    ):
        mock_apps = [{"id": "app1"}, {"id": "app2"}]
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.status_code = 200
        mock_response.json.return_value = mock_apps
        mock_session.get.return_value = mock_response

        apps, next_cursor = client_with_injection.list_applications()

        assert apps == mock_apps
        assert next_cursor is None
        mock_session.get.assert_called_once_with(
            f"{TEST_ORG_URL}/api/v1/apps",
            params={"limit": DEFAULT_API_LIMIT},
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )

    def test_list_applications_with_pagination(
        self,
        client_with_injection,
        mock_session,
        mock_rate_limiter,
    ):
        link_header = f'<{TEST_ORG_URL}/api/v1/apps?after=cursor123>; rel="next"'
        mock_response = MagicMock()
        mock_response.headers = {"Link": link_header}
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "app1"}]
        mock_session.get.return_value = mock_response

        apps, next_cursor = client_with_injection.list_applications(limit=1)

        assert apps == [{"id": "app1"}]
        assert next_cursor == "cursor123"
        mock_session.get.assert_called_once_with(
            f"{TEST_ORG_URL}/api/v1/apps",
            params={"limit": 1},
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )

    def test_list_applications_http_error(
        self,
        client_with_injection,
        mock_session,
        mock_rate_limiter,
    ):
        mock_session.get.side_effect = requests.RequestException("Network error")
        with pytest.raises(ConnectionException) as exc_info:
            client_with_injection.list_applications()
        assert "Okta API request failed" in str(exc_info.value)

    def test_list_applications_http_status_error(
        self,
        client_with_injection,
        mock_session,
        mock_rate_limiter,
    ):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
        mock_session.get.return_value = mock_response

        with pytest.raises(ConnectionException) as exc_info:
            client_with_injection.list_applications()
        assert "Okta API request failed" in str(exc_info.value)

    def test_list_all_applications_multiple_pages(self, client_with_injection):
        with patch.object(client_with_injection, "list_applications") as mock_list:
            mock_list.side_effect = [
                ([{"id": "app1"}], "cursor1"),
                ([{"id": "app2"}], "cursor2"),
                ([{"id": "app3"}], None),
            ]
            apps = client_with_injection.list_all_applications(page_size=1)
        assert [a["id"] for a in apps] == ["app1", "app2", "app3"]
        assert mock_list.call_count == 3

    def test_list_all_applications_respects_max_pages(self, client_with_injection):
        with patch.object(client_with_injection, "list_applications") as mock_list:
            mock_list.side_effect = [
                ([{"id": "app"}], "cursor1"),
                ([{"id": "app"}], "cursor2"),
                ([{"id": "app"}], "cursor3"),
            ]
            apps = client_with_injection.list_all_applications(page_size=1, max_pages=3)
        assert len(apps) == 3
        assert mock_list.call_count == 3

    def test_list_all_applications_stops_on_duplicate_cursor(
        self, client_with_injection
    ):
        with patch.object(client_with_injection, "list_applications") as mock_list:
            mock_list.side_effect = [
                ([{"id": "app1"}], "same_cursor"),
                ([{"id": "app2"}], "same_cursor"),
            ]
            apps = client_with_injection.list_all_applications(page_size=1)

        assert len(apps) == 2
        assert mock_list.call_count == 2


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_rate_limiter_called(self, mock_session):
        """Rate limiter should be called before requests."""
        client = OktaHttpClient(
            org_url=TEST_ORG_URL,
            client_id=TEST_CLIENT_ID,
            private_key=TEST_PRIVATE_KEY_STR,
            rate_limit_per_minute=100,
            session=mock_session,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.headers = {}
        mock_session.get.return_value = mock_response

        with patch(
            "fides.api.service.connectors.okta_http_client.RateLimiter"
        ) as mock_limiter_class:
            mock_limiter = MagicMock()
            mock_limiter_class.return_value = mock_limiter
            client.list_applications()

        mock_limiter.limit.assert_called_once()
        # Verify rate limit request was built correctly
        rate_limit_requests = mock_limiter.limit.call_args[0][0]
        assert len(rate_limit_requests) == 1
        assert rate_limit_requests[0].key == f"okta:{TEST_ORG_URL}"
        assert rate_limit_requests[0].rate_limit == 100

    def test_rate_limiting_disabled_when_none(self, mock_session):
        """Rate limiter should not be called when rate_limit_per_minute is None."""
        client = OktaHttpClient(
            org_url=TEST_ORG_URL,
            client_id=TEST_CLIENT_ID,
            private_key=TEST_PRIVATE_KEY_STR,
            rate_limit_per_minute=None,
            session=mock_session,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.headers = {}
        mock_session.get.return_value = mock_response

        with patch(
            "fides.api.service.connectors.okta_http_client.RateLimiter"
        ) as mock_limiter_class:
            client.list_applications()

        # RateLimiter should not have been instantiated
        mock_limiter_class.assert_not_called()

    def test_build_rate_limit_requests(self, mock_session):
        """_build_rate_limit_requests should return correct configuration."""
        client = OktaHttpClient(
            org_url=TEST_ORG_URL,
            client_id=TEST_CLIENT_ID,
            private_key=TEST_PRIVATE_KEY_STR,
            rate_limit_per_minute=250,
            session=mock_session,
        )

        rate_requests = client._build_rate_limit_requests()
        assert len(rate_requests) == 1
        assert rate_requests[0].key == f"okta:{TEST_ORG_URL}"
        assert rate_requests[0].rate_limit == 250


class TestStaticHelperMethods:
    def test_extract_cursor_from_link_header(self):
        link_header = (
            f'<{TEST_ORG_URL}/api/v1/apps?after=abc123>; rel="next", '
            f'<{TEST_ORG_URL}/api/v1/apps?after=prev>; rel="prev"'
        )
        cursor = OktaHttpClient._extract_next_cursor(link_header)
        assert cursor == "abc123"

    def test_extract_cursor_no_next_link(self):
        cursor = OktaHttpClient._extract_next_cursor(
            f'<{TEST_ORG_URL}/api/v1/apps>; rel="self"'
        )
        assert cursor is None

    def test_extract_cursor_none_header(self):
        assert OktaHttpClient._extract_next_cursor(None) is None

    def test_extract_cursor_no_angle_brackets(self):
        link_header = 'https://test.okta.com/api/v1/apps?after=abc123; rel="next"'
        cursor = OktaHttpClient._extract_next_cursor(link_header)
        assert cursor is None

    def test_extract_cursor_no_after_param(self):
        link_header = f'<{TEST_ORG_URL}/api/v1/apps?limit=200>; rel="next"'
        cursor = OktaHttpClient._extract_next_cursor(link_header)
        assert cursor is None

    def test_extract_cursor_url_encoded(self):
        link_header = (
            f'<{TEST_ORG_URL}/api/v1/apps?after=abc%3D123&limit=200>; rel="next"'
        )
        cursor = OktaHttpClient._extract_next_cursor(link_header)
        assert cursor == "abc=123"

    def test_extract_cursor_multiple_params(self):
        link_header = f'<{TEST_ORG_URL}/api/v1/apps?limit=200&after=xyz789&filter=active>; rel="next"'
        cursor = OktaHttpClient._extract_next_cursor(link_header)
        assert cursor == "xyz789"

    def test_parse_jwk_accepts_dict(self):
        parsed = OktaHttpClient._parse_jwk(RSA_JWK)
        assert parsed["kid"] == RSA_JWK["kid"]

    def test_parse_jwk_rejects_dict_without_d(self):
        # _parse_jwk validates 'd' parameter for defense-in-depth
        public_jwk = RSA_JWK.copy()
        del public_jwk["d"]
        with pytest.raises(ValueError) as exc_info:
            OktaHttpClient._parse_jwk(public_jwk)
        assert "missing 'd' parameter" in str(exc_info.value)

    def test_parse_jwk_rejects_string_without_d(self):
        # _parse_jwk validates 'd' parameter for JSON strings too
        public_jwk = RSA_JWK.copy()
        del public_jwk["d"]
        with pytest.raises(ValueError) as exc_info:
            OktaHttpClient._parse_jwk(json.dumps(public_jwk))
        assert "missing 'd' parameter" in str(exc_info.value)

    def test_parse_jwk_round_trip(self):
        parsed = OktaHttpClient._parse_jwk(json.dumps(RSA_JWK))
        assert parsed["kid"] == RSA_JWK["kid"]

    def test_determine_alg_from_jwk_prefers_alg_field(self):
        jwk = {**RSA_JWK, "alg": "RS512"}
        assert OktaHttpClient._determine_alg_from_jwk(jwk) == "RS512"

    def test_determine_alg_from_ec_curve(self):
        alg = OktaHttpClient._determine_alg_from_jwk(EC_JWK)
        assert alg == "ES256"

    def test_determine_alg_default_fallback(self):
        jwk = {"kty": "unknown", "d": "value"}
        assert OktaHttpClient._determine_alg_from_jwk(jwk) == "RS256"


class TestSessionConfiguration:
    """Tests for verifying session configuration with library built-ins."""

    @patch("requests_oauth2client.PrivateKeyJwt")
    @patch("requests_oauth2client.OAuth2Client")
    @patch("requests_oauth2client.OAuth2ClientCredentialsAuth")
    @patch("requests_oauth2client.DPoPKey")
    def test_session_has_oauth2_auth(
        self,
        mock_dpop_class,
        mock_auth_class,
        mock_oauth_class,
        mock_private_key_jwt,
    ):
        """Session should have OAuth2ClientCredentialsAuth configured."""
        mock_dpop_instance = MagicMock()
        mock_dpop_class.generate.return_value = mock_dpop_instance
        mock_oauth_instance = MagicMock()
        mock_oauth_class.return_value = mock_oauth_instance
        mock_auth_instance = MagicMock()
        mock_auth_class.return_value = mock_auth_instance

        client = OktaHttpClient(
            org_url=TEST_ORG_URL,
            client_id=TEST_CLIENT_ID,
            private_key=json.dumps(RSA_JWK),
        )

        # Verify OAuth2ClientCredentialsAuth was created with correct params
        mock_auth_class.assert_called_once_with(
            client=mock_oauth_instance,
            scope="okta.apps.read",
            dpop_key=mock_dpop_instance,
            leeway=600,
        )
        # Verify session.auth is set
        assert client._session.auth is mock_auth_instance

    @patch("requests_oauth2client.PrivateKeyJwt")
    @patch("requests_oauth2client.OAuth2Client")
    @patch("requests_oauth2client.OAuth2ClientCredentialsAuth")
    @patch("requests_oauth2client.DPoPKey")
    def test_session_has_retry_adapter(
        self,
        mock_dpop_class,
        mock_auth_class,
        mock_oauth_class,
        mock_private_key_jwt,
    ):
        """Session should have HTTPAdapter with retry strategy configured."""
        mock_dpop_class.generate.return_value = MagicMock()
        mock_oauth_class.return_value = MagicMock()
        mock_auth_class.return_value = MagicMock()

        client = OktaHttpClient(
            org_url=TEST_ORG_URL,
            client_id=TEST_CLIENT_ID,
            private_key=json.dumps(RSA_JWK),
        )

        # Verify HTTPS adapter is mounted
        https_adapter = client._session.get_adapter("https://example.com")
        assert isinstance(https_adapter, HTTPAdapter)

        # Verify retry strategy
        retry = https_adapter.max_retries
        assert retry.total == 3
        assert retry.backoff_factor == 1.0
        assert 429 in retry.status_forcelist
        assert 502 in retry.status_forcelist
        assert 503 in retry.status_forcelist
        assert 504 in retry.status_forcelist
        assert retry.respect_retry_after_header is True

    @patch("requests_oauth2client.PrivateKeyJwt")
    @patch("requests_oauth2client.OAuth2Client")
    @patch("requests_oauth2client.OAuth2ClientCredentialsAuth")
    @patch("requests_oauth2client.DPoPKey")
    def test_dpop_enabled_on_oauth_client(
        self,
        mock_dpop_class,
        mock_auth_class,
        mock_oauth_class,
        mock_private_key_jwt,
    ):
        """OAuth2Client should have dpop_bound_access_tokens=True."""
        mock_dpop_class.generate.return_value = MagicMock()
        mock_auth_class.return_value = MagicMock()

        OktaHttpClient(
            org_url=TEST_ORG_URL,
            client_id=TEST_CLIENT_ID,
            private_key=json.dumps(RSA_JWK),
        )

        mock_oauth_class.assert_called_once()
        call_kwargs = mock_oauth_class.call_args[1]
        assert call_kwargs["dpop_bound_access_tokens"] is True

    @patch("requests_oauth2client.PrivateKeyJwt")
    @patch("requests_oauth2client.OAuth2Client")
    @patch("requests_oauth2client.OAuth2ClientCredentialsAuth")
    @patch("requests_oauth2client.DPoPKey")
    def test_custom_scopes_passed_to_auth(
        self,
        mock_dpop_class,
        mock_auth_class,
        mock_oauth_class,
        mock_private_key_jwt,
    ):
        """Custom scopes should be passed to OAuth2ClientCredentialsAuth."""
        mock_dpop_class.generate.return_value = MagicMock()
        mock_oauth_class.return_value = MagicMock()
        mock_auth_class.return_value = MagicMock()

        custom_scopes = ["okta.apps.read", "okta.users.read"]
        OktaHttpClient(
            org_url=TEST_ORG_URL,
            client_id=TEST_CLIENT_ID,
            private_key=json.dumps(RSA_JWK),
            scopes=custom_scopes,
        )

        call_kwargs = mock_auth_class.call_args[1]
        assert call_kwargs["scope"] == "okta.apps.read okta.users.read"
