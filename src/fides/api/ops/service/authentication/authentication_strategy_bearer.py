from requests import PreparedRequest

from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.schemas.saas.strategy_configuration import (
    BearerAuthenticationConfiguration,
)
from fides.api.ops.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.ops.util.saas_util import assign_placeholders


class BearerAuthenticationStrategy(AuthenticationStrategy):
    """
    Replaces the token placeholder with the actual credentials
    and uses it to add a bearer authentication header to the incoming request.
    """

    name = "bearer"
    configuration_model = BearerAuthenticationConfiguration

    def __init__(self, configuration: BearerAuthenticationConfiguration):
        self.token = configuration.token

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """Add bearer authentication to the request"""
        request.headers["Authorization"] = "Bearer " + assign_placeholders(  # type: ignore
            self.token, connection_config.secrets  # type: ignore
        )
        return request
