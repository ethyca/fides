import json
from typing import Dict, List, Optional

from requests import PreparedRequest

from fides.api.common_exceptions import FidesopsException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.saas.saas_config import Header, QueryParam
from fides.api.schemas.saas.strategy_configuration import (
    ApiKeyAuthenticationConfiguration,
)
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.util.saas_util import assign_placeholders
from fides.api.util.url_util import set_query_parameter


class ApiKeyAuthenticationStrategy(AuthenticationStrategy):
    """
    Adds an API key to each request header, query param, or the body
    depending on configuration
    """

    name = "api_key"
    configuration_model = ApiKeyAuthenticationConfiguration

    def __init__(self, configuration: ApiKeyAuthenticationConfiguration):
        self.headers: List[Header] = configuration.headers  # type: ignore
        self.query_params: List[QueryParam] = configuration.query_params  # type: ignore
        self.body: Optional[str] = configuration.body  # type: ignore

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """
        Add API key authentication to the request header or query param
        """
        secrets = connection_config.secrets
        if not secrets:
            raise FidesopsException(
                "Secrets are not configured for this SaaS connector. Secrets must be configured to use API key authentication"
            )
        if self.headers:
            for header in self.headers:
                header_val = assign_placeholders(header.value, secrets)
                if header_val is None:
                    raise FidesopsException(
                        f"Value for API key param '{header.value}' not found"
                    )
                request.headers[header.name] = header_val
        if self.query_params:
            for query_param in self.query_params:
                param_val = assign_placeholders(query_param.value, secrets)
                if param_val is None:
                    raise FidesopsException(
                        f"Value for API key param '{query_param.value}' not found"
                    )
                request.url = set_query_parameter(
                    request.url,  # type: ignore
                    query_param.name,
                    param_val,
                )
        if self.body:
            body_with_api_key: Optional[str] = assign_placeholders(
                self.body, secrets or {}
            )
            api_key_request_body: Dict = json.loads(body_with_api_key or "{}")

            original_request_body: Dict = json.loads(request.body or "{}")
            original_request_body.update(api_key_request_body)

            request.prepare_body(
                data=json.dumps(original_request_body), files=None, json=True
            )

        return request
