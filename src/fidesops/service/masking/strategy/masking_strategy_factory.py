import logging
from typing import Callable, Dict, Type, Union, ValuesView

from pydantic import ValidationError

from fidesops.common_exceptions import NoSuchStrategyException
from fidesops.common_exceptions import ValidationError as FidesopsValidationError
from fidesops.schemas.masking.masking_configuration import FormatPreservationConfig
from fidesops.service.masking.strategy.masking_strategy import MaskingStrategy

logger = logging.getLogger(__name__)


class MaskingStrategyFactory:
    registry: Dict[str, Type[MaskingStrategy]] = {}
    valid_strategies: str = ""

    @classmethod
    def register(
        cls, name: str
    ) -> Callable[[Type[MaskingStrategy]], Type[MaskingStrategy]]:
        def wrapper(strategy_class: Type[MaskingStrategy]) -> Type[MaskingStrategy]:
            logger.debug(
                f"Registering new masking strategy '{strategy_class}' under name '{name}'"
            )

            if name in cls.registry:
                logger.warning(
                    f"Masking strategy with name '{name}' already exists. It previously referred to class '{cls.registry[name]}', but will now refer to '{strategy_class}'"
                )

            cls.registry[name] = strategy_class
            cls.valid_strategies = ", ".join(cls.registry.keys())
            return cls.registry[name]

        return wrapper

    @classmethod
    def get_strategy(
        cls,
        strategy_name: str,
        configuration: Dict[str, Union[str, FormatPreservationConfig]],
    ) -> MaskingStrategy:
        """
        Returns the strategy given the name and configuration.
        Raises NoSuchStrategyException if the strategy does not exist
        """
        try:
            strategy = cls.registry[strategy_name]
        except KeyError:
            raise NoSuchStrategyException(
                f"Strategy '{strategy_name}' does not exist. Valid strategies are [{cls.valid_strategies}]"
            )
        try:
            strategy_config = strategy.get_configuration_model()(**configuration)
        except ValidationError as e:
            raise FidesopsValidationError(message=str(e))
        return strategy(configuration=strategy_config)

    @classmethod
    def get_strategies(cls) -> ValuesView[MaskingStrategy]:
        """Returns all supported masking strategies"""
        return cls.registry.values()
