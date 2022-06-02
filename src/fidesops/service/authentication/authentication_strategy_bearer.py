from requests import PreparedRequest

from fidesops.models.connectionconfig import ConnectionConfig
from fidesops.schemas.saas.strategy_configuration import (
    BearerAuthenticationConfiguration,
    StrategyConfiguration,
)
from fidesops.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fidesops.util.saas_util import assign_placeholders


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
        request.headers["Authorization"] = "Bearer " + assign_placeholders(
            self.token, connection_config.secrets
        )
        return request

    @staticmethod
    def get_configuration_model() -> StrategyConfiguration:
        return BearerAuthenticationConfiguration
