from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List

from pydantic import ValidationError

from fides.api.common_exceptions import NoSuchStrategyException
from fides.api.common_exceptions import ValidationError as FidesopsValidationError
from fides.api.service.pagination.pagination_strategy_cursor import (
    CursorPaginationStrategy,
)
from fides.api.service.pagination.pagination_strategy_link import LinkPaginationStrategy
from fides.api.service.pagination.pagination_strategy_offset import (
    OffsetPaginationStrategy,
)

if TYPE_CHECKING:
    from fides.api.schemas.saas.strategy_configuration import StrategyConfiguration
    from fides.api.service.pagination.pagination_strategy import PaginationStrategy


class SupportedPaginationStrategies(Enum):
    """
    The supported methods by which Fidesops can post-process Saas connector data.
    """

    offset = OffsetPaginationStrategy
    link = LinkPaginationStrategy
    cursor = CursorPaginationStrategy

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
) -> PaginationStrategy:
    """
    Returns the strategy given the name and configuration.
    Raises NoSuchStrategyException if the strategy does not exist
    """
    if not SupportedPaginationStrategies.__contains__(strategy_name):
        valid_strategies = ", ".join([s.name for s in SupportedPaginationStrategies])
        raise NoSuchStrategyException(
            f"Strategy '{strategy_name}' does not exist. Valid strategies are [{valid_strategies}]"
        )
    strategy = SupportedPaginationStrategies[strategy_name].value
    try:
        strategy_config: StrategyConfiguration = strategy.get_configuration_model()(
            **configuration
        )
        return strategy(configuration=strategy_config)
    except ValidationError as e:
        raise FidesopsValidationError(message=str(e))


def get_strategies() -> List[PaginationStrategy]:
    """Returns all supported pagination strategies"""
    return [e.value for e in SupportedPaginationStrategies]
