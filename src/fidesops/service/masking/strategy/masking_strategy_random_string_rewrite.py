import string
from secrets import choice
from typing import List, Optional

from fidesops.schemas.masking.masking_configuration import (
    MaskingConfiguration,
    RandomStringMaskingConfiguration,
)
from fidesops.schemas.masking.masking_strategy_description import (
    MaskingStrategyConfigurationDescription,
    MaskingStrategyDescription,
)
from fidesops.service.masking.strategy.format_preservation import FormatPreservation
from fidesops.service.masking.strategy.masking_strategy import MaskingStrategy

RANDOM_STRING_REWRITE = "random_string_rewrite"


class RandomStringRewriteMaskingStrategy(MaskingStrategy):
    """Masks each provied value with a random string of the length specified in the configuration."""

    def __init__(
        self,
        configuration: RandomStringMaskingConfiguration,
    ):
        self.length = configuration.length
        self.format_preservation = configuration.format_preservation

    def mask(
        self, values: Optional[List[str]], request_id: Optional[str]
    ) -> Optional[List[str]]:
        """Replaces the value with a random lowercase string of the configured length"""
        if values is None:
            return None
        masked_values: List[str] = []
        for _ in range(len(values)):
            masked: str = "".join(
                [
                    choice(string.ascii_lowercase + string.digits)
                    for _ in range(self.length)
                ]
            )
            if self.format_preservation is not None:
                formatter = FormatPreservation(self.format_preservation)
                masked = formatter.format(masked)
            masked_values.append(masked)
        return masked_values

    def secrets_required(self) -> bool:
        return False

    @staticmethod
    def get_configuration_model() -> MaskingConfiguration:
        return RandomStringMaskingConfiguration

    @staticmethod
    def get_description() -> MaskingStrategyDescription:
        return MaskingStrategyDescription(
            name=RANDOM_STRING_REWRITE,
            description="Masks the input value with a random string of a specified length",
            configurations=[
                MaskingStrategyConfigurationDescription(
                    key="length",
                    description="Specifies the desired length of the randomized string.",
                )
            ],
        )

    @staticmethod
    def data_type_supported(data_type: Optional[str]) -> bool:
        """Determines whether or not the given data type is supported by this masking strategy"""
        supported_data_types = {"string"}
        return data_type in supported_data_types
