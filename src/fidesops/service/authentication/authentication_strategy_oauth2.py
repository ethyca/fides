import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Literal, Optional
from urllib.parse import urlencode
from uuid import uuid4

from requests import PreparedRequest
from sqlalchemy.orm import Session

from fidesops.common_exceptions import FidesopsException, OAuth2TokenException
from fidesops.models.authentication_request import AuthenticationRequest
from fidesops.models.connectionconfig import ConnectionConfig
from fidesops.schemas.saas.saas_config import ClientConfig, SaaSRequest
from fidesops.schemas.saas.strategy_configuration import (
    OAuth2AuthenticationConfiguration,
    StrategyConfiguration,
)
from fidesops.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fidesops.service.connectors.saas.authenticated_client import AuthenticatedClient
from fidesops.util.logger import NotPii
from fidesops.util.saas_util import assign_placeholders, map_param_values

logger = logging.getLogger(__name__)


class OAuth2AuthenticationStrategy(AuthenticationStrategy):
    """
    Checks the expiration date on the stored access token and refreshes
    it if needed using the configured token refresh request.
    """

    strategy_name = "oauth2"

    def __init__(self, configuration: OAuth2AuthenticationConfiguration):
        self.expires_in = configuration.expires_in
        self.authorization_request = configuration.authorization_request
        self.token_request = configuration.token_request
        self.refresh_request = configuration.refresh_request

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """
        Checks the expiration date on the existing access token and refreshes if necessary.
        The existing/updated access token is then added to the request as a bearer token.
        """

        # make sure required secrets have been provided
        self._check_required_secrets(connection_config)

        access_token = connection_config.secrets.get("access_token")
        if not access_token:
            raise FidesopsException(
                f"OAuth2 access token not found for {connection_config.key}, please "
                f"authenticate connection via /api/v1/connection/{connection_config.key}/authorize"
            )

        # The refresh request is optional since the OAuth2 spec does not require
        # a refresh token to be returned as part of an access token request
        #
        # https://datatracker.ietf.org/doc/html/rfc6749#section-5.1

        if self.refresh_request:
            expires_at = connection_config.secrets.get("expires_at")
            if self._close_to_expiration(expires_at, connection_config):
                refresh_response = self._call_token_request(
                    "refresh", self.refresh_request, connection_config
                )
                access_token = self._validate_and_store_response(
                    None, refresh_response, connection_config
                )

        # add access_token to request
        request.headers["Authorization"] = "Bearer " + access_token
        return request

    @staticmethod
    def _close_to_expiration(
        expires_at: int, connection_config: ConnectionConfig
    ) -> bool:
        """Check if the access_token will expire in the next 10 minutes"""
        if expires_at is None:
            logger.info(
                f"The expires_at value is not defined for {connection_config.key}, skipping token refresh"
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

        logger.info(f"Attempting {action} token request for {connection_config.key}")

        # get the client config from the token request or default to the
        # protocol and host specified by the root client config (no auth)
        root_client_config = connection_config.get_saas_config().client_config
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
                f"{assign_placeholders(oauth_client_config.host, connection_config.secrets)}"
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
                connection_config.secrets,
            )
            # ignore errors so we can return the error message in the response
            response = client.send(prepared_request, ignore_errors=True)
            json_response = response.json()
        except Exception as exc:
            logger.error(
                "Error occurred during the %s request for %s: %s",
                action,
                NotPii(connection_config.key),
                str(exc),
            )
            raise OAuth2TokenException(
                f"Error occurred during the {action} request for {connection_config.key}: {str(exc)}"
            )

        return json_response

    def _validate_and_store_response(
        self,
        db: Optional[Session],
        response: Dict[str, Any],
        connection_config: ConnectionConfig,
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

        expires_in = response.get("expires_in") or self.expires_in
        if expires_in:
            data["expires_at"] = int(datetime.utcnow().timestamp()) + expires_in

        # persist new tokens to the database
        # ideally we use a passed in database session but we can
        # get the session from the connection_config as a fallback
        if not db:
            db = Session.object_session(connection_config)
        updated_secrets = {**connection_config.secrets, **data}
        connection_config.update(db, data={"secrets": updated_secrets})
        logger.info(
            f"Successfully updated the OAuth2 token(s) for {connection_config.key}"
        )

        return access_token

    def get_authorization_url(
        self, db: Session, connection_config: ConnectionConfig
    ) -> Optional[str]:
        """
        Returns the authorization URL to initiate the OAuth2 workflow.
        Also stores a reference between the authorization request and the connector
        to be able to link the returned auth code to the correct connector."""

        # make sure the required secrets to generate the authorization url have been provided
        self._check_required_secrets(connection_config)

        # generate the state that will be used to link this authorization request to this connector
        state = str(uuid4())
        AuthenticationRequest.create_or_update(
            db, data={"connection_key": connection_config.key, "state": state}
        )
        # add state to secrets
        connection_config.secrets["state"] = state

        # assign placeholders in the authorization request config
        prepared_authorization_request = map_param_values(
            "authorize",
            f"{connection_config.name} OAuth2",
            self.authorization_request,
            connection_config.secrets,
        )

        # get the client config from the authorization request or default
        # to the base client config if one isn't provided
        client_config = (
            self.authorization_request.client_config
            if self.authorization_request.client_config
            else connection_config.get_saas_config().client_config
        )

        # build the complete URL with query params
        return (
            f"{client_config.protocol}://{assign_placeholders(client_config.host, connection_config.secrets)}"
            f"{prepared_authorization_request.path}"
            f"?{urlencode(prepared_authorization_request.query_params)}"
        )

    def get_access_token(
        self, db: Session, code: str, connection_config: ConnectionConfig
    ) -> None:
        """
        Generates and executes the access token request based on the OAuth2 config
        and connection config secrets. The access and refresh tokens returned from
        this request are stored in the connection config secrets.
        """

        self._check_required_secrets(connection_config)
        connection_config.secrets = {**connection_config.secrets, "code": code}
        access_response = self._call_token_request(
            "access", self.token_request, connection_config
        )
        self._validate_and_store_response(db, access_response, connection_config)

    @staticmethod
    def _check_required_secrets(connection_config: ConnectionConfig) -> None:
        secrets = connection_config.secrets or {}
        required_secrets = {
            "client_id": secrets.get("client_id"),
            "client_secret": secrets.get("client_secret"),
            "redirect_uri": secrets.get("redirect_uri"),
        }

        if not all(required_secrets.values()):
            missing_secrets = [
                name for name, value in required_secrets.items() if not value
            ]
            raise FidesopsException(
                f"Missing required secret(s) '{', '.join(missing_secrets)}' for {connection_config.key}"
            )

    @staticmethod
    def get_configuration_model() -> StrategyConfiguration:
        return OAuth2AuthenticationConfiguration
