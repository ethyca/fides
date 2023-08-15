from typing import List, Optional
from urllib.parse import urlencode
from uuid import uuid4

from requests import PreparedRequest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import FidesopsException
from fides.api.models.authentication_request import AuthenticationRequest
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.saas.strategy_configuration import (
    OAuth2AuthorizationCodeConfiguration,
)
from fides.api.service.authentication.authentication_strategy_oauth2_base import (
    OAuth2AuthenticationStrategyBase,
)
from fides.api.util.saas_util import assign_placeholders, map_param_values
from fides.config import CONFIG


class OAuth2AuthorizationCodeAuthenticationStrategy(OAuth2AuthenticationStrategyBase):
    """
    Checks the expiration date on the stored access token and refreshes
    it if needed using the configured token refresh request.
    """

    name = "oauth2_authorization_code"
    configuration_model = OAuth2AuthorizationCodeConfiguration

    def __init__(self, configuration: OAuth2AuthorizationCodeConfiguration):
        super().__init__(configuration)
        self.authorization_request = configuration.authorization_request

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """
        Checks the expiration date on the existing access token and refreshes if necessary.
        The existing/updated access token is then added to the request as a bearer token.
        """

        # make sure required secrets have been provided
        self._check_required_secrets(connection_config)

        access_token = connection_config.secrets.get("access_token")  # type: ignore
        if not access_token:
            raise FidesopsException(
                f"OAuth2 access token not found for {connection_config.key}, please "
                f"authenticate connection via /api/v1/connection/{connection_config.key}/authorize"
            )

        # The refresh request is optional since the OAuth2 spec does not require
        # a refresh token to be returned as part of an access token request
        #
        # https://datatracker.ietf.org/doc/html/rfc6749#section-5.1

        access_token = self._refresh_token(connection_config)

        # add access_token to request
        request.headers["Authorization"] = "Bearer " + access_token
        return request

    @property
    def _required_secrets(self) -> List[str]:
        return ["client_id", "client_secret", "redirect_uri"]

    def get_authorization_url(
        self,
        db: Session,
        connection_config: ConnectionConfig,
        referer: Optional[str] = None,
    ) -> Optional[str]:
        """
        Returns the authorization URL to initiate the OAuth2 workflow.
        Also stores a reference between the authorization request and the connector
        to be able to link the returned auth code to the correct connector."""

        # make sure the required secrets to generate the authorization url have been provided
        self._check_required_secrets(connection_config)

        # generate the state that will be used to link this authorization request to this connector
        state = self._generate_state()
        AuthenticationRequest.create_or_update(
            db,
            data={
                "connection_key": connection_config.key,
                "state": state,
                "referer": referer,
            },
        )
        # add state to secrets
        connection_config.secrets["state"] = state  # type: ignore

        # assign placeholders in the authorization request config
        prepared_authorization_request = map_param_values(
            "authorize",
            f"{connection_config.name} OAuth2",
            self.authorization_request,
            connection_config.secrets,  # type: ignore
        )

        # get the client config from the authorization request or default
        # to the base client config if one isn't provided
        client_config = (
            self.authorization_request.client_config
            if self.authorization_request.client_config
            else connection_config.get_saas_config().client_config  # type: ignore
        )

        # build the complete URL with query params
        return (
            f"{client_config.protocol}://{assign_placeholders(client_config.host, connection_config.secrets)}"  # type: ignore
            f"{prepared_authorization_request.path}"
            f"?{urlencode(prepared_authorization_request.query_params)}"
        )

    @staticmethod
    def _generate_state() -> str:
        """
        Generates a string value to associate the authentication request
        with an eventual OAuth2 callback response.

        If an oauth_instance name is defined then the name is added as a
        prefix to the generated state. The state prefix can be used by a
        proxy server to route the callback response to a specific Fidesops
        instance. This functionality is not part of the OAuth2 specification
        but it can be used for local testing of OAuth2 workflows.
        """

        state = str(uuid4())
        if CONFIG.oauth_instance:
            state = f"{CONFIG.oauth_instance}-{state}"
        return state
