import hashlib
import hmac
from typing import Optional, Callable

from fidesops.core.config import config
from fidesops.schemas.masking.masking_configuration import (
    MaskingConfiguration,
    HmacMaskingConfiguration,
)
from fidesops.schemas.masking.masking_strategy_description import (
    MaskingStrategyDescription,
    MaskingStrategyConfigurationDescription,
)
from fidesops.service.masking.strategy.format_preservation import FormatPreservation
from fidesops.service.masking.strategy.masking_strategy import MaskingStrategy


HMAC = "hmac"


class HmacMaskingStrategy(MaskingStrategy):
    """
    Masks a value by generating a hash using a hash algorithm and a required secret key.  One of the differences
    between this and the HashMaskingStrategy is the required secret key."""

    def __init__(
        self,
        configuration: HmacMaskingConfiguration,
    ):
        self.algorithm = configuration.algorithm
        algorithm_function_mapping = {
            HmacMaskingConfiguration.Algorithm.sha_256: self._hmac_sha256,
            HmacMaskingConfiguration.Algorithm.sha_512: self._hmac_sha512,
        }

        self.algorithm_function = algorithm_function_mapping.get(self.algorithm)
        self.hmac_key = configuration.hmac_key
        self.salt = configuration.salt
        self.format_preservation = configuration.format_preservation

    def mask(self, value: Optional[str]) -> Optional[str]:
        """
        Returns a hash using the hmac algorithm, generating a hash of the supplied value and the secret hmac_key.
        Returns None if the provided value is None.
        """
        if value is None:
            return None
        masked: str = self.algorithm_function(value, self.hmac_key, self.salt)
        if self.format_preservation is not None:
            formatter = FormatPreservation(self.format_preservation)
            return formatter.format(masked)
        return masked

    @staticmethod
    def get_configuration_model() -> MaskingConfiguration:
        return HmacMaskingConfiguration

    @staticmethod
    def get_description() -> MaskingStrategyDescription:
        return MaskingStrategyDescription(
            name=HMAC,
            description="Masks the input value by using the HMAC algorithm along with a hashed version of the data "
            "and a secret key.",
            configurations=[
                MaskingStrategyConfigurationDescription(
                    key="algorithm",
                    description="Specifies the hashing algorithm to be used. Can be SHA-256 or "
                    "SHA-512. If not provided, default is SHA-256",
                ),
                MaskingStrategyConfigurationDescription(
                    key="hmac_key",
                    description="Specifies the secret key to be used in conjunction with the hash.",
                ),
                MaskingStrategyConfigurationDescription(
                    key="salt",
                    description="Specifies optional salt that can be added to the value we're hashing.",
                ),
            ],
        )

    # Helpers
    @staticmethod
    def _hmac_sha256(value: str, hmac_key: str, salt: str) -> str:
        """Creates a new hmac object using the sh256 hash algorithm and the hmac_key and then returns the hexdigest."""
        return _hmac(
            value=value, hmac_key=hmac_key, salt=salt, hashing_alg=hashlib.sha256
        )

    @staticmethod
    def _hmac_sha512(value: str, hmac_key: str, salt: str) -> str:
        """Creates a new hmac object using the sha512 hash algorithm and the hmac_key and then returns the hexdigest."""
        return _hmac(
            value=value, hmac_key=hmac_key, salt=salt, hashing_alg=hashlib.sha512
        )


def _hmac(value: str, hmac_key: str, salt: str, hashing_alg: Callable) -> str:
    """Generic HMAC algorithm"""
    return hmac.new(
        key=hmac_key.encode(config.security.ENCODING),
        msg=(value + salt).encode(config.security.ENCODING),
        digestmod=hashing_alg,
    ).hexdigest()
