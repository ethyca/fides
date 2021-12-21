import string
from typing import Optional
from secrets import choice

from fidesops.schemas.masking.masking_configuration import (
    RandomStringMaskingConfiguration,
    MaskingConfiguration,
)
from fidesops.schemas.masking.masking_strategy_description import (
    MaskingStrategyDescription,
    MaskingStrategyConfigurationDescription,
)
from fidesops.service.masking.strategy.format_preservation import FormatPreservation
from fidesops.service.masking.strategy.masking_strategy import MaskingStrategy


RANDOM_STRING_REWRITE = "random_string_rewrite"


class RandomStringRewriteMaskingStrategy(MaskingStrategy):
    """Masks a value with a random string of the length specified in the configuration."""

    def __init__(
        self,
        configuration: RandomStringMaskingConfiguration,
    ):
        self.length = configuration.length
        self.format_preservation = configuration.format_preservation

    def mask(
        self, value: Optional[str], privacy_request_id: Optional[str]
    ) -> Optional[str]:
        """Replaces the value with a random lowercase string of the configured length"""
        if value is None:
            return None
        masked: str = "".join(
            [choice(string.ascii_lowercase + string.digits) for _ in range(self.length)]
        )
        if self.format_preservation is not None:
            formatter = FormatPreservation(self.format_preservation)
            return formatter.format(masked)
        return masked

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
