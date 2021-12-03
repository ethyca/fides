from typing import Optional

from fidesops.schemas.masking.masking_configuration import (
    NullMaskingConfiguration,
    MaskingConfiguration,
)
from fidesops.schemas.masking.masking_strategy_description import (
    MaskingStrategyDescription,
    MaskingStrategyConfigurationDescription,
)
from fidesops.service.masking.strategy.masking_strategy import MaskingStrategy


NULL_REWRITE = "null_rewrite"


class NullMaskingStrategy(MaskingStrategy):
    """Masks a value with a null value."""

    def __init__(
        self,
        configuration: NullMaskingConfiguration,
    ):
        """For parity with other MaskingStrategies, but for NullMaskingStrategy, nothing is pulled from the config"""

    def mask(self, value: Optional[str]) -> None:
        """Replaces the value with a null value"""
        return None

    @staticmethod
    def get_configuration_model() -> MaskingConfiguration:
        return NullMaskingConfiguration

    @staticmethod
    def get_description() -> MaskingStrategyDescription:
        return MaskingStrategyDescription(
            name=NULL_REWRITE,
            description="Masks the input value with a null value",
            configurations=[],
        )

    @staticmethod
    def data_type_supported(data_type: Optional[str]) -> bool:
        """Determines whether or not the given data type is supported by this masking strategy"""
        return True
