from typing import Any, Dict, Optional

from requests import Response

from fides.api.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.schemas.saas.strategy_configuration import StrategyConfiguration
from fides.api.service.async_dsr.async_dsr_strategy import AsyncDSRStrategy


class CallbackAsyncDSRStrategy(AsyncDSRStrategy):
    """
    Strategy for callback async DSR requests.
    """

    name = "callback"
    configuration_model = StrategyConfiguration

    def __init__(self, configuration: StrategyConfiguration):
        pass

    def start_request(
        self,
        request_params: SaaSRequestParams,
        connector_params: Dict[str, Any],
        response: Response,
        data_path: Optional[str],
    ) -> Optional[SaaSRequestParams]:
        pass
