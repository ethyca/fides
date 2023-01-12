from typing import Callable, Dict, Type, Union, ValuesView

from loguru import logger
from pydantic import ValidationError

from fides.api.ops.common_exceptions import NoSuchStrategyException
from fides.api.ops.common_exceptions import ValidationError as FidesopsValidationError
from fides.api.ops.schemas.masking.masking_configuration import FormatPreservationConfig
from fides.api.ops.service.masking.strategy.masking_strategy import MaskingStrategy


class MaskingStrategyFactory:
    registry: Dict[str, Type[MaskingStrategy]] = {}
    valid_strategies: str = ""

    @classmethod
    def register(
        cls, name: str
    ) -> Callable[[Type[MaskingStrategy]], Type[MaskingStrategy]]:
        def wrapper(strategy_class: Type[MaskingStrategy]) -> Type[MaskingStrategy]:
            logger.debug(
                "Registering new masking strategy '{}' under name '{}'",
                strategy_class,
                name,
            )

            if name in cls.registry:
                logger.warning(
                    "Masking strategy with name '{}' already exists. It previously referred to class '{}', but will now refer to '{}'",
                    name,
                    cls.registry[name],
                    strategy_class,
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
            strategy_config = strategy.get_configuration_model()(**configuration)  # type: ignore
        except ValidationError as e:
            raise FidesopsValidationError(message=str(e))
        return strategy(configuration=strategy_config)  # type: ignore

    @classmethod
    def get_strategies(cls) -> ValuesView[MaskingStrategy]:
        """Returns all supported masking strategies"""
        return cls.registry.values()  # type: ignore
