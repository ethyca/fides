from __future__ import annotations

import hashlib
from typing import Dict, List, Optional, Type

from fides.api.ops.schemas.masking.masking_configuration import HashMaskingConfiguration
from fides.api.ops.schemas.masking.masking_secrets import (
    MaskingSecretCache,
    MaskingSecretMeta,
    SecretType,
)
from fides.api.ops.schemas.masking.masking_strategy_description import (
    MaskingStrategyConfigurationDescription,
    MaskingStrategyDescription,
)
from fides.api.ops.service.masking.strategy.format_preservation import (
    FormatPreservation,
)
from fides.api.ops.service.masking.strategy.masking_strategy import MaskingStrategy
from fides.api.ops.util.encryption.secrets_util import SecretsUtil
from fides.core.config import get_config

CONFIG = get_config()


class HashMaskingStrategy(MaskingStrategy):
    """Masks a value by hashing it"""

    name = "hash"
    configuration_model = HashMaskingConfiguration

    def __init__(
        self,
        configuration: HashMaskingConfiguration,
    ):
        self.algorithm = configuration.algorithm
        if self.algorithm == HashMaskingConfiguration.Algorithm.SHA_256:
            self.algorithm_function = self._hash_sha256
        elif self.algorithm == HashMaskingConfiguration.Algorithm.SHA_512:
            self.algorithm_function = self._hash_sha512
        self.format_preservation = configuration.format_preservation

    def mask(
        self, values: Optional[List[str]], request_id: Optional[str]
    ) -> Optional[List[str]]:
        """Returns the hashed version of the provided values. Returns None if the provided value
        is None"""
        if values is None:
            return None
        masking_meta: Dict[
            SecretType, MaskingSecretMeta
        ] = self._build_masking_secret_meta()
        salt: str | None = SecretsUtil.get_or_generate_secret(
            request_id,
            SecretType.salt,
            masking_meta[SecretType.salt],
        )

        masked_values: List[str] = []
        for value in values:
            masked: str = self.algorithm_function(value, salt)  # type: ignore
            if self.format_preservation is not None:
                formatter = FormatPreservation(self.format_preservation)
                masked = formatter.format(masked)
            masked_values.append(masked)
        return masked_values

    def secrets_required(self) -> bool:
        return True

    def generate_secrets_for_cache(self) -> List[MaskingSecretCache]:
        masking_meta: Dict[
            SecretType, MaskingSecretMeta
        ] = self._build_masking_secret_meta()
        return SecretsUtil.build_masking_secrets_for_cache(masking_meta)

    # MR Note - We will need a way to ensure that this does not fall out of date. Given that it
    # includes subjective instructions, this is not straightforward to automate
    @classmethod
    def get_description(cls: Type[MaskingStrategy]) -> MaskingStrategyDescription:
        return MaskingStrategyDescription(
            name=cls.name,
            description="Masks the input value by returning a hashed version of the input value",
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

    # Helpers

    @staticmethod
    def _hash_sha256(value: str, salt: str) -> str:
        return hashlib.sha256(
            (value + salt).encode(CONFIG.security.encoding)
        ).hexdigest()

    @staticmethod
    def _hash_sha512(value: str, salt: str) -> str:
        return hashlib.sha512(
            (value + salt).encode(CONFIG.security.encoding)
        ).hexdigest()

    @classmethod
    def _build_masking_secret_meta(
        cls: Type[MaskingStrategy],
    ) -> Dict[SecretType, MaskingSecretMeta]:
        return {
            SecretType.salt: MaskingSecretMeta[str](
                masking_strategy=cls.name,
                generate_secret_func=SecretsUtil.generate_secret_string,
            )
        }
