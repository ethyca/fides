import logging
from enum import Enum
from typing import Any, Dict, List

from fidesctl.api.ops.common_exceptions import NoSuchStrategyException
from fidesctl.api.ops.common_exceptions import (
    ValidationError as FidesopsValidationError,
)
from fidesctl.api.ops.schemas.saas.strategy_configuration import StrategyConfiguration
from fidesctl.api.ops.service.processors.post_processor_strategy.post_processor_strategy import (
    PostProcessorStrategy,
)
from fidesctl.api.ops.service.processors.post_processor_strategy.post_processor_strategy_filter import (
    FilterPostProcessorStrategy,
)
from fidesctl.api.ops.service.processors.post_processor_strategy.post_processor_strategy_unwrap import (
    UnwrapPostProcessorStrategy,
)
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class SupportedPostProcessorStrategies(Enum):
    """
    The supported methods by which Fidesops can post-process Saas connector data.
    """

    unwrap = UnwrapPostProcessorStrategy
    filter = FilterPostProcessorStrategy

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
) -> PostProcessorStrategy:
    """
    Returns the strategy given the name and configuration.
    Raises NoSuchStrategyException if the strategy does not exist
    """
    if not SupportedPostProcessorStrategies.__contains__(strategy_name):
        valid_strategies = ", ".join([s.name for s in SupportedPostProcessorStrategies])
        raise NoSuchStrategyException(
            f"Strategy '{strategy_name}' does not exist. Valid strategies are [{valid_strategies}]"
        )
    strategy = SupportedPostProcessorStrategies[strategy_name].value
    try:
        strategy_config: StrategyConfiguration = strategy.get_configuration_model()(
            **configuration
        )
        return strategy(configuration=strategy_config)
    except ValidationError as e:
        raise FidesopsValidationError(message=str(e))


def get_strategies() -> List[PostProcessorStrategy]:
    """Returns all supported postprocessor strategies"""
    return [e.value for e in SupportedPostProcessorStrategies]
