import json
import sys
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
def mock_oauth_client_and_dpop_key():
    return MagicMock(), MagicMock()


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
        client_with_injection._oauth_client.client_credentials.return_value = mock_token
        return mock_token

    def test_list_applications_single_page(self, client_with_injection, mock_token):
        mock_apps = [{"id": "app1"}, {"id": "app2"}]
        with patch("requests.get") as mock_get:
            mock_response = MagicMock(headers={}, status_code=200)
            mock_response.json.return_value = mock_apps
            mock_get.return_value = mock_response

            apps, next_cursor = client_with_injection.list_applications()

            assert apps == mock_apps
            assert next_cursor is None
            mock_get.assert_called_once_with(
                f"{TEST_ORG_URL}/api/v1/apps",
                params={"limit": DEFAULT_API_LIMIT},
                auth=mock_token,
                timeout=DEFAULT_REQUEST_TIMEOUT,
            )

    def test_list_applications_with_pagination(self, client_with_injection, mock_token):
        link_header = f'<{TEST_ORG_URL}/api/v1/apps?after=cursor123>; rel="next"'
        with patch("requests.get") as mock_get:
            mock_response = MagicMock(headers={"Link": link_header}, status_code=200)
            mock_response.json.return_value = [{"id": "app1"}]
            mock_get.return_value = mock_response

            apps, next_cursor = client_with_injection.list_applications(limit=1)

            assert apps == [{"id": "app1"}]
            assert next_cursor == "cursor123"
            mock_get.assert_called_once_with(
                f"{TEST_ORG_URL}/api/v1/apps",
                params={"limit": 1},
                auth=mock_token,
                timeout=DEFAULT_REQUEST_TIMEOUT,
            )

    def test_list_applications_oauth_error(self, client_with_injection):
        class StubOAuth2Error(Exception):
            pass

        exceptions_module = ModuleType("requests_oauth2client.exceptions")
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
            client_with_injection._oauth_client.client_credentials.side_effect = (
                StubOAuth2Error("invalid_client")
            )
            with pytest.raises(ConnectionException) as exc_info:
                client_with_injection.list_applications()
        assert "OAuth2 token acquisition failed" in str(exc_info.value)

    def test_list_applications_http_error(self, client_with_injection, mock_token):
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Network error")
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

    def test_parse_jwk_accepts_dict_without_d(self):
        # _parse_jwk no longer validates 'd' - that's done by OktaSchema
        # This tests that dict passthrough works regardless of content
        public_jwk = RSA_JWK.copy()
        del public_jwk["d"]
        parsed = OktaHttpClient._parse_jwk(public_jwk)
        assert parsed["kid"] == RSA_JWK["kid"]

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
