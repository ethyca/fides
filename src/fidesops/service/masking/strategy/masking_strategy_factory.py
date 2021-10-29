from enum import Enum
from typing import Dict, List, Union

from pydantic import ValidationError

from fidesops.service.masking.strategy.masking_strategy_hmac import HmacMaskingStrategy
from fidesops.service.masking.strategy.masking_strategy_random_string_rewrite import (
    RandomStringRewriteMaskingStrategy,
)
from fidesops.service.masking.strategy.masking_strategy import MaskingStrategy
from fidesops.service.masking.strategy.masking_strategy_aes_encrypt import (
    AesEncryptionMaskingStrategy,
)
from fidesops.service.masking.strategy.masking_strategy_hash import HashMaskingStrategy
from fidesops.service.masking.strategy.masking_strategy_string_rewrite import (
    StringRewriteMaskingStrategy,
)
from fidesops.common_exceptions import (
    ValidationError as FidesopsValidationError,
    NoSuchStrategyException,
)

from fidesops.schemas.masking.masking_configuration import FormatPreservationConfig


class SupportedMaskingStrategies(Enum):
    """
    The supported methods by which Fidesops can pseudonymize data.
    """

    string_rewrite = StringRewriteMaskingStrategy
    hash = HashMaskingStrategy
    random_string_rewrite = RandomStringRewriteMaskingStrategy
    aes_encrypt = AesEncryptionMaskingStrategy
    hmac = HmacMaskingStrategy


def get_strategy(
    strategy_name: str,
    configuration: Dict[
        str,
        Union[str, FormatPreservationConfig],
    ],
) -> MaskingStrategy:
    """
    Returns the strategy given the name and configuration.
    Raises NoSuchStrategyException if the strategy does not exist
    """
    if strategy_name not in SupportedMaskingStrategies.__members__:
        valid_strategies = ", ".join([s.name for s in SupportedMaskingStrategies])
        raise NoSuchStrategyException(
            f"Strategy '{strategy_name}' does not exist. Valid strategies are [{valid_strategies}]"
        )
    strategy = SupportedMaskingStrategies[strategy_name].value
    try:
        strategy_config = strategy.get_configuration_model()(**configuration)
        return strategy(configuration=strategy_config)
    except ValidationError as e:
        raise FidesopsValidationError(message=str(e))


def get_strategies() -> List[MaskingStrategy]:
    """Returns all supported masking strategies"""
    return [e.value for e in SupportedMaskingStrategies]
