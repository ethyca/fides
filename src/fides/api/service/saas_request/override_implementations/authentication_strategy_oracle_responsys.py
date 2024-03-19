from typing import Dict, Optional, cast

from requests import PreparedRequest, post

from fides.api.common_exceptions import FidesopsException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.saas.strategy_configuration import StrategyConfiguration
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.util.saas_util import assign_placeholders


class OracleResponsysAuthenticationConfiguration(StrategyConfiguration):
    """
    Parameters to authorize a Oracle Responsys connection
    """

    username: str
    password: str


class OracleResponsysAuthenticationStrategy(AuthenticationStrategy):
    """
    Generates a token from the provided key and secret.
    """

    name = "oracle_responsys"
    configuration_model = OracleResponsysAuthenticationConfiguration

    def __init__(self, configuration: OracleResponsysAuthenticationConfiguration):
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
        password: Optional[str] = assign_placeholders(self.password, secrets)

        response = post(
            url=f"https://{domain}/rest/api/v1.3/auth/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"user_name": username, "password": password, "auth_type": "password"},
        )

        if response.ok:
            json_response = response.json()
            token = json_response.get("authToken")
        else:
            raise FidesopsException(f"Unable to get token {response.json()}")

        request.headers["Authorization"] = token
        return request
