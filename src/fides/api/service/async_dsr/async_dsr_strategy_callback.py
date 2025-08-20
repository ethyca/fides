from fides.api.schemas.saas.strategy_configuration import StrategyConfiguration
from fides.api.service.async_dsr.async_dsr_strategy import AsyncDSRStrategy


class CallbackAsyncDSRStrategy(AsyncDSRStrategy):
    """
    Strategy for polling async DSR requests.
    """

    name = "callback"
    configuration_model = StrategyConfiguration

    def __init__(self, configuration: StrategyConfiguration):
        pass
