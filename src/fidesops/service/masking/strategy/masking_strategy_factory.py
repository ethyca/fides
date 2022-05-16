from enum import Enum
from typing import Dict, List, Union

from pydantic import ValidationError

from fidesops.common_exceptions import NoSuchStrategyException
from fidesops.common_exceptions import ValidationError as FidesopsValidationError
from fidesops.schemas.masking.masking_configuration import (
    FormatPreservationConfig,
    MaskingConfiguration,
)
from fidesops.service.masking.strategy.masking_strategy import MaskingStrategy
from fidesops.service.masking.strategy.masking_strategy_aes_encrypt import (
    AesEncryptionMaskingStrategy,
)
from fidesops.service.masking.strategy.masking_strategy_hash import HashMaskingStrategy
from fidesops.service.masking.strategy.masking_strategy_hmac import HmacMaskingStrategy
from fidesops.service.masking.strategy.masking_strategy_nullify import (
    NullMaskingStrategy,
)
from fidesops.service.masking.strategy.masking_strategy_random_string_rewrite import (
    RandomStringRewriteMaskingStrategy,
)
from fidesops.service.masking.strategy.masking_strategy_string_rewrite import (
    StringRewriteMaskingStrategy,
)


class SupportedMaskingStrategies(Enum):
    """
    The supported methods by which Fidesops can pseudonymize data.
    """

    string_rewrite = StringRewriteMaskingStrategy
    random_string_rewrite = RandomStringRewriteMaskingStrategy
    null_rewrite = NullMaskingStrategy
    hash = HashMaskingStrategy
    aes_encrypt = AesEncryptionMaskingStrategy
    hmac = HmacMaskingStrategy

    @classmethod
    def __contains__(cls, item: str) -> bool:
        try:
            cls[item]
        except KeyError:
            return False

        return True


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
    if not SupportedMaskingStrategies.__contains__(strategy_name):
        valid_strategies = ", ".join([s.name for s in SupportedMaskingStrategies])
        raise NoSuchStrategyException(
            f"Strategy '{strategy_name}' does not exist. Valid strategies are [{valid_strategies}]"
        )
    strategy = SupportedMaskingStrategies[strategy_name].value
    try:
        strategy_config: MaskingConfiguration = strategy.get_configuration_model()(
            **configuration
        )
        return strategy(configuration=strategy_config)
    except ValidationError as e:
        raise FidesopsValidationError(message=str(e))


def get_strategies() -> List[MaskingStrategy]:
    """Returns all supported masking strategies"""
    return [e.value for e in SupportedMaskingStrategies]
