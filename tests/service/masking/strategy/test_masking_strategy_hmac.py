from fidesops.service.masking.strategy.masking_strategy_hmac import HmacMaskingStrategy
from fidesops.schemas.masking.masking_configuration import HmacMaskingConfiguration


def test_hmac_sha_256():
    configuration = HmacMaskingConfiguration(algorithm="SHA-256", hmac_key="test_key")
    masker = HmacMaskingStrategy(configuration)
    expected = "1d84bde40b344149a4fcb7e48030dab21d6b35e21a65eba33687132586977081"

    masked = masker.mask("my_data")
    assert expected == masked


def test_hmac_sha_256_with_optional_salt():
    configuration = HmacMaskingConfiguration(
        algorithm="SHA-256", hmac_key="test_key", salt="test_salt"
    )
    masker = HmacMaskingStrategy(configuration)
    expected = "df1e66dc2262ae3336f36294811f795b075900287e0a1add7974eacea8a52970"

    masked = masker.mask("my_data")
    assert expected == masked


def test_mask_sha512():
    configuration = HmacMaskingConfiguration(algorithm="SHA-512", hmac_key="test_key")
    masker = HmacMaskingStrategy(configuration)
    expected = (
        "2d6805864fdee15f4c6a0e809fada0db3043d0e219383b8395b1dae797db680bb0446bcddf71f633f3a6e8970a6952"
        "7b47f304563f4f061d01712cfe34fc449e"
    )

    masked = masker.mask("my_data")
    assert expected == masked


def test_hmac_sha_512_with_optional_salt():
    configuration = HmacMaskingConfiguration(
        algorithm="SHA-512", hmac_key="test_key", salt="test_salt"
    )
    masker = HmacMaskingStrategy(configuration)
    expected = (
        "0b4b968fa95510640bff35404ca89c146769e0a88cd4a6c15843176735a0820eec0f6580a21fd2b6b30f130cef01ccb4c"
        "5ab1d63387c4153ce8fc507e52efbaf"
    )

    masked = masker.mask("my_data")
    assert expected == masked


def test_mask_sha256_default():
    configuration = HmacMaskingConfiguration(hmac_key="test_key")
    masker = HmacMaskingStrategy(configuration)
    expected = "1d84bde40b344149a4fcb7e48030dab21d6b35e21a65eba33687132586977081"

    masked = masker.mask("my_data")
    assert expected == masked


def test_mask_arguments_null():
    configuration = HmacMaskingConfiguration(hmac_key="test_key")
    masker = HmacMaskingStrategy(configuration)
    expected = None

    masked = masker.mask(None)
    assert expected == masked
