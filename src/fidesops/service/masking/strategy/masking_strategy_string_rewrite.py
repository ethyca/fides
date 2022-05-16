from typing import List, Optional

from fidesops.schemas.masking.masking_configuration import (
    MaskingConfiguration,
    StringRewriteMaskingConfiguration,
)
from fidesops.schemas.masking.masking_strategy_description import (
    MaskingStrategyConfigurationDescription,
    MaskingStrategyDescription,
)
from fidesops.service.masking.strategy.format_preservation import FormatPreservation
from fidesops.service.masking.strategy.masking_strategy import MaskingStrategy

STRING_REWRITE = "string_rewrite"


class StringRewriteMaskingStrategy(MaskingStrategy):
    """Masks the values with a pre-determined value"""

    def __init__(
        self,
        configuration: StringRewriteMaskingConfiguration,
    ):
        self.rewrite_value = configuration.rewrite_value
        self.format_preservation = configuration.format_preservation

    def mask(
        self, values: Optional[List[str]], request_id: Optional[str]
    ) -> Optional[List[str]]:
        """Replaces the value with the value specified in strategy spec. Returns None if input is
        None"""
        if values is None:
            return None
        masked_values: List[str] = []
        for _ in range(len(values)):
            if self.format_preservation is not None:
                formatter = FormatPreservation(self.format_preservation)
                masked_values.append(formatter.format(self.rewrite_value))
            else:
                masked_values.append(self.rewrite_value)
        return masked_values

    def secrets_required(self) -> bool:
        return False

    @staticmethod
    def get_configuration_model() -> MaskingConfiguration:
        return StringRewriteMaskingConfiguration

    # MR Note - We will need a way to ensure that this does not fall out of date. Given that it
    # includes subjective instructions, this is not straightforward to automate
    @staticmethod
    def get_description() -> MaskingStrategyDescription:
        return MaskingStrategyDescription(
            name=STRING_REWRITE,
            description="Masks the input value with a default string value",
            configurations=[
                MaskingStrategyConfigurationDescription(
                    key="rewrite_value",
                    description="The string that will replace existing values",
                )
            ],
        )

    @staticmethod
    def data_type_supported(data_type: Optional[str]) -> bool:
        """Determines whether or not the given data type is supported by this masking strategy"""
        supported_data_types = {"string"}
        return data_type in supported_data_types
