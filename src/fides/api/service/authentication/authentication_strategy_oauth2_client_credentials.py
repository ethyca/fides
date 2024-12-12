from requests import PreparedRequest

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.saas.strategy_configuration import OAuth2BaseConfiguration
from fides.api.service.authentication.authentication_strategy_oauth2_base import (
    OAuth2AuthenticationStrategyBase,
)


class OAuth2ClientCredentialsAuthenticationStrategy(OAuth2AuthenticationStrategyBase):
    """
    Checks the expiration date on the stored access token and refreshes
    it if needed using the configured token refresh request.
    """

    name = "oauth2_client_credentials"
    configuration_model = OAuth2BaseConfiguration

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """
        Checks the expiration date on the existing access token and refreshes if necessary.
        The existing/updated access token is then added to the request as a bearer token.
        """

        access_token = connection_config.secrets.get("access_token")  # type: ignore
        if not access_token:
            access_token = self.get_access_token(connection_config)
        else:
            access_token = self._refresh_token(connection_config)

        # add access_token to request
        request.headers["Authorization"] = "Bearer " + access_token
        return request
