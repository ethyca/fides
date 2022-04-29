from fidesops.schemas.masking.masking_secrets import MaskingSecretCache, SecretType
from fidesops.service.masking.strategy.masking_strategy_hmac import (
    HmacMaskingStrategy,
    HMAC,
)
from fidesops.schemas.masking.masking_configuration import HmacMaskingConfiguration
from ....test_helpers.cache_secrets_helper import clear_cache_secrets, cache_secret

request_id = "1345134"


def test_hmac_sha_256():
    configuration = HmacMaskingConfiguration(algorithm="SHA-256")
    masker = HmacMaskingStrategy(configuration)
    expected = "df1e66dc2262ae3336f36294811f795b075900287e0a1add7974eacea8a52970"

    secret_key = MaskingSecretCache[str](
        secret="test_key", masking_strategy=HMAC, secret_type=SecretType.key
    )
    cache_secret(secret_key, request_id)
    secret_salt = MaskingSecretCache[str](
        secret="test_salt", masking_strategy=HMAC, secret_type=SecretType.salt
    )
    cache_secret(secret_salt, request_id)

    masked = masker.mask(["my_data"], request_id)[0]
    assert expected == masked
    clear_cache_secrets(request_id)


def test_mask_sha512():
    configuration = HmacMaskingConfiguration(algorithm="SHA-512")
    masker = HmacMaskingStrategy(configuration)
    expected = "0b4b968fa95510640bff35404ca89c146769e0a88cd4a6c15843176735a0820eec0f6580a21fd2b6b30f130cef01ccb4c5ab1d63387c4153ce8fc507e52efbaf"

    secret_key = MaskingSecretCache[str](
        secret="test_key", masking_strategy=HMAC, secret_type=SecretType.key
    )
    cache_secret(secret_key, request_id)
    secret_salt = MaskingSecretCache[str](
        secret="test_salt", masking_strategy=HMAC, secret_type=SecretType.salt
    )
    cache_secret(secret_salt, request_id)

    masked = masker.mask(["my_data"], request_id)[0]
    assert expected == masked
    clear_cache_secrets(request_id)


def test_mask_sha256_default():
    configuration = HmacMaskingConfiguration()
    masker = HmacMaskingStrategy(configuration)
    expected = "df1e66dc2262ae3336f36294811f795b075900287e0a1add7974eacea8a52970"

    secret_key = MaskingSecretCache[str](
        secret="test_key", masking_strategy=HMAC, secret_type=SecretType.key
    )
    cache_secret(secret_key, request_id)
    secret_salt = MaskingSecretCache[str](
        secret="test_salt", masking_strategy=HMAC, secret_type=SecretType.salt
    )
    cache_secret(secret_salt, request_id)

    masked = masker.mask(["my_data"], request_id)[0]
    assert expected == masked
    clear_cache_secrets(request_id)


def test_mask_sha256_default_multi_value():
    configuration = HmacMaskingConfiguration()
    masker = HmacMaskingStrategy(configuration)
    expected = "df1e66dc2262ae3336f36294811f795b075900287e0a1add7974eacea8a52970"
    expected2 = "fdc1f6389fbbb07174d4f15a4bbf0c0e2226a32ef2b288aa9a490e9fb91ce4bf"

    secret_key = MaskingSecretCache[str](
        secret="test_key", masking_strategy=HMAC, secret_type=SecretType.key
    )
    cache_secret(secret_key, request_id)
    secret_salt = MaskingSecretCache[str](
        secret="test_salt", masking_strategy=HMAC, secret_type=SecretType.salt
    )
    cache_secret(secret_salt, request_id)

    masked = masker.mask(["my_data", "my_other_data"], request_id)
    assert expected == masked[0]
    assert expected2 == masked[1]
    clear_cache_secrets(request_id)


def test_mask_arguments_null():
    configuration = HmacMaskingConfiguration()
    masker = HmacMaskingStrategy(configuration)
    expected = None

    secret_key = MaskingSecretCache[str](
        secret="test_key", masking_strategy=HMAC, secret_type=SecretType.key
    )
    cache_secret(secret_key, request_id)
    secret_salt = MaskingSecretCache[str](
        secret="test_salt", masking_strategy=HMAC, secret_type=SecretType.salt
    )
    cache_secret(secret_salt, request_id)

    masked = masker.mask(None, request_id)
    assert expected == masked
    clear_cache_secrets(request_id)
