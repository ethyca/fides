import json
import sys
import time
from datetime import datetime, timedelta
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
import requests
from requests.auth import AuthBase

from fides.api.common_exceptions import ConnectionException
from fides.api.service.connectors.okta_http_client import (
    DEFAULT_API_LIMIT,
    DEFAULT_MAX_PAGES,
    DEFAULT_OKTA_SCOPES,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_RETRY_COUNT,
    RETRY_STATUS_CODES,
    TOKEN_EXPIRY_BUFFER_MINUTES,
    OktaHttpClient,
    _get_retry_after,
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
def mock_oauth_client_and_dpop_key():
    return MagicMock(), MagicMock()


@pytest.fixture
def mock_oauth2_exceptions():
    """Mock requests_oauth2client.exceptions module for tests that call _get_token()."""

    class StubInvalidClient(Exception):
        pass

    class StubUnauthorizedClient(Exception):
        pass

    class StubOAuth2Error(Exception):
        pass

    exceptions_module = ModuleType("requests_oauth2client.exceptions")
    exceptions_module.InvalidClient = StubInvalidClient
    exceptions_module.UnauthorizedClient = StubUnauthorizedClient
    exceptions_module.OAuth2Error = StubOAuth2Error

    package_module = ModuleType("requests_oauth2client")
    package_module.exceptions = exceptions_module

    with patch.dict(
        sys.modules,
        {
            "requests_oauth2client": package_module,
            "requests_oauth2client.exceptions": exceptions_module,
        },
    ):
        yield exceptions_module


@pytest.fixture
def client_with_injection(mock_oauth_client_and_dpop_key):
    mock_oauth_client, mock_dpop_key = mock_oauth_client_and_dpop_key
    return OktaHttpClient(
        org_url=TEST_ORG_URL,
        client_id=TEST_CLIENT_ID,
        private_key=TEST_PRIVATE_KEY_STR,
        oauth_client=mock_oauth_client,
        dpop_key=mock_dpop_key,
    )


class TestOktaHttpClientInit:
    def test_injected_dependencies_set(
        self, client_with_injection, mock_oauth_client_and_dpop_key
    ):
        mock_oauth_client, mock_dpop_key = mock_oauth_client_and_dpop_key
        assert client_with_injection._oauth_client is mock_oauth_client
        assert client_with_injection._dpop_key is mock_dpop_key
        assert client_with_injection.org_url == TEST_ORG_URL

    @pytest.mark.parametrize(
        "oauth_client,dpop_key",
        [
            (MagicMock(), None),
            (None, MagicMock()),
        ],
    )
    def test_injection_requires_both(self, oauth_client, dpop_key):
        with pytest.raises(ValueError) as exc_info:
            OktaHttpClient(
                org_url=TEST_ORG_URL,
                client_id=TEST_CLIENT_ID,
                private_key=TEST_PRIVATE_KEY_STR,
                oauth_client=oauth_client,
                dpop_key=dpop_key,
            )
        assert "Both oauth_client and dpop_key" in str(exc_info.value)

    def test_init_strips_trailing_slash(self, mock_oauth_client_and_dpop_key):
        mock_oauth_client, mock_dpop_key = mock_oauth_client_and_dpop_key
        client = OktaHttpClient(
            org_url=f"{TEST_ORG_URL}/",
            client_id=TEST_CLIENT_ID,
            private_key=TEST_PRIVATE_KEY_STR,
            oauth_client=mock_oauth_client,
            dpop_key=mock_dpop_key,
        )
        assert client.org_url == TEST_ORG_URL

    def test_default_scopes_are_tuple(self, client_with_injection):
        assert client_with_injection.scopes == DEFAULT_OKTA_SCOPES
        assert isinstance(client_with_injection.scopes, tuple)

    def test_custom_scopes_coerced_to_tuple(self, mock_oauth_client_and_dpop_key):
        mock_oauth_client, mock_dpop_key = mock_oauth_client_and_dpop_key
        scopes = ["okta.apps.read", "okta.users.read"]
        client = OktaHttpClient(
            org_url=TEST_ORG_URL,
            client_id=TEST_CLIENT_ID,
            private_key=TEST_PRIVATE_KEY_STR,
            scopes=scopes,
            oauth_client=mock_oauth_client,
            dpop_key=mock_dpop_key,
        )
        assert client.scopes == tuple(scopes)

    @patch(
        "fides.api.service.connectors.okta_http_client.OktaHttpClient._determine_alg_from_jwk"
    )
    @patch("fides.api.service.connectors.okta_http_client.OktaHttpClient._parse_jwk")
    @patch("requests_oauth2client.PrivateKeyJwt")
    @patch("requests_oauth2client.OAuth2Client")
    @patch("requests_oauth2client.DPoPKey")
    def test_full_initialization_without_injection(
        self,
        mock_dpop_class,
        mock_oauth_class,
        mock_private_key_jwt,
        mock_parse_jwk,
        mock_determine_alg,
    ):
        mock_parse_jwk.return_value = RSA_JWK
        mock_determine_alg.return_value = "RS256"
        mock_dpop_instance = MagicMock()
        mock_dpop_class.generate.return_value = mock_dpop_instance

        client = OktaHttpClient(
            org_url=TEST_ORG_URL,
            client_id=TEST_CLIENT_ID,
            private_key=json.dumps(RSA_JWK),
        )

        mock_parse_jwk.assert_called_once_with(json.dumps(RSA_JWK))
        mock_determine_alg.assert_called_once_with(RSA_JWK)
        mock_dpop_class.generate.assert_called_once_with(alg="ES256")
        assert client._dpop_key is mock_dpop_instance
        mock_private_key_jwt.assert_called_once_with(
            TEST_CLIENT_ID, RSA_JWK, alg="RS256"
        )
        mock_oauth_class.assert_called_once_with(
            token_endpoint=f"{TEST_ORG_URL}/oauth2/v1/token",
            auth=mock_private_key_jwt.return_value,
        )

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
    def mock_token(self, client_with_injection):
        mock_token = MagicMock(spec=AuthBase)
        mock_token.expires_at = datetime.utcnow().timestamp() + 3600  # 1 hour from now
        client_with_injection._oauth_client.client_credentials.return_value = mock_token
        return mock_token

    @pytest.fixture
    def mock_rate_limiter(self):
        """Mock rate limiter to avoid Redis dependency in tests."""
        with patch("fides.api.service.connectors.okta_http_client.RateLimiter") as mock:
            mock.return_value.limit.return_value = None
            yield mock

    def test_list_applications_single_page(
        self, client_with_injection, mock_token, mock_rate_limiter, mock_oauth2_exceptions
    ):
        mock_apps = [{"id": "app1"}, {"id": "app2"}]
        with patch("requests.request") as mock_request:
            mock_response = MagicMock(headers={}, status_code=200)
            mock_response.ok = True
            mock_response.json.return_value = mock_apps
            mock_request.return_value = mock_response

            apps, next_cursor = client_with_injection.list_applications()

            assert apps == mock_apps
            assert next_cursor is None
            mock_request.assert_called_once_with(
                method="GET",
                url=f"{TEST_ORG_URL}/api/v1/apps",
                params={"limit": DEFAULT_API_LIMIT},
                auth=mock_token,
                timeout=DEFAULT_REQUEST_TIMEOUT,
            )

    def test_list_applications_with_pagination(
        self, client_with_injection, mock_token, mock_rate_limiter, mock_oauth2_exceptions
    ):
        link_header = f'<{TEST_ORG_URL}/api/v1/apps?after=cursor123>; rel="next"'
        with patch("requests.request") as mock_request:
            mock_response = MagicMock(headers={"Link": link_header}, status_code=200)
            mock_response.ok = True
            mock_response.json.return_value = [{"id": "app1"}]
            mock_request.return_value = mock_response

            apps, next_cursor = client_with_injection.list_applications(limit=1)

            assert apps == [{"id": "app1"}]
            assert next_cursor == "cursor123"
            mock_request.assert_called_once_with(
                method="GET",
                url=f"{TEST_ORG_URL}/api/v1/apps",
                params={"limit": 1},
                auth=mock_token,
                timeout=DEFAULT_REQUEST_TIMEOUT,
            )

    def test_list_applications_oauth_error(
        self, client_with_injection, mock_rate_limiter, mock_oauth2_exceptions
    ):
        client_with_injection._oauth_client.client_credentials.side_effect = (
            mock_oauth2_exceptions.OAuth2Error("invalid_client")
        )
        with pytest.raises(ConnectionException) as exc_info:
            client_with_injection.list_applications()
        assert "OAuth2 token acquisition failed" in str(exc_info.value)

    def test_list_applications_http_error(
        self, client_with_injection, mock_token, mock_rate_limiter, mock_oauth2_exceptions
    ):
        with patch("requests.request") as mock_request:
            mock_request.side_effect = requests.RequestException("Network error")
            with pytest.raises(ConnectionException) as exc_info:
                client_with_injection.list_applications()
        assert "Okta API request failed" in str(exc_info.value)

    def test_get_token_import_error(self, client_with_injection):
        with patch.dict(sys.modules, {"requests_oauth2client.exceptions": None}):
            with pytest.raises(ConnectionException) as exc_info:
                client_with_injection._get_token()
        assert "requests-oauth2client' library is required" in str(exc_info.value)

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


class TestTokenCaching:
    """Tests for token caching functionality."""

    @pytest.fixture
    def client_with_injection(self, mock_oauth_client_and_dpop_key):
        mock_oauth_client, mock_dpop_key = mock_oauth_client_and_dpop_key
        return OktaHttpClient(
            org_url=TEST_ORG_URL,
            client_id=TEST_CLIENT_ID,
            private_key=TEST_PRIVATE_KEY_STR,
            oauth_client=mock_oauth_client,
            dpop_key=mock_dpop_key,
        )

    def test_token_cached_on_first_call(
        self, client_with_injection, mock_oauth2_exceptions
    ):
        """Token should be cached after first acquisition."""
        mock_token = MagicMock(spec=AuthBase)
        mock_token.expires_at = datetime.utcnow().timestamp() + 3600
        client_with_injection._oauth_client.client_credentials.return_value = mock_token

        # First call should acquire token
        token1 = client_with_injection._get_token()
        assert token1 is mock_token
        assert client_with_injection._cached_token is mock_token
        assert client_with_injection._oauth_client.client_credentials.call_count == 1

    def test_cached_token_reused(self, client_with_injection, mock_oauth2_exceptions):
        """Cached token should be reused on subsequent calls."""
        mock_token = MagicMock(spec=AuthBase)
        mock_token.expires_at = datetime.utcnow().timestamp() + 3600
        client_with_injection._oauth_client.client_credentials.return_value = mock_token

        # Multiple calls should reuse the same token
        token1 = client_with_injection._get_token()
        token2 = client_with_injection._get_token()
        token3 = client_with_injection._get_token()

        assert token1 is token2 is token3
        # Should only call client_credentials once
        assert client_with_injection._oauth_client.client_credentials.call_count == 1

    def test_token_refreshed_when_close_to_expiry(
        self, client_with_injection, mock_oauth2_exceptions
    ):
        """Token should be refreshed when close to expiry (within 10 min buffer)."""
        # First token expires in 5 minutes (within buffer)
        mock_token1 = MagicMock(spec=AuthBase)
        mock_token1.expires_at = datetime.utcnow().timestamp() + 300  # 5 minutes
        mock_token2 = MagicMock(spec=AuthBase)
        mock_token2.expires_at = datetime.utcnow().timestamp() + 3600

        client_with_injection._oauth_client.client_credentials.side_effect = [
            mock_token1,
            mock_token2,
        ]

        # First call gets token1
        token1 = client_with_injection._get_token()
        assert token1 is mock_token1

        # Second call should get new token since first is close to expiry
        token2 = client_with_injection._get_token()
        assert token2 is mock_token2
        assert client_with_injection._oauth_client.client_credentials.call_count == 2

    def test_token_not_refreshed_when_valid(
        self, client_with_injection, mock_oauth2_exceptions
    ):
        """Token should not be refreshed when still valid (outside buffer)."""
        # Token expires in 20 minutes (outside 10 min buffer)
        mock_token = MagicMock(spec=AuthBase)
        mock_token.expires_at = datetime.utcnow().timestamp() + 1200  # 20 minutes
        client_with_injection._oauth_client.client_credentials.return_value = mock_token

        # Multiple calls should all return same token
        for _ in range(5):
            client_with_injection._get_token()

        # Should only call client_credentials once
        assert client_with_injection._oauth_client.client_credentials.call_count == 1

    def test_clear_token_cache(self, client_with_injection, mock_oauth2_exceptions):
        """clear_token_cache should reset cached state."""
        mock_token = MagicMock(spec=AuthBase)
        mock_token.expires_at = datetime.utcnow().timestamp() + 3600
        client_with_injection._oauth_client.client_credentials.return_value = mock_token

        # Acquire token
        client_with_injection._get_token()
        assert client_with_injection._cached_token is not None

        # Clear cache
        client_with_injection.clear_token_cache()
        assert client_with_injection._cached_token is None
        assert client_with_injection._token_expires_at is None

        # Next call should acquire new token
        client_with_injection._get_token()
        assert client_with_injection._oauth_client.client_credentials.call_count == 2

    def test_token_expiry_from_expires_in(
        self, client_with_injection, mock_oauth2_exceptions
    ):
        """Token expiry should be calculated from expires_in if expires_at not available."""
        mock_token = MagicMock(spec=AuthBase)
        mock_token.expires_at = None
        mock_token.expires_in = 3600  # 1 hour
        client_with_injection._oauth_client.client_credentials.return_value = mock_token

        client_with_injection._get_token()

        # expires_at should be set based on expires_in
        expected_min = datetime.utcnow().timestamp() + 3500
        expected_max = datetime.utcnow().timestamp() + 3700
        assert expected_min < client_with_injection._token_expires_at < expected_max

    def test_token_default_expiry_when_no_expiration_info(
        self, client_with_injection, mock_oauth2_exceptions
    ):
        """Token should default to 1 hour expiry if no expiration info."""
        mock_token = MagicMock(spec=AuthBase)
        mock_token.expires_at = None
        mock_token.expires_in = None
        client_with_injection._oauth_client.client_credentials.return_value = mock_token

        client_with_injection._get_token()

        # Should default to 1 hour
        expected_min = datetime.utcnow().timestamp() + 3500
        expected_max = datetime.utcnow().timestamp() + 3700
        assert expected_min < client_with_injection._token_expires_at < expected_max


class TestRetryLogic:
    """Tests for retry logic."""

    @pytest.fixture
    def client_with_injection(self, mock_oauth_client_and_dpop_key):
        mock_oauth_client, mock_dpop_key = mock_oauth_client_and_dpop_key
        client = OktaHttpClient(
            org_url=TEST_ORG_URL,
            client_id=TEST_CLIENT_ID,
            private_key=TEST_PRIVATE_KEY_STR,
            rate_limit_per_minute=None,  # Disable rate limiting for these tests
            oauth_client=mock_oauth_client,
            dpop_key=mock_dpop_key,
        )
        # Set up token
        mock_token = MagicMock(spec=AuthBase)
        mock_token.expires_at = datetime.utcnow().timestamp() + 3600
        mock_oauth_client.client_credentials.return_value = mock_token
        return client

    def test_retry_on_429(self, client_with_injection, mock_oauth2_exceptions):
        """Should retry on 429 (rate limit) response."""
        mock_response_429 = MagicMock()
        mock_response_429.ok = False
        mock_response_429.status_code = 429
        mock_response_429.headers = {}

        mock_response_200 = MagicMock()
        mock_response_200.ok = True
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = []
        mock_response_200.headers = {}

        with patch("requests.request") as mock_request:
            with patch(
                "fides.api.service.connectors.okta_http_client.sleep"
            ) as mock_sleep:
                mock_request.side_effect = [mock_response_429, mock_response_200]
                apps, _ = client_with_injection.list_applications()

        assert apps == []
        assert mock_request.call_count == 2
        mock_sleep.assert_called_once()

    def test_retry_on_503(self, client_with_injection, mock_oauth2_exceptions):
        """Should retry on 503 (service unavailable) response."""
        mock_response_503 = MagicMock()
        mock_response_503.ok = False
        mock_response_503.status_code = 503
        mock_response_503.headers = {}

        mock_response_200 = MagicMock()
        mock_response_200.ok = True
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = []
        mock_response_200.headers = {}

        with patch("requests.request") as mock_request:
            with patch(
                "fides.api.service.connectors.okta_http_client.sleep"
            ) as mock_sleep:
                mock_request.side_effect = [mock_response_503, mock_response_200]
                apps, _ = client_with_injection.list_applications()

        assert apps == []
        assert mock_request.call_count == 2

    def test_no_retry_on_400(self, client_with_injection, mock_oauth2_exceptions):
        """Should not retry on 400 (bad request) response."""
        mock_response_400 = MagicMock()
        mock_response_400.ok = False
        mock_response_400.status_code = 400
        mock_response_400.raise_for_status.side_effect = requests.HTTPError(
            "Bad Request"
        )

        with patch("requests.request") as mock_request:
            mock_request.return_value = mock_response_400
            with pytest.raises(ConnectionException):
                client_with_injection.list_applications()

        # Should only try once (no retries)
        assert mock_request.call_count == 1

    def test_respects_retry_after_header(self, client_with_injection, mock_oauth2_exceptions):
        """Should respect Retry-After header when present."""
        mock_response_429 = MagicMock()
        mock_response_429.ok = False
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "5"}

        mock_response_200 = MagicMock()
        mock_response_200.ok = True
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = []
        mock_response_200.headers = {}

        with patch("requests.request") as mock_request:
            with patch(
                "fides.api.service.connectors.okta_http_client.sleep"
            ) as mock_sleep:
                mock_request.side_effect = [mock_response_429, mock_response_200]
                client_with_injection.list_applications()

        # Should use Retry-After value (5 seconds)
        mock_sleep.assert_called_once_with(5.0)

    def test_max_retries_exceeded(self, client_with_injection, mock_oauth2_exceptions):
        """Should fail after max retries."""
        mock_response_503 = MagicMock()
        mock_response_503.ok = False
        mock_response_503.status_code = 503
        mock_response_503.headers = {}

        with patch("requests.request") as mock_request:
            with patch("fides.api.service.connectors.okta_http_client.sleep"):
                mock_request.return_value = mock_response_503
                with pytest.raises(ConnectionException) as exc_info:
                    client_with_injection.list_applications()

        assert "status 503" in str(exc_info.value)
        # Should try DEFAULT_RETRY_COUNT + 1 times
        assert mock_request.call_count == DEFAULT_RETRY_COUNT + 1


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_rate_limiter_called(
        self, mock_oauth_client_and_dpop_key, mock_oauth2_exceptions
    ):
        """Rate limiter should be called before requests."""
        mock_oauth_client, mock_dpop_key = mock_oauth_client_and_dpop_key
        client = OktaHttpClient(
            org_url=TEST_ORG_URL,
            client_id=TEST_CLIENT_ID,
            private_key=TEST_PRIVATE_KEY_STR,
            rate_limit_per_minute=100,
            oauth_client=mock_oauth_client,
            dpop_key=mock_dpop_key,
        )

        mock_token = MagicMock(spec=AuthBase)
        mock_token.expires_at = datetime.utcnow().timestamp() + 3600
        mock_oauth_client.client_credentials.return_value = mock_token

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.headers = {}

        with patch("requests.request", return_value=mock_response):
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

    def test_rate_limiting_disabled_when_none(
        self, mock_oauth_client_and_dpop_key, mock_oauth2_exceptions
    ):
        """Rate limiter should not be called when rate_limit_per_minute is None."""
        mock_oauth_client, mock_dpop_key = mock_oauth_client_and_dpop_key
        client = OktaHttpClient(
            org_url=TEST_ORG_URL,
            client_id=TEST_CLIENT_ID,
            private_key=TEST_PRIVATE_KEY_STR,
            rate_limit_per_minute=None,
            oauth_client=mock_oauth_client,
            dpop_key=mock_dpop_key,
        )

        mock_token = MagicMock(spec=AuthBase)
        mock_token.expires_at = datetime.utcnow().timestamp() + 3600
        mock_oauth_client.client_credentials.return_value = mock_token

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.headers = {}

        with patch("requests.request", return_value=mock_response):
            with patch(
                "fides.api.service.connectors.okta_http_client.RateLimiter"
            ) as mock_limiter_class:
                client.list_applications()

        # RateLimiter should not have been instantiated
        mock_limiter_class.assert_not_called()

    def test_build_rate_limit_requests(self, mock_oauth_client_and_dpop_key):
        """_build_rate_limit_requests should return correct configuration."""
        mock_oauth_client, mock_dpop_key = mock_oauth_client_and_dpop_key
        client = OktaHttpClient(
            org_url=TEST_ORG_URL,
            client_id=TEST_CLIENT_ID,
            private_key=TEST_PRIVATE_KEY_STR,
            rate_limit_per_minute=250,
            oauth_client=mock_oauth_client,
            dpop_key=mock_dpop_key,
        )

        requests = client._build_rate_limit_requests()
        assert len(requests) == 1
        assert requests[0].key == f"okta:{TEST_ORG_URL}"
        assert requests[0].rate_limit == 250


class TestRetryAfterParsing:
    """Tests for _get_retry_after helper function."""

    def test_retry_after_numeric(self):
        """Should parse numeric Retry-After header."""
        response = MagicMock()
        response.headers = {"Retry-After": "30"}
        assert _get_retry_after(response) == 30.0

    def test_retry_after_not_present(self):
        """Should return None if no Retry-After header."""
        response = MagicMock()
        response.headers = {}
        assert _get_retry_after(response) is None

    def test_retry_after_max_cap(self):
        """Should cap Retry-After at max value."""
        response = MagicMock()
        response.headers = {"Retry-After": "600"}  # 10 minutes
        result = _get_retry_after(response)
        assert result == 300  # Max is 300 seconds

    def test_retry_after_whitespace(self):
        """Should handle whitespace in numeric value."""
        response = MagicMock()
        response.headers = {"Retry-After": "  45  "}
        assert _get_retry_after(response) == 45.0


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
