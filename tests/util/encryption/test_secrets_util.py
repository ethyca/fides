from typing import Dict, List

from fidesops.schemas.masking.masking_secrets import (
    MaskingSecretCache,
    MaskingSecretMeta,
    SecretType,
)
from fidesops.service.masking.strategy.masking_strategy_aes_encrypt import AES_ENCRYPT
from fidesops.service.masking.strategy.masking_strategy_hmac import (
    HMAC,
    HmacMaskingStrategy,
)
from fidesops.util.encryption.secrets_util import SecretsUtil

from ...test_helpers.cache_secrets_helper import cache_secret, clear_cache_secrets

request_id = "12345"


def test_get_secret_from_cache_str() -> None:
    # build masking secret meta for HMAC key
    masking_meta_key: Dict[SecretType, MaskingSecretMeta] = {
        SecretType.key: MaskingSecretMeta[str](
            masking_strategy=HMAC,
            generate_secret_func=SecretsUtil.generate_secret_string,
        )
    }

    # cache secrets for HMAC
    secret_key = MaskingSecretCache[str](
        secret="test_key", masking_strategy=HMAC, secret_type=SecretType.key
    )
    cache_secret(secret_key, request_id)

    result: str = SecretsUtil.get_or_generate_secret(
        request_id, SecretType.key, masking_meta_key[SecretType.key]
    )
    assert result == "test_key"
    clear_cache_secrets(request_id)


def test_get_secret_from_cache_bytes() -> None:
    # build masking secret meta for AES key
    masking_meta_key: Dict[SecretType, MaskingSecretMeta] = {
        SecretType.key: MaskingSecretMeta[bytes](
            masking_strategy=AES_ENCRYPT,
            generate_secret_func=SecretsUtil.generate_secret_bytes,
        )
    }

    # cache secret AES key
    secret_key = MaskingSecretCache[str](
        secret=b"\x94Y\xa8Z", masking_strategy=AES_ENCRYPT, secret_type=SecretType.key
    )
    cache_secret(secret_key, request_id)

    result: str = SecretsUtil.get_or_generate_secret(
        request_id, SecretType.key, masking_meta_key[SecretType.key]
    )
    assert result == b"\x94Y\xa8Z"
    clear_cache_secrets(request_id)


def test_generate_secret() -> None:
    # build masking secret meta for HMAC key
    masking_meta_key: Dict[SecretType, MaskingSecretMeta] = {
        SecretType.key: MaskingSecretMeta[str](
            masking_strategy=HMAC,
            generate_secret_func=SecretsUtil.generate_secret_string,
        )
    }

    result: str = SecretsUtil.get_or_generate_secret(
        None, SecretType.key, masking_meta_key[SecretType.key]
    )
    assert result


def test_build_masking_secrets_for_cache() -> None:
    # build masking secret meta for all HMAC secrets
    masking_meta: Dict[
        SecretType, MaskingSecretMeta
    ] = HmacMaskingStrategy._build_masking_secret_meta()
    result: List[MaskingSecretCache] = SecretsUtil.build_masking_secrets_for_cache(
        masking_meta
    )
    assert len(result) == 2
