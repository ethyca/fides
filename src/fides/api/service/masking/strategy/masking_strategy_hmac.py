from __future__ import annotations

from typing import Dict, List, Optional, Type

from fides.api.schemas.masking.masking_configuration import HmacMaskingConfiguration
from fides.api.schemas.masking.masking_secrets import (
    MaskingSecretCache,
    MaskingSecretMeta,
    SecretType,
)
from fides.api.schemas.masking.masking_strategy_description import (
    MaskingStrategyConfigurationDescription,
    MaskingStrategyDescription,
)
from fides.api.service.masking.strategy.format_preservation import FormatPreservation
from fides.api.service.masking.strategy.masking_strategy import MaskingStrategy
from fides.api.util.encryption.hmac_encryption_scheme import hmac_encrypt_return_str
from fides.api.util.encryption.secrets_util import SecretsUtil


class HmacMaskingStrategy(MaskingStrategy):
    """
    Masks a value by generating a hash using a hash algorithm and a required secret key.  One of the differences
    between this and the HashMaskingStrategy is the required secret key."""

    name = "hmac"
    configuration_model = HmacMaskingConfiguration

    def __init__(
        self,
        configuration: HmacMaskingConfiguration,
    ):
        self.algorithm = configuration.algorithm
        self.format_preservation = configuration.format_preservation

    def mask(
        self, values: Optional[List[str]], request_id: Optional[str]
    ) -> Optional[List[Optional[str]]]:
        """
        Returns a hash using the hmac algorithm, generating a hash of each of the supplied value and the secret hmac_key.
        Returns None if the provided value is None.
        """
        if values is None:
            return None

        masking_meta: Dict[SecretType, MaskingSecretMeta] = (
            self._build_masking_secret_meta()
        )
        key: str | None = SecretsUtil.get_or_generate_secret(
            request_id, SecretType.key, masking_meta[SecretType.key]
        )
        salt: str | None = SecretsUtil.get_or_generate_secret(
            request_id, SecretType.salt, masking_meta[SecretType.salt]
        )

        masked_values: List[Optional[str]] = []
        for value in values:
            if value is None:
                masked_values.append(None)
                continue
            masked: str = hmac_encrypt_return_str(str(value), key, salt, self.algorithm)  # type: ignore
            if self.format_preservation is not None:
                formatter = FormatPreservation(self.format_preservation)
                masked = formatter.format(masked)
            masked_values.append(masked)
        return masked_values

    def secrets_required(self) -> bool:
        return True

    def generate_secrets_for_cache(self) -> List[MaskingSecretCache]:
        masking_meta: Dict[SecretType, MaskingSecretMeta] = (
            self._build_masking_secret_meta()
        )
        return SecretsUtil.build_masking_secrets_for_cache(masking_meta)

    @classmethod
    def get_description(cls: Type[MaskingStrategy]) -> MaskingStrategyDescription:
        return MaskingStrategyDescription(
            name=cls.name,
            description="Masks the input value by using the HMAC algorithm along with a hashed version of the data "
            "and a secret key.",
            configurations=[
                MaskingStrategyConfigurationDescription(
                    key="algorithm",
                    description="Specifies the hashing algorithm to be used. Can be SHA-256 or "
                    "SHA-512. If not provided, default is SHA-256",
                ),
                MaskingStrategyConfigurationDescription(
                    key="format_preservation",
                    description="Option to preserve format in masking, with a provided suffix",
                ),
            ],
        )

    @staticmethod
    def data_type_supported(data_type: Optional[str]) -> bool:
        """Determines whether or not the given data type is supported by this masking strategy"""
        supported_data_types = {"string"}
        return data_type in supported_data_types

    @classmethod
    def _build_masking_secret_meta(
        cls: Type[MaskingStrategy],
    ) -> Dict[SecretType, MaskingSecretMeta]:
        return {
            SecretType.key: MaskingSecretMeta[str](
                masking_strategy=cls.name,
                generate_secret_func=SecretsUtil.generate_secret_string,
            ),
            SecretType.salt: MaskingSecretMeta[str](
                masking_strategy=cls.name,
                generate_secret_func=SecretsUtil.generate_secret_string,
            ),
        }
