from typing import Any, Dict, List, cast

from requests import PreparedRequest

from fides.api.ops.graph.traversal import TraversalNode
from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.saas.strategy_configuration import StrategyConfiguration
from fides.api.ops.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.ops.service.connectors.saas.authenticated_client import (
    AuthenticatedClient,
)
from fides.api.ops.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.ops.util.collection_util import Row
from fides.api.ops.util.saas_util import assign_placeholders


@register("custom_user_access", [SaaSRequestType.READ])
def custom_user_access(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    return [{"id": 1}]


class CustomAuthenticationConfiguration(StrategyConfiguration):
    """
    Parameters for custom authentication
    """

    secret_knock: str
    secret_handshake: str


class CustomAuthenticationStrategy(AuthenticationStrategy):
    """
    Adds the secrets to the request
    """

    name = "custom"
    configuration_model = CustomAuthenticationConfiguration

    def __init__(self, configuration: CustomAuthenticationConfiguration):
        self.secret_knock = configuration.secret_knock
        self.secret_handshake = configuration.secret_handshake

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """
        Verifies you know the secret knock and secret handshake, so secure
        """

        secrets = cast(Dict, connection_config.secrets)

        secret_knock = assign_placeholders(self.secret_knock, secrets)
        secret_handshake = assign_placeholders(self.secret_handshake, secrets)

        assert secret_knock
        assert secret_handshake

        request.headers["Authorization"] = f"Bearer {secret_knock + secret_handshake}"
        return request
