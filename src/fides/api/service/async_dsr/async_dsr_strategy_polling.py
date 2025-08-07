from typing import Dict, Optional, List, Any
from requests import Response

from fides.api.graph.traversal import TraversalNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.schemas.saas.strategy_configuration import PollingAsyncDSRConfiguration
from fides.api.service.async_dsr.async_dsr_strategy import AsyncDSRStrategy
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.util.saas_util import map_param_values


class PollingAsyncDSRStrategy(AsyncDSRStrategy):
    """
    Strategy for polling async DSR requests.
    """

    name = "polling"
    configuration_model = PollingAsyncDSRConfiguration

    def __init__(self, configuration: PollingAsyncDSRConfiguration):
        self.status_request = configuration.status_request
        self.result_request = configuration.result_request
        self.result_path = configuration.result_path

    def start_request(
        self,
        request_params: SaaSRequestParams,
        connector_params: Dict[str, Any],
        response: Response,
        data_path: Optional[str],
    ) -> Optional[SaaSRequestParams]:
        pass

    def get_status_request(
        self,
        client: AuthenticatedClient,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        input_data: Dict[str, List[Any]],
        secrets: Dict[str, Any],
    ) -> Optional[SaaSRequestParams]:
        """Executes the status requests, and move forward if its true"""
        prepared_status_request = map_param_values(
            "status",
            "Polling",
            self.status_request,
            secrets,  # type: ignore
        )
        response: Response = client.send(prepared_status_request, privacy_request.id)

        return response.ok
        # TODO: Finish up status

        if response.ok:
            return self.get_result_request(
                client,
                node,
                policy,
                privacy_request,
                input_data,
                secrets,
            )

    def get_result_request(
        self,
        request_params: SaaSRequestParams,
        connector_params: Dict[str, Any],
        response: Response,
        data_path: Optional[str],
    ) -> Optional[SaaSRequestParams]:
        pass
