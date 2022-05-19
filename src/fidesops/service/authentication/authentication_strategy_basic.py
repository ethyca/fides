from typing import Any, Dict

from requests import PreparedRequest

from fidesops.schemas.saas.strategy_configuration import (
    BasicAuthenticationConfiguration,
    StrategyConfiguration,
)
from fidesops.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fidesops.util.saas_util import assign_placeholders


class BasicAuthenticationStrategy(AuthenticationStrategy):
    """
    Replaces the username and password placeholders with the actual credentials
    and uses them to add a basic authentication header to the incoming request.
    """

    strategy_name = "basic"

    def __init__(self, configuration: BasicAuthenticationConfiguration):
        self.username = configuration.username
        self.password = configuration.password

    def add_authentication(
        self, request: PreparedRequest, secrets: Dict[str, Any]
    ) -> PreparedRequest:
        """Add basic authentication to the request"""
        request.prepare_auth(
            auth=(
                assign_placeholders(self.username, secrets),
                assign_placeholders(self.password, secrets),
            )
        )
        return request

    @staticmethod
    def get_configuration_model() -> StrategyConfiguration:
        return BasicAuthenticationConfiguration
