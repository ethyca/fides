from typing import Dict, List, Optional

from fidesops.schemas.masking.masking_configuration import (
    AesEncryptionMaskingConfiguration,
    HmacMaskingConfiguration,
    MaskingConfiguration,
)
from fidesops.schemas.masking.masking_secrets import (
    MaskingSecretCache,
    MaskingSecretMeta,
    SecretType,
)
from fidesops.schemas.masking.masking_strategy_description import (
    MaskingStrategyConfigurationDescription,
    MaskingStrategyDescription,
)
from fidesops.service.masking.strategy.format_preservation import FormatPreservation
from fidesops.service.masking.strategy.masking_strategy import MaskingStrategy
from fidesops.util.encryption.aes_gcm_encryption_scheme import encrypt
from fidesops.util.encryption.hmac_encryption_scheme import hmac_encrypt_return_bytes
from fidesops.util.encryption.secrets_util import SecretsUtil

AES_ENCRYPT = "aes_encrypt"


class AesEncryptionMaskingStrategy(MaskingStrategy):
    def __init__(self, configuration: AesEncryptionMaskingConfiguration):
        self.mode = configuration.mode
        self.format_preservation = configuration.format_preservation

    def mask(
        self, values: Optional[List[str]], request_id: Optional[str]
    ) -> Optional[List[str]]:
        if values is None:
            return None
        if self.mode == AesEncryptionMaskingConfiguration.Mode.GCM:
            masking_meta: Dict[
                SecretType, MaskingSecretMeta
            ] = self._build_masking_secret_meta()
            key: bytes = SecretsUtil.get_or_generate_secret(
                request_id, SecretType.key, masking_meta[SecretType.key]
            )
            key_hmac: str = SecretsUtil.get_or_generate_secret(
                request_id,
                SecretType.key_hmac,
                masking_meta[SecretType.key_hmac],
            )
            # The nonce is generated deterministically such that the same input val will result in same nonce
            # and therefore the same masked val through the aes strategy. This is called convergent encryption, with this
            # implementation loosely based on https://www.vaultproject.io/docs/secrets/transit#convergent-encryption

            masked_values: List[str] = []
            for value in values:
                nonce: bytes = self._generate_nonce(
                    value, key_hmac, request_id, masking_meta
                )
                masked: str = encrypt(value, key, nonce)
                if self.format_preservation is not None:
                    formatter = FormatPreservation(self.format_preservation)
                    masked = formatter.format(masked)
                masked_values.append(masked)
            return masked_values

        raise ValueError(f"aes_mode {self.mode} is not supported")

    def secrets_required(self) -> bool:
        return True

    def generate_secrets_for_cache(self) -> List[MaskingSecretCache]:
        masking_meta: Dict[
            SecretType, MaskingSecretMeta
        ] = self._build_masking_secret_meta()
        return SecretsUtil.build_masking_secrets_for_cache(masking_meta)

    @staticmethod
    def get_configuration_model() -> MaskingConfiguration:
        """Used to get the configuration model to configure the strategy"""
        return AesEncryptionMaskingConfiguration

    @staticmethod
    def get_description() -> MaskingStrategyDescription:
        """Returns the description used for documentation. In particular, used by the
        documentation endpoint in masking_endpoints.list_masking_strategies"""
        return MaskingStrategyDescription(
            name=AES_ENCRYPT,
            description="Masks by encrypting the value using AES",
            configurations=[
                MaskingStrategyConfigurationDescription(
                    key="mode",
                    description="Specifies the algorithm mode. Default is GCM if not provided.",
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

    @staticmethod
    def _generate_nonce(
        value: Optional[str],
        key: str,
        privacy_request_id: Optional[str],
        masking_meta: Dict[SecretType, MaskingSecretMeta],
    ) -> bytes:
        salt: str = SecretsUtil.get_or_generate_secret(
            privacy_request_id, SecretType.salt_hmac, masking_meta[SecretType.salt_hmac]
        )
        # Trim to 12 bytes, which is recommended length from aes gcm lib:
        # https://cryptography.io/en/latest/hazmat/primitives/aead/#cryptography.hazmat.primitives.ciphers.aead.AESGCM.encrypt
        return hmac_encrypt_return_bytes(
            value, key, salt, HmacMaskingConfiguration.Algorithm.sha_256
        )[:12]

    @staticmethod
    def _build_masking_secret_meta() -> Dict[SecretType, MaskingSecretMeta]:
        return {
            SecretType.key: MaskingSecretMeta[bytes](
                masking_strategy=AES_ENCRYPT,
                generate_secret_func=SecretsUtil.generate_secret_bytes,
            ),
            SecretType.key_hmac: MaskingSecretMeta[str](
                masking_strategy=AES_ENCRYPT,
                generate_secret_func=SecretsUtil.generate_secret_string,
            ),
            SecretType.salt_hmac: MaskingSecretMeta[str](
                masking_strategy=AES_ENCRYPT,
                generate_secret_func=SecretsUtil.generate_secret_string,
            ),
        }
