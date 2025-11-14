from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, Optional

import requests
from loguru import logger
from requests.auth import HTTPBasicAuth
from sqlalchemy.orm import Session

from fides.api.common_exceptions import ConnectionException, OAuth2TokenException
from fides.api.models.connectionconfig import ConnectionConfig


class OktaOAuth2Client:
    """
    Lightweight OAuth2 Client Credentials helper for Okta.

    This class encapsulates token acquisition, caching, and persistence in the
    `ConnectionConfig` secrets for the Okta connector/worker use case.
    """

    TOKEN_PATH = "/oauth2/v1/token"
    DEFAULT_SCOPE = "okta.apps.read"
    DEFAULT_EXPIRATION_SECONDS = 3600
    EXPIRATION_BUFFER_SECONDS = 300

    @staticmethod
    def _default_clock() -> datetime:
        return datetime.now(timezone.utc)

    def __init__(
        self,
        connection_config: ConnectionConfig,
        *,
        scope: Optional[str] = None,
        clock: Callable[[], datetime] = None,
    ) -> None:
        self.connection_config = connection_config
        self.scope = scope or self.DEFAULT_SCOPE
        self.clock = clock or self._default_clock

    def get_access_token(self, db: Optional[Session] = None) -> str:
        """
        Retrieve a valid OAuth2 access token for Okta.
        Returns a cached token when still valid or requests a new one as needed.
        """
        self._validate_required_secrets(self.connection_config)

        secrets = self.connection_config.secrets or {}
        access_token: Optional[str] = secrets.get("access_token")
        expires_at: Optional[int] = secrets.get("expires_at")

        if access_token and self._token_is_valid(expires_at):
            return access_token

        token_response = self._request_new_token()
        return self._persist_token(token_response, db)

    @staticmethod
    def _validate_required_secrets(connection_config: ConnectionConfig) -> None:
        secrets = connection_config.secrets or {}
        missing = [
            secret_name
            for secret_name in ("org_url", "client_id", "client_secret")
            if not secrets.get(secret_name)
        ]
        if missing:
            raise ConnectionException(
                "Okta connection configuration is missing required OAuth2 secrets: "
                + ", ".join(missing)
            )

    def _token_is_valid(self, expires_at: Optional[int]) -> bool:
        if not expires_at:
            return False

        buffer_time = self.clock() + timedelta(seconds=self.EXPIRATION_BUFFER_SECONDS)
        return expires_at > int(buffer_time.timestamp())

    def _token_endpoint(self) -> str:
        org_url: str = self.connection_config.secrets.get("org_url")  # type: ignore
        # Ensure only a single slash between org_url and the token path
        return org_url.rstrip("/") + self.TOKEN_PATH

    def _request_new_token(self) -> Dict[str, str]:
        secrets = self.connection_config.secrets or {}
        client_id: str = secrets.get("client_id")  # type: ignore
        client_secret: str = secrets.get("client_secret")  # type: ignore

        data = {
            "grant_type": "client_credentials",
            "scope": self.scope,
        }

        try:
            response = requests.post(
                self._token_endpoint(),
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                auth=HTTPBasicAuth(client_id, client_secret),
                timeout=30,
            )
        except requests.exceptions.RequestException as exc:  # pragma: no cover
            logger.error("Error requesting Okta OAuth2 access token: {}", exc)
            raise OAuth2TokenException(
                f"Error occurred during the access token request for {self.connection_config.key}: {exc}"
            ) from exc

        if response.status_code != 200:
            logger.error(
                "Okta OAuth2 token request failed with status {}: {}",
                response.status_code,
                response.text,
            )
            raise OAuth2TokenException(
                f"Unable to retrieve token for {self.connection_config.key}. "
                f"Status code: {response.status_code}"
            )

        try:
            return response.json()
        except ValueError as exc:
            logger.error("Invalid JSON in Okta OAuth2 token response: {}", exc)
            raise OAuth2TokenException(
                f"Invalid JSON response retrieving token for {self.connection_config.key}: {exc}"
            ) from exc

    def _persist_token(
        self, token_response: Dict[str, str], db: Optional[Session]
    ) -> str:
        access_token = token_response.get("access_token")
        if not access_token:
            logger.error("Okta OAuth2 token response missing access_token: {}", token_response)
            raise OAuth2TokenException(
                f"Unable to retrieve token for {self.connection_config.key} (missing access_token)."
            )

        expires_in = token_response.get("expires_in") or self.DEFAULT_EXPIRATION_SECONDS
        expires_at = int(self.clock().timestamp()) + int(expires_in)

        updated_secrets = {
            **(self.connection_config.secrets or {}),
            "access_token": access_token,
            "expires_at": expires_at,
        }

        db = db or Session.object_session(self.connection_config)
        if db is None:
            logger.warning(
                "Okta OAuth2 token persistence without DB session for {}", self.connection_config.key
            )

        self.connection_config.update(db, data={"secrets": updated_secrets})
        return access_token
