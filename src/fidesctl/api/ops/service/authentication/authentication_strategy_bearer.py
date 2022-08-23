from requests import PreparedRequest

from fidesctl.api.ops.models.connectionconfig import ConnectionConfig
from fidesctl.api.ops.schemas.saas.strategy_configuration import (
    BearerAuthenticationConfiguration,
    StrategyConfiguration,
)
from fidesctl.api.ops.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fidesctl.api.ops.util.saas_util import assign_placeholders


class BearerAuthenticationStrategy(AuthenticationStrategy):
    """
    Replaces the token placeholder with the actual credentials
    and uses it to add a bearer authentication header to the incoming request.
    """

    strategy_name = "bearer"

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

    @staticmethod
    def get_configuration_model() -> StrategyConfiguration:
        return BearerAuthenticationConfiguration  # type: ignore
