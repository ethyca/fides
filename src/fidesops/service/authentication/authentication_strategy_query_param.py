from typing import Any, Dict

from requests import PreparedRequest

from fidesops.schemas.saas.strategy_configuration import (
    QueryParamAuthenticationConfiguration,
    StrategyConfiguration,
)
from fidesops.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fidesops.util.saas_util import assign_placeholders
from fidesops.util.url_util import set_query_parameter


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
        self, request: PreparedRequest, secrets: Dict[str, Any]
    ) -> PreparedRequest:
        """Add token to the request as a query param"""
        request.url = set_query_parameter(
            request.url, self.name, assign_placeholders(self.value, secrets)
        )
        return request

    @staticmethod
    def get_configuration_model() -> StrategyConfiguration:
        return QueryParamAuthenticationConfiguration
