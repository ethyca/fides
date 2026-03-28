from __future__ import annotations

from abc import ABC
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pydantic import ValidationError

from fides.api.common_exceptions import NoSuchStrategyException
from fides.api.common_exceptions import ValidationError as FidesopsValidationError
from fides.api.schemas.saas.strategy_configuration import StrategyConfiguration

T = TypeVar("T", bound="Strategy")
C = TypeVar("C", bound=StrategyConfiguration)


def _find_strategy_subclass(
    cls: Type[Strategy], strategy_name: str
) -> Optional[Type[Strategy]]:
    if hasattr(cls, "name") and cls.name == strategy_name:
        return cls
    for sub in cls.__subclasses__():
        found = _find_strategy_subclass(sub, strategy_name)
        if found:
            return found
    return None


def _find_all_strategy_subclasses(
    cls: Type[T], subs: Optional[List[Type[T]]] = None
) -> List[Type[T]]:
    if subs is None:
        subs = []
    if hasattr(cls, "name"):
        subs.append(cls)
    for sub in cls.__subclasses__():
        _find_all_strategy_subclasses(sub, subs)
    return subs


class Strategy(ABC, Generic[C]):
    """Abstract base class for strategies"""

    name: str
    configuration_model: Optional[Type[C]] = None

    @classmethod
    def get_strategy(
        cls: Type[T],
        strategy_name: str,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> T:
        """
        Returns the strategy given the name and configuration.
        Raises NoSuchStrategyException if the strategy does not exist
        """

        strategy_class = _find_strategy_subclass(cls, strategy_name)

        if strategy_class is None:
            valid_strategies = ", ".join(
                [sub.name for sub in _find_all_strategy_subclasses(cls)]
            )
            raise NoSuchStrategyException(
                f"Strategy '{strategy_name}' does not exist. Valid strategies are [{valid_strategies}]"
            )
        try:
            if strategy_class.configuration_model:
                strategy_config = strategy_class.configuration_model(**configuration)
            else:
                return strategy_class()  # type: ignore
        except ValidationError as e:
            raise FidesopsValidationError(message=str(e))
        return strategy_class(strategy_config)  # type: ignore

    @classmethod
    def get_strategies(cls: Type[T]) -> List[Type[T]]:
        """Returns all supported strategies"""
        return _find_all_strategy_subclasses(cls)
