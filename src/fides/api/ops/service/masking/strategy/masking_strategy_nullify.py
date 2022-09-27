from typing import List, Optional, Type

from fides.api.ops.schemas.masking.masking_configuration import NullMaskingConfiguration
from fides.api.ops.schemas.masking.masking_strategy_description import (
    MaskingStrategyDescription,
)
from fides.api.ops.service.masking.strategy.masking_strategy import MaskingStrategy


class NullMaskingStrategy(MaskingStrategy):
    """Masks provided values each with a null value."""

    name = "null_rewrite"
    configuration_model = NullMaskingConfiguration

    def __init__(
        self,
        configuration: NullMaskingConfiguration,
    ):
        """For parity with other MaskingStrategies, but for NullMaskingStrategy, nothing is pulled from the config"""

    def mask(
        self, values: Optional[List[str]], request_id: Optional[str]
    ) -> Optional[List[None]]:
        """Replaces the value with a null value"""
        if values is None:
            return None
        masked_values: List[None] = []
        for _ in range(len(values)):
            masked_values.append(None)
        return masked_values

    def secrets_required(self) -> bool:
        return False

    @classmethod
    def get_description(cls: Type[MaskingStrategy]) -> MaskingStrategyDescription:
        return MaskingStrategyDescription(
            name=cls.name,
            description="Masks the input value with a null value",
            configurations=[],
        )

    @staticmethod
    def data_type_supported(data_type: Optional[str]) -> bool:
        """Determines whether or not the given data type is supported by this masking strategy"""
        return True
