from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
from requests import Request

from fides.api.common_exceptions import FidesopsException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.service.authentication.authentication_strategy_google_cloud_service_account import (
    DEFAULT_SCOPES,
    DEFAULT_TOKEN_URI,
    TOKEN_REFRESH_BUFFER_SECONDS,
    GoogleCloudServiceAccountAuthenticationStrategy,
)


@pytest.fixture
def valid_secrets():
    """Valid service account credentials as individual fields."""
    return {
        "project_id": "test-project-123",
        "client_email": "test-sa@test-project-123.iam.gserviceaccount.com",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIItest\n-----END PRIVATE KEY-----\n",
    }


@pytest.fixture
def google_cloud_connection_config(valid_secrets):
    """Connection config with valid Google Cloud service account credentials."""
    return ConnectionConfig(
        key="google_cloud_test_connector",
        secrets=valid_secrets,
    )


@pytest.fixture
def google_cloud_configuration():
    """Default configuration for Google Cloud Service Account strategy."""
    return {}


@pytest.fixture
def google_cloud_configuration_with_scopes():
    """Configuration with custom scopes."""
    return {
        "scopes": [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
    }


@pytest.fixture
def connection_config_with_optional_fields():
    """Connection config with optional fields included."""
    return ConnectionConfig(
        key="google_cloud_optional_fields_connector",
        secrets={
            "project_id": "test-project-123",
            "client_email": "test-sa@test-project-123.iam.gserviceaccount.com",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIItest\n-----END PRIVATE KEY-----\n",
            "private_key_id": "key-id-456",
            "client_id": "123456789",
            "token_uri": "https://custom.googleapis.com/token",
        },
    )


class TestStrategyConfiguration:
    """Tests for strategy configuration and initialization."""

    def test_strategy_registered(self):
        """Test that the strategy is registered in the factory."""
        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", {}
        )
        assert isinstance(strategy, GoogleCloudServiceAccountAuthenticationStrategy)

    def test_default_scopes(self, google_cloud_configuration):
        """Test that default scopes are used when not specified."""
        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )
        assert strategy.scopes == DEFAULT_SCOPES

    def test_custom_scopes(self, google_cloud_configuration_with_scopes):
        """Test that custom scopes override defaults."""
        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration_with_scopes
        )
        assert strategy.scopes == google_cloud_configuration_with_scopes["scopes"]


