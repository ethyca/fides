"""
Google Cloud Service Account Authentication Strategy.

Authenticates HTTP requests using Google Cloud Service Account credentials
by generating OAuth2 access tokens from the service account's private key.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger
from requests import PreparedRequest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import FidesopsException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.saas.strategy_configuration import (
    GoogleCloudServiceAccountConfiguration,
    StrategyConfiguration,
)
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.util.logger import Pii

# Required fields in a Google Cloud service account JSON key file
REQUIRED_KEYFILE_FIELDS = [
    "type",
    "project_id",
    "private_key",
    "client_email",
    "token_uri",
]

# Default OAuth2 scopes for Google Cloud Platform APIs
DEFAULT_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

# Token refresh buffer in seconds (refresh 10 minutes before expiration)
TOKEN_REFRESH_BUFFER_SECONDS = 600

# Timeout for token refresh requests in seconds
TOKEN_REFRESH_TIMEOUT_SECONDS = 30


class GoogleCloudServiceAccountAuthenticationStrategy(AuthenticationStrategy):
    """
    Authenticates HTTP requests using a Google Cloud Service Account.

    This strategy uses the service account credentials (keyfile_creds) stored
    in connection secrets to generate OAuth2 access tokens. The tokens are
    cached and automatically refreshed when close to expiration.

    The service account key JSON must be provided in the connection config
    secrets under the key 'keyfile_creds'.

    Example SaaS config authentication block:
    ```yaml
    authentication:
      strategy: google_cloud_service_account
      configuration:
        scopes:
          - https://www.googleapis.com/auth/spreadsheets
    ```
    """

    name = "google_cloud_service_account"
    configuration_model = GoogleCloudServiceAccountConfiguration

    def __init__(self, configuration: GoogleCloudServiceAccountConfiguration):
        self.scopes: List[str] = configuration.scopes or DEFAULT_SCOPES

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """
        Add Google Cloud Service Account authentication to the request.
        """
        access_token = self._get_access_token(connection_config)
        request.headers["Authorization"] = f"Bearer {access_token}"
        return request

    def _get_access_token(self, connection_config: ConnectionConfig) -> str:
        """
        Get a valid access token, refreshing if necessary.

        Checks for a cached token in connection secrets. If the token exists
        and is not close to expiration, returns it. Otherwise, generates a
        new token using the service account credentials.
        """
        secrets = connection_config.secrets
        if not secrets:
            raise FidesopsException(
                "Secrets are not configured for this connector. "
                "Secrets must be configured to use Google Cloud Service Account authentication."
            )

        keyfile_creds = secrets.get("keyfile_creds")
        if not keyfile_creds:
            raise FidesopsException(
                "Missing 'keyfile_creds' in connection secrets. "
                "Service account key JSON is required for Google Cloud authentication."
            )

        # Validate keyfile structure before attempting to use it
        self._validate_keyfile_creds(keyfile_creds)

        # Check for cached token
        cached_token = secrets.get("google_cloud_access_token")
        expires_at = secrets.get("google_cloud_token_expires_at")

        if cached_token and expires_at:
            if not self._is_close_to_expiration(expires_at, connection_config):
                return cached_token

        # Generate new token
        return self._refresh_access_token(keyfile_creds, connection_config)

    def _validate_keyfile_creds(self, keyfile_creds: Dict[str, Any]) -> None:
        """
        Validate that the keyfile credentials contain all required fields.

        Raises FidesopsException with a clear message if validation fails.
        """
        # Check credential type
        cred_type = keyfile_creds.get("type")
        if cred_type != "service_account":
            raise FidesopsException(
                f"Invalid Google Cloud credential type: expected 'service_account', "
                f"got '{cred_type}'. Ensure you are using a service account key, "
                "not another credential type."
            )

        # Check for required fields
        missing_fields = [
            field for field in REQUIRED_KEYFILE_FIELDS if not keyfile_creds.get(field)
        ]
        if missing_fields:
            raise FidesopsException(
                f"Service account key is missing required fields: {', '.join(missing_fields)}. "
                "Please provide a complete service account key JSON file."
            )

    def _is_close_to_expiration(
        self, expires_at: int, connection_config: ConnectionConfig
    ) -> bool:
        """
        Check if the access token is close to expiration.

        Returns True if the token will expire within TOKEN_REFRESH_BUFFER_SECONDS.
        """
        if expires_at is None:
            logger.info(
                "No expiration time found for Google Cloud token for {}, will refresh",
                connection_config.key,
            )
            return True

        buffer_time = datetime.utcnow() + timedelta(seconds=TOKEN_REFRESH_BUFFER_SECONDS)
        return expires_at < buffer_time.timestamp()

    def _refresh_access_token(
        self,
        keyfile_creds: Dict[str, Any],
        connection_config: ConnectionConfig,
    ) -> str:
        """
        Generate a new OAuth2 access token from service account credentials.

        Uses Google's service account JWT flow to obtain a short-lived access token.
        The token and its expiration time are stored in connection secrets for caching.
        """
        # Import Google auth libraries here to avoid import errors if not installed
        try:
            from google.auth.exceptions import GoogleAuthError, TransportError
            from google.auth.transport.requests import Request
            from google.oauth2 import service_account
        except ImportError as exc:
            raise FidesopsException(
                "Google Cloud authentication requires the 'google-auth' library. "
                "Please ensure it is installed."
            ) from exc

        logger.info(
            "Generating new Google Cloud access token for {}",
            connection_config.key,
        )

        try:
            credentials = service_account.Credentials.from_service_account_info(
                dict(keyfile_creds),
                scopes=self.scopes,
            )

            # Refresh credentials to obtain access token
            # Using a timeout to prevent hanging on network issues
            request = Request()
            credentials.refresh(request)

            access_token = credentials.token
            if not access_token:
                raise FidesopsException(
                    "Failed to obtain access token from Google Cloud. "
                    "The token response was empty."
                )

            # Calculate expiration time
            # Google access tokens typically expire in 3600 seconds (1 hour)
            # Use the expiry from credentials if available, otherwise default to 1 hour
            if credentials.expiry:
                expires_at = int(credentials.expiry.timestamp())
            else:
                expires_at = int(
                    (datetime.utcnow() + timedelta(hours=1)).timestamp()
                )

            # Store token and expiration in connection secrets
            self._store_token(connection_config, access_token, expires_at)

            logger.info(
                "Successfully generated Google Cloud access token for {}",
                connection_config.key,
            )

            return access_token

        except TransportError as exc:
            logger.error(
                "Network error connecting to Google OAuth2 endpoint for {}: {}",
                connection_config.key,
                Pii(str(exc)),
            )
            raise FidesopsException(
                "Network error connecting to Google OAuth2 endpoint. "
                "Ensure outbound access to oauth2.googleapis.com is allowed."
            ) from exc

        except GoogleAuthError as exc:
            logger.error(
                "Google authentication error for {}: {}",
                connection_config.key,
                Pii(str(exc)),
            )
            raise FidesopsException(
                "Failed to authenticate with Google Cloud. "
                "Check that the service account key is valid and has the required permissions."
            ) from exc

        except Exception as exc:
            logger.error(
                "Unexpected error generating Google Cloud access token for {}: {}",
                connection_config.key,
                Pii(str(exc)),
            )
            raise FidesopsException(
                f"Failed to generate Google Cloud access token: {type(exc).__name__}"
            ) from exc

    def _store_token(
        self,
        connection_config: ConnectionConfig,
        access_token: str,
        expires_at: int,
    ) -> None:
        """
        Store the access token and expiration time in connection secrets.

        Uses the database session from the connection config to persist changes.
        """
        db: Optional[Session] = Session.object_session(connection_config)
        if db is None:
            logger.warning(
                "Unable to cache Google Cloud access token for {} - no database session available",
                connection_config.key,
            )
            return

        updated_secrets = {
            **(connection_config.secrets or {}),
            "google_cloud_access_token": access_token,
            "google_cloud_token_expires_at": expires_at,
        }

        connection_config.update(db, data={"secrets": updated_secrets})
        logger.debug(
            "Cached Google Cloud access token for {} (expires at {})",
            connection_config.key,
            datetime.fromtimestamp(expires_at).isoformat(),
        )

    @staticmethod
    def get_configuration_model() -> StrategyConfiguration:
        """Return the configuration model for this strategy."""
        return GoogleCloudServiceAccountConfiguration  # type: ignore
