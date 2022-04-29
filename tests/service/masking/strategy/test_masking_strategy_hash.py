from fidesops.schemas.masking.masking_configuration import HashMaskingConfiguration
from fidesops.schemas.masking.masking_secrets import MaskingSecretCache, SecretType
from fidesops.service.masking.strategy.masking_strategy_hash import (
    HashMaskingStrategy,
    HASH,
)
from ....test_helpers.cache_secrets_helper import clear_cache_secrets, cache_secret

request_id = "1345134"


def test_mask_sha256():
    configuration = HashMaskingConfiguration(algorithm="SHA-256")
    masker = HashMaskingStrategy(configuration)
    expected = "1c015e801323afa54bde5e4d510809e6b5f14ad9b9961c48cbd7143106b6e596"

    secret = MaskingSecretCache[str](
        secret="adobo", masking_strategy=HASH, secret_type=SecretType.salt
    )
    cache_secret(secret, request_id)

    masked = masker.mask(["monkey"], request_id)[0]
    assert expected == masked
    clear_cache_secrets(request_id)


def test_mask_sha512():
    configuration = HashMaskingConfiguration(algorithm="SHA-512")
    masker = HashMaskingStrategy(configuration)
    expected = "527ca44f5c95400d161c503e6ddad7be01941ec9e7a03c2201338a16ba8a36bb765a430bd6b276a590661154f3f743a3a91efecd056645b4ea13b4b8cf39e8e3"

    secret = MaskingSecretCache[str](
        secret="adobo", masking_strategy=HASH, secret_type=SecretType.salt
    )
    cache_secret(secret, request_id)

    masked = masker.mask(["monkey"], request_id)[0]
    assert expected == masked
    clear_cache_secrets(request_id)


def test_mask_sha256_default():
    configuration = HashMaskingConfiguration()
    masker = HashMaskingStrategy(configuration)
    expected = "1c015e801323afa54bde5e4d510809e6b5f14ad9b9961c48cbd7143106b6e596"

    secret = MaskingSecretCache[str](
        secret="adobo", masking_strategy=HASH, secret_type=SecretType.salt
    )
    cache_secret(secret, request_id)

    masked = masker.mask(["monkey"], request_id)[0]
    assert expected == masked
    clear_cache_secrets(request_id)


def test_mask_sha256_default_multi_value():
    configuration = HashMaskingConfiguration()
    masker = HashMaskingStrategy(configuration)
    expected = "1c015e801323afa54bde5e4d510809e6b5f14ad9b9961c48cbd7143106b6e596"
    expected2 = "f37d3290343da298f2471fa8cff444d242052529e4fa27a1b9361bd1fdc02fd4"

    secret = MaskingSecretCache[str](
        secret="adobo", masking_strategy=HASH, secret_type=SecretType.salt
    )
    cache_secret(secret, request_id)

    masked = masker.mask(["monkey", "tiger"], request_id)
    assert expected == masked[0]
    assert expected2 == masked[1]
    clear_cache_secrets(request_id)


def test_mask_arguments_null():
    configuration = HashMaskingConfiguration()
    masker = HashMaskingStrategy(configuration)
    expected = None

    secret = MaskingSecretCache[str](
        secret="adobo", masking_strategy=HASH, secret_type=SecretType.salt
    )
    cache_secret(secret, request_id)

    masked = masker.mask(None, request_id)
    assert expected == masked
    clear_cache_secrets(request_id)
