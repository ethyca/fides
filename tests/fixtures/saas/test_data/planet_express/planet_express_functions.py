from typing import Any, Dict, List, cast

from requests import PreparedRequest

from fides.api.graph.traversal import TraversalNode
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.strategy_configuration import StrategyConfiguration
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.util.collection_util import Row
from fides.api.util.saas_util import assign_placeholders


@register("planet_express_user_access", [SaaSRequestType.READ])
def planet_express_user_access(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    return [{"id": 1}]


class PlanetExpressAuthenticationConfiguration(StrategyConfiguration):
    """
    Parameters for custom authentication
    """

    secret_knock: str
    secret_handshake: str


class PlanetExpressAuthenticationStrategy(AuthenticationStrategy):
    """
    Adds the secrets to the request
    """

    name = "planet_express"
    configuration_model = PlanetExpressAuthenticationConfiguration

    def __init__(self, configuration: PlanetExpressAuthenticationConfiguration):
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
