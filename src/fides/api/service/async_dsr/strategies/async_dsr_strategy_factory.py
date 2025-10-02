from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import ValidationError
from sqlalchemy.orm import Session

from fides.api.common_exceptions import NoSuchStrategyException
from fides.api.common_exceptions import ValidationError as FidesopsValidationError
from fides.api.schemas.saas.async_polling_configuration import AsyncPollingConfiguration
from fides.api.service.async_dsr.strategies.async_dsr_strategy import AsyncDSRStrategy
from fides.api.service.async_dsr.strategies.async_dsr_strategy_callback import (
    AsyncCallbackStrategy,
)
from fides.api.service.async_dsr.strategies.async_dsr_strategy_polling import (
    AsyncPollingStrategy,
)


class SupportedAsyncDSRStrategies(Enum):
    """
    The supported async DSR strategies for handling asynchronous data subject requests.
    """

    callback = AsyncCallbackStrategy
    polling = AsyncPollingStrategy

    @classmethod
    def __contains__(cls, item: str) -> bool:
        try:
            cls[item]
        except KeyError:
            return False

        return True


def get_strategy(
    strategy_name: str,
    session: Session,
    configuration: Optional[Dict[str, Any]] = None,
) -> AsyncDSRStrategy:
    """
    Returns the enhanced strategy given the name, session, and configuration.
    Raises NoSuchStrategyException if the strategy does not exist
    """
    if not SupportedAsyncDSRStrategies.__contains__(strategy_name):
        valid_strategies = ", ".join(get_strategy_names())
        raise NoSuchStrategyException(
            f"Strategy '{strategy_name}' does not exist. Valid strategies are [{valid_strategies}]"
        )

    strategy_class = SupportedAsyncDSRStrategies[strategy_name].value

    if strategy_name == "polling":
        # Polling strategy requires configuration
        if not configuration:
            raise FidesopsValidationError("Configuration required for polling strategy")
        try:
            strategy_config = AsyncPollingConfiguration(**configuration)
            return strategy_class(session, strategy_config)
        except ValidationError as e:
            raise FidesopsValidationError(message=str(e))
    elif strategy_name == "callback":
        # Callback strategy only requires session
        return strategy_class(session)

    raise NoSuchStrategyException(f"Unsupported strategy: {strategy_name}")


def get_strategy_names() -> List[str]:
    """Returns all supported async DSR strategies"""
    return [s.name for s in SupportedAsyncDSRStrategies]
