from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from google.auth.exceptions import GoogleAuthError, TransportError
from google.auth.transport.requests import Request
from google.oauth2 import service_account
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

# Required fields for service account authentication
REQUIRED_FIELDS = [
    "project_id",
    "client_email",
    "private_key",
]

# Default OAuth2 scopes for Google Cloud Platform APIs
DEFAULT_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

# Default token URI for Google OAuth2
DEFAULT_TOKEN_URI = "https://oauth2.googleapis.com/token"

# Token refresh buffer in seconds (refresh 10 minutes before expiration)
TOKEN_REFRESH_BUFFER_SECONDS = 600

# Timeout for token refresh requests in seconds
TOKEN_REFRESH_TIMEOUT_SECONDS = 30


class GoogleCloudServiceAccountAuthenticationStrategy(AuthenticationStrategy):
    """
    Authenticates HTTP requests using a Google Cloud Service Account.

    This strategy uses the service account credentials stored in connection
    secrets to generate OAuth2 access tokens. The tokens are cached and
    automatically refreshed when close to expiration.

    Required connection secrets:
        - project_id: Your Google Cloud project ID
        - client_email: Service account email (e.g., my-sa@project.iam.gserviceaccount.com)
        - private_key: The RSA private key from your service account

    Optional connection secrets:
        - token_uri: OAuth2 token endpoint (defaults to https://oauth2.googleapis.com/token)
        - private_key_id: Key identifier
        - client_id: Client identifier

    Example SaaS config authentication block:
    ```yaml
    authentication:
      strategy: google_cloud_service_account
      configuration:
        scopes:
          - https://www.googleapis.com/auth/spreadsheets
    ```

    Example connector_params:
    ```yaml
    connector_params:
      - name: project_id
        label: Project ID
        description: Your Google Cloud project ID
      - name: client_email
        label: Service Account Email
        description: e.g., my-sa@my-project.iam.gserviceaccount.com
      - name: private_key
        label: Private Key
        description: The RSA private key from your service account JSON
        sensitive: True
        multiline: True
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
        """
        secrets = connection_config.secrets
        if not secrets:
            raise FidesopsException(
                "Secrets are not configured for this connector. "
                "Secrets must be configured to use Google Cloud Service Account authentication."
            )

        # Get keyfile_creds - either from full object or constructed from individual fields
        keyfile_creds = self._get_keyfile_creds(secrets)

        self._validate_keyfile_creds(keyfile_creds)

        cached_token = secrets.get("google_cloud_access_token")
        expires_at = secrets.get("google_cloud_token_expires_at")

        if cached_token and expires_at:
            if not self._is_close_to_expiration(expires_at, connection_config):
                return cached_token

        # Generate new token
        return self._refresh_access_token(keyfile_creds, connection_config)

    def _get_keyfile_creds(self, secrets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build keyfile credentials dict from individual secret fields.
        """
        project_id = secrets.get("project_id")
        client_email = secrets.get("client_email")
        private_key = secrets.get("private_key")

        # Check if we have the minimum required fields
        if not all([project_id, client_email, private_key]):
            missing = []
            if not project_id:
                missing.append("project_id")
            if not client_email:
                missing.append("client_email")
            if not private_key:
                missing.append("private_key")

            raise FidesopsException(
                f"Missing required Google Cloud credentials: {', '.join(missing)}. "
                "Please provide project_id, client_email, and private_key."
            )

        # Normalize the private key format
        # Handle common issues from copy/paste: escaped newlines, missing newlines
        normalized_private_key = self._normalize_private_key(private_key)

        # Construct keyfile_creds with smart defaults
        return {
            "type": "service_account",
            "project_id": project_id,
            "client_email": client_email,
            "private_key": normalized_private_key,
            "token_uri": secrets.get(
                "token_uri", DEFAULT_TOKEN_URI
            ),  # default Token URI is used if not provided
            # Optional fields - include if provided
            **(
                {"private_key_id": secrets["private_key_id"]}
                if secrets.get("private_key_id")
                else {}
            ),
            **({"client_id": secrets["client_id"]} if secrets.get("client_id") else {}),
            **({"auth_uri": secrets["auth_uri"]} if secrets.get("auth_uri") else {}),
            **(
                {"auth_provider_x509_cert_url": secrets["auth_provider_x509_cert_url"]}
                if secrets.get("auth_provider_x509_cert_url")
                else {}
            ),
            **(
                {"client_x509_cert_url": secrets["client_x509_cert_url"]}
                if secrets.get("client_x509_cert_url")
                else {}
            ),
        }

    def _normalize_private_key(self, private_key: str) -> str:
        """
        Normalize the private key format to handle common copy/paste issues.

        Handles:
        - Escaped newlines (\\n -> actual newlines)
        - Missing trailing newline
        - Validates basic structure
        """
        if not private_key:
            return private_key

        # Replace escaped newlines with actual newlines
        # This handles when users paste JSON-escaped keys
        normalized = private_key.replace("\\n", "\n")

        # Ensure the key ends with a newline (required by some parsers)
        if not normalized.endswith("\n"):
            normalized += "\n"

        # Validate basic structure
        if "-----BEGIN" not in normalized or "-----END" not in normalized:
            logger.warning(
                "Private key appears to be missing PEM headers. "
                "Expected '-----BEGIN PRIVATE KEY-----' and '-----END PRIVATE KEY-----'"
            )

        return normalized

    def _validate_keyfile_creds(self, keyfile_creds: Dict[str, Any]) -> None:
        """
        Validate that the keyfile credentials contain all required fields.
        """
        cred_type = keyfile_creds.get("type")
        if cred_type != "service_account":
            raise FidesopsException(
                f"Invalid Google Cloud credential type: expected 'service_account', "
                f"got '{cred_type}'."
            )

        # Validate required fields are present and non-empty
        required = ["project_id", "client_email", "private_key", "token_uri"]
        missing_fields = [field for field in required if not keyfile_creds.get(field)]
        if missing_fields:
            raise FidesopsException(
                f"Service account credentials missing required fields: {', '.join(missing_fields)}."
            )

    def _is_close_to_expiration(
        self, expires_at: int, connection_config: ConnectionConfig
    ) -> bool:
        """
        Check if the access token is close to expiration.

        Returns True if the token will expire within TOKEN_REFRESH_BUFFER_SECONDS.
        """
        buffer_time = datetime.now(timezone.utc) + timedelta(
            seconds=TOKEN_REFRESH_BUFFER_SECONDS
        )
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
            request = Request()
            credentials.refresh(request)

            access_token = credentials.token
            if not access_token:
                raise FidesopsException(
                    "Failed to obtain access token from Google Cloud. "
                    "The token response was empty."
                )

            # Calculate expiration time
            if credentials.expiry:
                expires_at = int(credentials.expiry.timestamp())
            else:
                expires_at = int(
                    (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
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

        except ValueError as exc:
            # ValueError typically indicates malformed credentials
            error_msg = str(exc)
            logger.error(
                "Invalid credential format for {}: {}",
                connection_config.key,
                Pii(error_msg),
            )

            # Provide helpful error message based on common issues
            if (
                "private_key" in error_msg.lower()
                or "Could not deserialize" in error_msg
            ):
                raise FidesopsException(
                    "Invalid private_key format. The private key must be a valid PEM-encoded "
                    "RSA private key. Ensure the key includes '-----BEGIN PRIVATE KEY-----' "
                    "and '-----END PRIVATE KEY-----' headers, and that newlines are preserved. "
                    f"Details: {error_msg}"
                ) from exc
            else:
                raise FidesopsException(
                    f"Invalid credential format: {error_msg}"
                ) from exc

        except Exception as exc:
            logger.error(
                "Unexpected error generating Google Cloud access token for {}: {}",
                connection_config.key,
                Pii(str(exc)),
            )
            raise FidesopsException(
                f"Failed to generate Google Cloud access token: {type(exc).__name__}. "
                f"Details: {str(exc)}"
            ) from exc

    def _store_token(
        self,
        connection_config: ConnectionConfig,
        access_token: str,
        expires_at: int,
    ) -> None:
        """
        Store the access token and expiration time in connection secrets.
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
