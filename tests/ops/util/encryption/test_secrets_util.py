from typing import Dict, List

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.masking.masking_secrets import (
    MaskingSecretCache,
    MaskingSecretMeta,
    SecretType,
)
from fides.api.service.masking.strategy.masking_strategy_aes_encrypt import (
    AesEncryptionMaskingStrategy,
)
from fides.api.service.masking.strategy.masking_strategy_hmac import HmacMaskingStrategy
from fides.api.util.encryption.secrets_util import SecretsUtil

from ...test_helpers.cache_secrets_helper import cache_secret, clear_cache_secrets

# We will eventually stop storing the secrets in Redis but we'll keep these cache tests
# here to make sure that we're able to read both from Redis and from the database
# during the transition period.


def test_get_secret_from_cache_str(privacy_request: PrivacyRequest) -> None:
    # build masking secret meta for HMAC key
    masking_meta_key: Dict[SecretType, MaskingSecretMeta] = {
        SecretType.key: MaskingSecretMeta[str](
            masking_strategy=HmacMaskingStrategy.name,
            generate_secret_func=SecretsUtil.generate_secret_string,
        )
    }

    # cache secrets for HMAC
    secret_key = MaskingSecretCache[str](
        secret="test_key",
        masking_strategy=HmacMaskingStrategy.name,
        secret_type=SecretType.key,
    )
    cache_secret(secret_key, privacy_request.id)

    result: str = SecretsUtil.get_or_generate_secret(
        privacy_request.id, SecretType.key, masking_meta_key[SecretType.key]
    )
    assert result == "test_key"
    clear_cache_secrets(privacy_request.id)


def test_get_secret_from_cache_bytes(privacy_request: PrivacyRequest) -> None:
    # build masking secret meta for AES key
    masking_meta_key: Dict[SecretType, MaskingSecretMeta] = {
        SecretType.key: MaskingSecretMeta[bytes](
            masking_strategy=AesEncryptionMaskingStrategy.name,
            generate_secret_func=SecretsUtil.generate_secret_bytes,
        )
    }

    # cache secret AES key
    secret_key = MaskingSecretCache[str](
        secret=b"\x94Y\xa8Z",
        masking_strategy=AesEncryptionMaskingStrategy.name,
        secret_type=SecretType.key,
    )
    cache_secret(secret_key, privacy_request.id)

    result: str = SecretsUtil.get_or_generate_secret(
        privacy_request.id, SecretType.key, masking_meta_key[SecretType.key]
    )
    assert result == b"\x94Y\xa8Z"
    clear_cache_secrets(privacy_request.id)


def test_get_secret_from_db_str(privacy_request: PrivacyRequest) -> None:
    # build masking secret meta for HMAC key
    masking_meta_key: Dict[SecretType, MaskingSecretMeta] = {
        SecretType.key: MaskingSecretMeta[str](
            masking_strategy=HmacMaskingStrategy.name,
            generate_secret_func=SecretsUtil.generate_secret_string,
        )
    }

    # cache secrets for HMAC
    secret_key = MaskingSecretCache[str](
        secret="test_key",
        masking_strategy=HmacMaskingStrategy.name,
        secret_type=SecretType.key,
    )
    privacy_request.persist_masking_secrets([secret_key])

    result: str = SecretsUtil.get_or_generate_secret(
        privacy_request.id, SecretType.key, masking_meta_key[SecretType.key]
    )
    assert result == "test_key"


def test_get_secret_from_db_bytes(privacy_request: PrivacyRequest) -> None:
    # build masking secret meta for AES key
    masking_meta_key: Dict[SecretType, MaskingSecretMeta] = {
        SecretType.key: MaskingSecretMeta[bytes](
            masking_strategy=AesEncryptionMaskingStrategy.name,
            generate_secret_func=SecretsUtil.generate_secret_bytes,
        )
    }

    # cache secret AES key
    secret_key = MaskingSecretCache[str](
        secret=b"\x94Y\xa8Z",
        masking_strategy=AesEncryptionMaskingStrategy.name,
        secret_type=SecretType.key,
    )
    privacy_request.persist_masking_secrets([secret_key])

    result: str = SecretsUtil.get_or_generate_secret(
        privacy_request.id, SecretType.key, masking_meta_key[SecretType.key]
    )
    assert result == b"\x94Y\xa8Z"


def test_generate_secret() -> None:
    # build masking secret meta for HMAC key
    masking_meta_key: Dict[SecretType, MaskingSecretMeta] = {
        SecretType.key: MaskingSecretMeta[str](
            masking_strategy=HmacMaskingStrategy.name,
            generate_secret_func=SecretsUtil.generate_secret_string,
        )
    }

    result: str = SecretsUtil.get_or_generate_secret(
        None, SecretType.key, masking_meta_key[SecretType.key]
    )
    assert result


def test_build_masking_secrets_for_cache() -> None:
    # build masking secret meta for all HMAC secrets
    masking_meta: Dict[SecretType, MaskingSecretMeta] = (
        HmacMaskingStrategy._build_masking_secret_meta()
    )
    result: List[MaskingSecretCache] = SecretsUtil.build_masking_secrets_for_cache(
        masking_meta
    )
    assert len(result) == 2
