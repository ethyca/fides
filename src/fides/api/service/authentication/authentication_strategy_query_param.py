from requests import PreparedRequest

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.saas.strategy_configuration import (
    QueryParamAuthenticationConfiguration,
    StrategyConfiguration,
)
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.util.saas_util import assign_placeholders
from fides.api.util.url_util import set_query_parameter


class QueryParamAuthenticationStrategy(AuthenticationStrategy):
    """
    Replaces the value placeholder with the actual credentials
    and adds it as a query param to the incoming request.
    """

    strategy_name = "query_param"

    def __init__(self, configuration: QueryParamAuthenticationConfiguration):
        self.name = configuration.name
        self.value = configuration.value

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """Add token to the request as a query param"""
        request.url = set_query_parameter(
            request.url,  # type: ignore
            self.name,
            assign_placeholders(self.value, connection_config.secrets),  # type: ignore
        )
        return request

    @staticmethod
    def get_configuration_model() -> StrategyConfiguration:
        return QueryParamAuthenticationConfiguration  # type: ignore