class TestKeyfileValidation:
    """Tests for service account keyfile validation."""

    def test_missing_secrets(self, google_cloud_configuration):
        """Test error when connection config has no secrets."""
        connection_config = ConnectionConfig(
            key="test_connector",
            secrets=None,
        )
        req = Request(method="GET", url="https://example.com").prepare()

        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        with pytest.raises(FidesopsException) as exc:
            strategy.add_authentication(req, connection_config)
        assert "Secrets are not configured" in str(exc.value)

    def test_missing_project_id(self, google_cloud_configuration):
        """Test error when project_id is missing."""
        connection_config = ConnectionConfig(
            key="test_connector",
            secrets={
                "client_email": "test@test.iam.gserviceaccount.com",
                "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            },
        )
        req = Request(method="GET", url="https://example.com").prepare()

        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        with pytest.raises(FidesopsException) as exc:
            strategy.add_authentication(req, connection_config)
        assert "project_id" in str(exc.value)

    def test_missing_client_email(self, google_cloud_configuration):
        """Test error when client_email is missing."""
        connection_config = ConnectionConfig(
            key="test_connector",
            secrets={
                "project_id": "test-project",
                "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            },
        )
        req = Request(method="GET", url="https://example.com").prepare()

        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        with pytest.raises(FidesopsException) as exc:
            strategy.add_authentication(req, connection_config)
        assert "client_email" in str(exc.value)

    def test_missing_private_key(self, google_cloud_configuration):
        """Test error when private_key is missing."""
        connection_config = ConnectionConfig(
            key="test_connector",
            secrets={
                "project_id": "test-project",
                "client_email": "test@test.iam.gserviceaccount.com",
            },
        )
        req = Request(method="GET", url="https://example.com").prepare()

        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        with pytest.raises(FidesopsException) as exc:
            strategy.add_authentication(req, connection_config)
        assert "private_key" in str(exc.value)


class TestCredentialsConstruction:
    """Tests for building credentials from individual fields."""

    def test_constructs_keyfile_from_fields(
        self,
        google_cloud_configuration,
        google_cloud_connection_config,
    ):
        """Test that individual fields are correctly assembled into credentials."""
        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        # Access the internal method to verify keyfile construction
        keyfile_creds = strategy._get_keyfile_creds(
            google_cloud_connection_config.secrets
        )

        assert keyfile_creds["type"] == "service_account"
        assert keyfile_creds["project_id"] == "test-project-123"
        assert (
            keyfile_creds["client_email"]
            == "test-sa@test-project-123.iam.gserviceaccount.com"
        )
        assert (
            keyfile_creds["private_key"]
            == "-----BEGIN PRIVATE KEY-----\nMIItest\n-----END PRIVATE KEY-----\n"
        )
        assert keyfile_creds["token_uri"] == DEFAULT_TOKEN_URI

    def test_custom_token_uri(
        self,
        google_cloud_configuration,
    ):
        """Test that custom token_uri overrides the default."""
        custom_token_uri = "https://custom.googleapis.com/token"
        connection_config = ConnectionConfig(
            key="test_connector",
            secrets={
                "project_id": "test-project",
                "client_email": "test@test.iam.gserviceaccount.com",
                "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
                "token_uri": custom_token_uri,
            },
        )

        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        keyfile_creds = strategy._get_keyfile_creds(connection_config.secrets)
        assert keyfile_creds["token_uri"] == custom_token_uri

    def test_includes_optional_fields(
        self,
        google_cloud_configuration,
        connection_config_with_optional_fields,
    ):
        """Test that optional fields are included when provided."""
        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        keyfile_creds = strategy._get_keyfile_creds(
            connection_config_with_optional_fields.secrets
        )

        assert keyfile_creds["private_key_id"] == "key-id-456"
        assert keyfile_creds["client_id"] == "123456789"
        assert keyfile_creds["token_uri"] == "https://custom.googleapis.com/token"


class TestPrivateKeyNormalization:
    """Tests for private key format normalization."""

    def test_normalizes_escaped_newlines(self, google_cloud_configuration):
        """Test that escaped \\n are converted to actual newlines."""
        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        # Key with escaped newlines (as often pasted from JSON)
        escaped_key = (
            "-----BEGIN PRIVATE KEY-----\\nMIItest\\n-----END PRIVATE KEY-----\\n"
        )
        normalized = strategy._normalize_private_key(escaped_key)

        assert "\\n" not in normalized
        assert "\n" in normalized
        assert normalized.startswith("-----BEGIN PRIVATE KEY-----\n")

    def test_adds_trailing_newline(self, google_cloud_configuration):
        """Test that missing trailing newline is added."""
        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        key_without_newline = (
            "-----BEGIN PRIVATE KEY-----\nMIItest\n-----END PRIVATE KEY-----"
        )
        normalized = strategy._normalize_private_key(key_without_newline)

        assert normalized.endswith("\n")

    def test_preserves_valid_key(self, google_cloud_configuration):
        """Test that already valid keys are preserved."""
        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        valid_key = "-----BEGIN PRIVATE KEY-----\nMIItest\n-----END PRIVATE KEY-----\n"
        normalized = strategy._normalize_private_key(valid_key)

        assert normalized == valid_key


class TestTokenCaching:
    """Tests for access token caching behavior."""

    def test_uses_cached_token_when_valid(
        self,
        google_cloud_configuration,
        valid_secrets,
    ):
        """Test that a valid cached token is reused."""
        # Set expiration far in the future
        future_expiry = int(
            (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
        )
        connection_config = ConnectionConfig(
            key="test_connector",
            secrets={
                **valid_secrets,
                "google_cloud_access_token": "cached_token_123",
                "google_cloud_token_expires_at": future_expiry,
            },
        )
        req = Request(method="GET", url="https://example.com").prepare()

        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        # Should use cached token without calling Google
        authenticated_request = strategy.add_authentication(req, connection_config)
        assert (
            authenticated_request.headers["Authorization"] == "Bearer cached_token_123"
        )

    @patch(
        "fides.api.service.authentication.authentication_strategy_google_cloud_service_account.GoogleCloudServiceAccountAuthenticationStrategy._refresh_access_token"
    )
    def test_refreshes_token_when_close_to_expiration(
        self,
        mock_refresh: Mock,
        google_cloud_configuration,
        valid_secrets,
    ):
        """Test that token is refreshed when close to expiration."""
        mock_refresh.return_value = "new_token_456"

        # Set expiration within the refresh buffer
        close_expiry = int(
            (
                datetime.now(timezone.utc)
                + timedelta(seconds=TOKEN_REFRESH_BUFFER_SECONDS - 60)
            ).timestamp()
        )
        connection_config = ConnectionConfig(
            key="test_connector",
            secrets={
                **valid_secrets,
                "google_cloud_access_token": "old_token",
                "google_cloud_token_expires_at": close_expiry,
            },
        )
        req = Request(method="GET", url="https://example.com").prepare()

        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        authenticated_request = strategy.add_authentication(req, connection_config)
        assert authenticated_request.headers["Authorization"] == "Bearer new_token_456"
        mock_refresh.assert_called_once()

    @patch(
        "fides.api.service.authentication.authentication_strategy_google_cloud_service_account.GoogleCloudServiceAccountAuthenticationStrategy._refresh_access_token"
    )
    def test_refreshes_token_when_expired(
        self,
        mock_refresh: Mock,
        google_cloud_configuration,
        valid_secrets,
    ):
        """Test that token is refreshed when already expired."""
        mock_refresh.return_value = "new_token_789"

        # Set expiration in the past
        past_expiry = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        connection_config = ConnectionConfig(
            key="test_connector",
            secrets={
                **valid_secrets,
                "google_cloud_access_token": "expired_token",
                "google_cloud_token_expires_at": past_expiry,
            },
        )
        req = Request(method="GET", url="https://example.com").prepare()

        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        authenticated_request = strategy.add_authentication(req, connection_config)
        assert authenticated_request.headers["Authorization"] == "Bearer new_token_789"
        mock_refresh.assert_called_once()

    @patch(
        "fides.api.service.authentication.authentication_strategy_google_cloud_service_account.GoogleCloudServiceAccountAuthenticationStrategy._refresh_access_token"
    )
    def test_refreshes_token_when_no_cached_token(
        self,
        mock_refresh: Mock,
        google_cloud_configuration,
        google_cloud_connection_config,
    ):
        """Test that token is fetched when no cached token exists."""
        mock_refresh.return_value = "fresh_token"

        req = Request(method="GET", url="https://example.com").prepare()

        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        authenticated_request = strategy.add_authentication(
            req, google_cloud_connection_config
        )
        assert authenticated_request.headers["Authorization"] == "Bearer fresh_token"
        mock_refresh.assert_called_once()


class TestTokenGeneration:
    """Tests for OAuth2 access token generation from service account."""

    @patch("fides.api.models.connectionconfig.ConnectionConfig.update")
    @patch("google.oauth2.service_account.Credentials")
    def test_successful_token_generation(
        self,
        mock_credentials_class: Mock,
        mock_update: Mock,
        google_cloud_configuration,
        google_cloud_connection_config,
    ):
        """Test successful token generation using mocked Google auth."""
        # Mock the credentials instance
        mock_credentials = MagicMock()
        mock_credentials.token = "generated_access_token"
        mock_credentials.expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_credentials_class.from_service_account_info.return_value = mock_credentials

        req = Request(method="GET", url="https://example.com").prepare()

        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        # Trigger _refresh_access_token by not having a cached token
        authenticated_request = strategy.add_authentication(
            req, google_cloud_connection_config
        )

        assert (
            authenticated_request.headers["Authorization"]
            == "Bearer generated_access_token"
        )
        mock_credentials_class.from_service_account_info.assert_called_once()

    @patch("google.oauth2.service_account.Credentials")
    def test_network_error_handling(
        self,
        mock_credentials_class: Mock,
        google_cloud_configuration,
        google_cloud_connection_config,
    ):
        """Test proper error handling for network failures."""
        from google.auth.exceptions import TransportError

        # Make the credentials refresh raise a TransportError
        mock_credentials = MagicMock()
        mock_credentials.refresh.side_effect = TransportError("Connection refused")
        mock_credentials_class.from_service_account_info.return_value = mock_credentials

        req = Request(method="GET", url="https://example.com").prepare()

        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        with pytest.raises(FidesopsException) as exc:
            strategy.add_authentication(req, google_cloud_connection_config)

        assert "Network error" in str(exc.value) or "oauth2.googleapis.com" in str(
            exc.value
        )

    @patch("google.oauth2.service_account.Credentials")
    def test_auth_error_handling(
        self,
        mock_credentials_class: Mock,
        google_cloud_configuration,
        google_cloud_connection_config,
    ):
        """Test proper error handling for authentication failures."""
        from google.auth.exceptions import GoogleAuthError

        # Make the credentials refresh raise a GoogleAuthError
        mock_credentials = MagicMock()
        mock_credentials.refresh.side_effect = GoogleAuthError("Invalid credentials")
        mock_credentials_class.from_service_account_info.return_value = mock_credentials

        req = Request(method="GET", url="https://example.com").prepare()

        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        with pytest.raises(FidesopsException) as exc:
            strategy.add_authentication(req, google_cloud_connection_config)

        assert "Failed to authenticate" in str(exc.value) or "Google Cloud" in str(
            exc.value
        )


class TestAddAuthentication:
    """Tests for the add_authentication method."""

    def test_preserves_existing_headers(
        self,
        google_cloud_configuration,
        valid_secrets,
    ):
        """Test that existing request headers are preserved."""
        future_expiry = int(
            (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
        )
        connection_config = ConnectionConfig(
            key="test_connector",
            secrets={
                **valid_secrets,
                "google_cloud_access_token": "test_token",
                "google_cloud_token_expires_at": future_expiry,
            },
        )
        req = Request(
            method="GET",
            url="https://example.com",
            headers={"Content-Type": "application/json", "X-Custom-Header": "value"},
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy(
            "google_cloud_service_account", google_cloud_configuration
        )

        authenticated_request = strategy.add_authentication(req, connection_config)

        assert authenticated_request.headers["Content-Type"] == "application/json"
        assert authenticated_request.headers["X-Custom-Header"] == "value"
        assert "Authorization" in authenticated_request.headers
