from typing import Dict, Optional, cast

from requests import PreparedRequest, post

from fides.api.common_exceptions import FidesopsException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.saas.strategy_configuration import StrategyConfiguration
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.util.saas_util import assign_placeholders


class HeapAuthenticationConfiguration(StrategyConfiguration):
    """
    Parameters to authorize a Heap connection
    """

    username: str
    password: str


class HeapAuthenticationStrategy(AuthenticationStrategy):
    """
    Generates a token from the provided key and secret.
    Stores the expiration time to know when to refresh the token.
    """

    name = "heap"
    configuration_model = HeapAuthenticationConfiguration

    def __init__(self, configuration: HeapAuthenticationConfiguration):
        self.username = configuration.username
        self.password = configuration.password

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """
        Retrieves a token using the provided username and password
        """

        secrets = cast(Dict, connection_config.secrets)
        domain: Optional[str] = secrets.get("domain")
        username: Optional[str] = assign_placeholders(self.username, secrets)
        password: Optional[int] = assign_placeholders(self.password, secrets)

        response = post(
            url=f"https://{domain}/api/public/v0/auth_token",
            auth=(username, password),
        )

        if response.ok:
            json_response = response.json()
            token = json_response.get("access_token")
        else:
            raise FidesopsException(f"Unable to get token {response.json()}")

        request.headers["Authorization"] = f"Bearer {token}"
        return request
