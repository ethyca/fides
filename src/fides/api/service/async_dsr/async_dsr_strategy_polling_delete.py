from typing import Any, Dict, List, Optional

import pydash
from requests import Response

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.schemas.saas.strategy_configuration import PollingAsyncDSRBaseConfiguration
from fides.api.service.async_dsr.async_dsr_strategy_polling_base import PollingAsyncDSRBaseStrategy
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.util.collection_util import Row
from fides.api.util.saas_util import map_param_values

from fides.api.models.privacy_request.request_task import RequestTask


class PollingAsyncErasureStrategy(PollingAsyncDSRBaseStrategy):
    """
    Strategy for polling async erasure requests.
    Erasure requests typically only need to confirm completion status.
    """

    name = "polling_erasure"
    configuration_model = PollingAsyncDSRBaseConfiguration

    def __init__(self, configuration: PollingAsyncDSRBaseConfiguration):
        super().__init__(configuration)

    def get_result_request(
        self,
        client: AuthenticatedClient,
        param_values: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute result request and return erasure confirmation."""
        prepared_result_request = map_param_values(
            "result", "polling erasure request", self.result_request, param_values
        )

        response: Response = client.send(prepared_result_request)

        if response.ok:
            # For erasure, we typically just need confirmation
            result = pydash.get(response.json(), self.result_path) if self.result_path else response.json()

            return {
                "status": "completed",
                "details": result
            }

        raise PrivacyRequestError(
            f"Erasure result request failed with status code {response.status_code}"
        )
