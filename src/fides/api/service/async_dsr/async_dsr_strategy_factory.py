from enum import Enum
from typing import Any, Dict, List

from pydantic import ValidationError

from fides.api.common_exceptions import NoSuchStrategyException
from fides.api.common_exceptions import ValidationError as FidesopsValidationError
from fides.api.schemas.saas.strategy_configuration import StrategyConfiguration
from fides.api.service.async_dsr.async_dsr_strategy import AsyncDSRStrategy
from fides.api.service.async_dsr.async_dsr_strategy_callback import (
    CallbackAsyncDSRStrategy,
)
from fides.api.service.async_dsr.async_dsr_strategy_polling import (
    PollingAsyncDSRStrategy,
)


class SupportedAsyncDSRStrategies(Enum):
    """
    The supported async DSR strategies for handling asynchronous data subject requests.
    """

    callback = CallbackAsyncDSRStrategy
    polling = PollingAsyncDSRStrategy

    @classmethod
    def __contains__(cls, item: str) -> bool:
        try:
            cls[item]
        except KeyError:
            return False

        return True


def get_strategy(
    strategy_name: str,
    configuration: Dict[str, Any],
) -> AsyncDSRStrategy:
    """
    Returns the strategy given the name and configuration.
    Raises NoSuchStrategyException if the strategy does not exist
    """
    if not SupportedAsyncDSRStrategies.__contains__(strategy_name):
        valid_strategies = ", ".join(get_strategy_names())
        raise NoSuchStrategyException(
            f"Strategy '{strategy_name}' does not exist. Valid strategies are [{valid_strategies}]"
        )
    strategy = SupportedAsyncDSRStrategies[strategy_name].value
    if strategy.configuration_model is None:
        return strategy()
    try:
        strategy_config: StrategyConfiguration = strategy.configuration_model(
            **configuration
        )
        return strategy(configuration=strategy_config)
    except ValidationError as e:
        raise FidesopsValidationError(message=str(e))


def get_strategy_names() -> List[str]:
    """Returns all supported async DSR strategies"""
    return [s.name for s in SupportedAsyncDSRStrategies]
