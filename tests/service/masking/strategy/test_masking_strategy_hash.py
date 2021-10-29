from fidesops.schemas.masking.masking_configuration import HashMaskingConfiguration
from fidesops.service.masking.strategy.masking_strategy_hash import HashMaskingStrategy


def test_mask_sha256_with_salt():
    configuration = HashMaskingConfiguration(algorithm="SHA-256", salt="adobo")
    masker = HashMaskingStrategy(configuration)
    expected = "1c015e801323afa54bde5e4d510809e6b5f14ad9b9961c48cbd7143106b6e596"

    masked = masker.mask("monkey")
    assert expected == masked


def test_mask_sha256_without_salt():
    configuration = HashMaskingConfiguration(algorithm="SHA-256")
    masker = HashMaskingStrategy(configuration)
    expected = "000c285457fc971f862a79b786476c78812c8897063c6fa9c045f579a3b2d63f"

    masked = masker.mask("monkey")
    assert expected == masked


def test_mask_sha512_with_salt():
    configuration = HashMaskingConfiguration(algorithm="SHA-512", salt="adobo")
    masker = HashMaskingStrategy(configuration)
    expected = "527ca44f5c95400d161c503e6ddad7be01941ec9e7a03c2201338a16ba8a36bb765a430bd6b276a590661154f3f743a3a91efecd056645b4ea13b4b8cf39e8e3"

    masked = masker.mask("monkey")
    assert expected == masked


def test_mask_sha512_without_salt():
    configuration = HashMaskingConfiguration(algorithm="SHA-512")
    masker = HashMaskingStrategy(configuration)
    expected = "65a0ef45df509ad1cf01501b2a1b12cc2fbac0f00a31ae6f3ddc361396955216fb3a4d84e18dc1065dff311e3943878bc0bdb8a60caefd2fbdc6b2a757a3204b"

    masked = masker.mask("monkey")
    assert expected == masked


def test_mask_sha256_default():
    configuration = HashMaskingConfiguration()
    masker = HashMaskingStrategy(configuration)
    expected = "000c285457fc971f862a79b786476c78812c8897063c6fa9c045f579a3b2d63f"

    masked = masker.mask("monkey")
    assert expected == masked


def test_mask_arguments_null():
    configuration = HashMaskingConfiguration()
    masker = HashMaskingStrategy(configuration)
    expected = None

    masked = masker.mask(None)
    assert expected == masked
