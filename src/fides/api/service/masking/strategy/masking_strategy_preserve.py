from typing import List, Optional, Type

from fides.api.schemas.masking.masking_configuration import PreserveMaskingConfiguration
from fides.api.schemas.masking.masking_strategy_description import (
    MaskingStrategyDescription,
)
from fides.api.service.masking.strategy.masking_strategy import MaskingStrategy


class PreserveMaskingStrategy(MaskingStrategy):
    """Preserves provided values as-is without any modifications."""

    name = "preserve"
    configuration_model = PreserveMaskingConfiguration

    def __init__(
        self,
        configuration: PreserveMaskingConfiguration,
    ):
        """For parity with other MaskingStrategies, but for PreserveMaskingStrategy, nothing is pulled from the config"""

    def mask(
        self, values: Optional[List[str]], request_id: Optional[str]
    ) -> Optional[List[str]]:
        """Returns the original values without any modifications"""
        return values

    def secrets_required(self) -> bool:
        return False

    @classmethod
    def get_description(cls: Type[MaskingStrategy]) -> MaskingStrategyDescription:
        return MaskingStrategyDescription(
            name=cls.name,
            description="Preserves the input values as-is without any modifications",
            configurations=[],
        )

    @staticmethod
    def data_type_supported(data_type: Optional[str]) -> bool:
        """Determines whether or not the given data type is supported by this masking strategy"""
        return True
