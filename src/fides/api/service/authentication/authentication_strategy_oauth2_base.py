from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import FidesopsException, OAuth2TokenException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.saas.saas_config import ClientConfig, SaaSRequest
from fides.api.schemas.saas.strategy_configuration import OAuth2BaseConfiguration
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.util.logger import Pii
from fides.api.util.saas_util import assign_placeholders, map_param_values


class OAuth2AuthenticationStrategyBase(AuthenticationStrategy):
    """
    Base class for the various OAuth2 flows. Includes common functionality
    for processing token requests and responses.
    """

    def __init__(self, configuration: OAuth2BaseConfiguration) -> None:
        self.expires_in = configuration.expires_in
        self.token_request = configuration.token_request
        self.refresh_request = configuration.refresh_request

    @property
    def _required_secrets(self) -> List[str]:
        """A list of required secrets for the given OAuth2 strategy."""
        return ["client_id", "client_secret"]

    @staticmethod
    def _close_to_expiration(
        expires_at: int, connection_config: ConnectionConfig
    ) -> bool:
        """Check if the access_token will expire in the next 10 minutes."""

        if expires_at is None:
            logger.info(
                "The expires_at value is not defined for {}, skipping token refresh",
                connection_config.key,
            )
            return False

        return expires_at < (datetime.utcnow() + timedelta(minutes=10)).timestamp()

    @staticmethod
    def _call_token_request(
        action: Literal["access", "refresh"],
        token_request: SaaSRequest,
        connection_config: ConnectionConfig,
    ) -> Dict[str, Any]:
        """
        Generates and executes the token request based on the OAuth2 config
        and connection config secrets.
        """

        logger.info("Attempting {} token request for {}", action, connection_config.key)

        # get the client config from the token request or default to the
        # protocol and host specified by the root client config (no auth)
        root_client_config = connection_config.get_saas_config().client_config  # type: ignore
        oauth_client_config = (
            token_request.client_config
            if token_request.client_config
            else ClientConfig(
                protocol=root_client_config.protocol, host=root_client_config.host
            )
        )

        client = AuthenticatedClient(
            (
                f"{oauth_client_config.protocol}://"
                f"{assign_placeholders(oauth_client_config.host, connection_config.secrets)}"  # type: ignore
            ),
            connection_config,
            oauth_client_config,
        )

        try:
            # map param values to placeholders in request
            prepared_request = map_param_values(
                action,
                f"{connection_config.name} OAuth2",
                token_request,
                connection_config.secrets,  # type: ignore
            )
            # ignore errors so we can return the error message in the response
            response = client.send(prepared_request, ignore_errors=True)
            json_response = response.json()
        except Exception as exc:
            logger.error(
                "Error occurred during the {} request for {}: {}",
                action,
                connection_config.key,
                Pii(str(exc)),
            )
            raise OAuth2TokenException(
                f"Error occurred during the {action} request for {connection_config.key}: {str(exc)}"
            )

        return json_response

    def _check_required_secrets(self, connection_config: ConnectionConfig) -> None:
        """
        Verifies that the secrets required for authentication have been provided.
        """

        secrets = connection_config.secrets or {}
        required_secrets = {name: secrets.get(name) for name in self._required_secrets}
        if not all(required_secrets.values()):
            missing_secrets = [
                name for name, value in required_secrets.items() if not value
            ]
            raise FidesopsException(
                f"Missing required secret(s) '{', '.join(missing_secrets)}' for {connection_config.key}"
            )

    def _validate_and_store_response(
        self,
        response: Dict[str, Any],
        connection_config: ConnectionConfig,
        db: Optional[Session] = None,
    ) -> str:
        """
        Persists and returns the new access token.
        Also updates the refresh token if one is provided.
        """

        access_token = response.get("access_token")

        # error, error_description, and error_uri are part of the OAuth2 spec
        if access_token is None:
            error_message = " ".join(
                filter(
                    None,
                    (
                        f"Unable to retrieve token for {connection_config.key} ({response.get('error')}).",
                        response.get("error_description"),
                        response.get("error_uri"),
                    ),
                )
            )
            logger.error(error_message)
            raise OAuth2TokenException(error_message)

        data = {"access_token": access_token}

        # The authorization server MAY issue a new refresh token, in which case
        # the client MUST discard the old refresh token and replace it with the
        # new refresh token.
        #
        # https://datatracker.ietf.org/doc/html/rfc6749#section-6

        refresh_token = response.get("refresh_token")
        if refresh_token:
            data["refresh_token"] = refresh_token

        # If omitted, the authorization server SHOULD provide the
        # expiration time via other means or document the default value.
        #
        # https://datatracker.ietf.org/doc/html/rfc6749#section-5.1
        #
        # This alternate way of specifying the expiration is handled
        # by the optional expires_in field of the OAuth2AuthenticationConfiguration

        expires_in = self.expires_in or response.get("expires_in")
        if expires_in:
            data["expires_at"] = int(datetime.utcnow().timestamp()) + expires_in

        # persist new tokens to the database
        # ideally we use a passed in database session but we can
        # get the session from the connection_config as a fallback
        db = db or Session.object_session(connection_config)
        updated_secrets = {**connection_config.secrets, **data}  # type: ignore
        connection_config.update(db, data={"secrets": updated_secrets})
        logger.info(
            "Successfully updated the OAuth2 token(s) for {}", connection_config.key
        )

        return access_token

    def get_access_token(
        self, connection_config: ConnectionConfig, db: Optional[Session] = None
    ) -> str:
        """
        Executes the access token request based on the OAuth2 config
        and connection config secrets. The access and refresh tokens returned from
        this request are stored in the connection config secrets.
        """

        self._check_required_secrets(connection_config)
        access_response = self._call_token_request(
            "access", self.token_request, connection_config
        )
        return self._validate_and_store_response(access_response, connection_config, db)

    def _refresh_token(self, connection_config: ConnectionConfig) -> str:
        """
        Persists and returns a refreshed access_token if the token is close to expiring.
        Otherwise just returns the existing access_token.
        """

        if self.refresh_request:
            expires_at = connection_config.secrets.get("expires_at")  # type: ignore
            if self._close_to_expiration(expires_at, connection_config):
                refresh_response = self._call_token_request(
                    "refresh", self.refresh_request, connection_config
                )
                return self._validate_and_store_response(
                    refresh_response, connection_config
                )
        return connection_config.secrets.get("access_token")  # type: ignore
