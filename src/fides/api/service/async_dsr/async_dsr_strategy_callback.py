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


    def __init__(self):
        pass
