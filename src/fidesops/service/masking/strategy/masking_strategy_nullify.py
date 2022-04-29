from typing import Optional, List

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
    """Masks provided values each with a null value."""

    def __init__(
        self,
        configuration: NullMaskingConfiguration,
    ):
        """For parity with other MaskingStrategies, but for NullMaskingStrategy, nothing is pulled from the config"""

    def mask(
        self, values: Optional[List[str]], privacy_request_id: Optional[str]
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
