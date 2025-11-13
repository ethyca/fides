from datetime import datetime, timedelta
from typing import Dict, Optional
from unittest import mock
from unittest.mock import Mock

import pytest

from fides.api.common_exceptions import ConnectionException, OAuth2TokenException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.service.connectors.okta_oauth2_client import OktaOAuth2Client


class DummyConnectionConfig:
    """
    Lightweight stand-in for ConnectionConfig for unit testing.
    """

    def __init__(self, secrets: Optional[Dict[str, Optional[str]]] = None) -> None:
        self.secrets = secrets or {}
        self.key = "okta_connection"
        self.update = Mock()


@pytest.fixture
def connection_config() -> ConnectionConfig:
    return DummyConnectionConfig(
        secrets={
            "org_url": "https://example.okta.com",
            "client_id": "client-id",
            "client_secret": "client-secret",
            "access_token": "cached-token",
            "expires_at": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        }
    )  # type: ignore


@pytest.fixture
def oauth_client(connection_config: ConnectionConfig) -> OktaOAuth2Client:
    return OktaOAuth2Client(connection_config)


class TestGetAccessToken:
    def test_returns_cached_token_when_valid(self, oauth_client: OktaOAuth2Client) -> None:
        token = oauth_client.get_access_token()
        assert token == "cached-token"

    def test_requests_new_token_when_expired(self, connection_config: ConnectionConfig) -> None:
        connection_config.secrets["expires_at"] = int(
            (datetime.utcnow() - timedelta(seconds=1)).timestamp()
        )

        with mock.patch("fides.api.service.connectors.okta_oauth2_client.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "fresh-token",
                "expires_in": 600,
            }
            mock_post.return_value = mock_response

            oauth_client = OktaOAuth2Client(connection_config)
            token = oauth_client.get_access_token()
            assert token == "fresh-token"
            connection_config.update.assert_called_once()

    def test_requests_new_token_when_missing(self, connection_config: ConnectionConfig) -> None:
        connection_config.secrets["access_token"] = None
        connection_config.secrets["expires_at"] = None

        with mock.patch("fides.api.service.connectors.okta_oauth2_client.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"access_token": "fresh-token"}
            mock_post.return_value = mock_response

            oauth_client = OktaOAuth2Client(connection_config)
            token = oauth_client.get_access_token()
            assert token == "fresh-token"

    def test_handles_missing_required_secrets(self) -> None:
        connection_config = DummyConnectionConfig(
            secrets={
                "org_url": "https://example.okta.com",
                "client_id": "client-id",
            }
        )  # type: ignore
        oauth_client = OktaOAuth2Client(connection_config)  # type: ignore

        with pytest.raises(ConnectionException) as exc:
            oauth_client.get_access_token()

        assert "missing required OAuth2 secrets" in str(exc.value)

    def test_raises_error_on_http_failure(self, connection_config: ConnectionConfig) -> None:
        connection_config.secrets["access_token"] = None
        connection_config.secrets["expires_at"] = None

        with mock.patch(
            "fides.api.service.connectors.okta_oauth2_client.requests.post",
            side_effect=Exception("boom"),
        ):
            oauth_client = OktaOAuth2Client(connection_config)
            with pytest.raises(OAuth2TokenException):
                oauth_client.get_access_token()

    def test_raises_error_when_response_missing_access_token(
        self, connection_config: ConnectionConfig
    ) -> None:
        connection_config.secrets["access_token"] = None
        connection_config.secrets["expires_at"] = None

        with mock.patch("fides.api.service.connectors.okta_oauth2_client.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"not_access_token": "oops"}
            mock_post.return_value = mock_response

            oauth_client = OktaOAuth2Client(connection_config)
            with pytest.raises(OAuth2TokenException):
                oauth_client.get_access_token()

    def test_raises_error_when_status_not_200(self, connection_config: ConnectionConfig) -> None:
        connection_config.secrets["access_token"] = None
        connection_config.secrets["expires_at"] = None

        with mock.patch("fides.api.service.connectors.okta_oauth2_client.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_post.return_value = mock_response

            oauth_client = OktaOAuth2Client(connection_config)
            with pytest.raises(OAuth2TokenException):
                oauth_client.get_access_token()
