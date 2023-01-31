from datetime import datetime
from unittest import mock
from unittest.mock import Mock

from fides.api.ops.schemas.masking.masking_configuration import (
    AesEncryptionMaskingConfiguration,
)
from fides.api.ops.schemas.masking.masking_secrets import MaskingSecretCache, SecretType
from fides.api.ops.service.masking.strategy.masking_strategy_aes_encrypt import (
    AesEncryptionMaskingStrategy,
)

from ....test_helpers.cache_secrets_helper import cache_secret, clear_cache_secrets

request_id = "1345134"
GCM_CONFIGURATION = AesEncryptionMaskingConfiguration(
    mode=AesEncryptionMaskingConfiguration.Mode.GCM
)
AES_STRATEGY = AesEncryptionMaskingStrategy(configuration=GCM_CONFIGURATION)


@mock.patch(
    "fides.api.ops.service.masking.strategy.masking_strategy_aes_encrypt.encrypt"
)
def test_mask_gcm_happypath(mock_encrypt: Mock):
    mock_encrypt.return_value = "encrypted"

    cache_secrets()

    masked_value = AES_STRATEGY.mask(["value"], request_id)[0]
    mock_encrypt.assert_called_with(
        "value",
        b"y\xc5I\xd4\x92\xf6G\t\x80\xb1$\x06\x19t/\xc4",
        b"\x94Y\xa8Z\xd9\x12\x83\x00\xa4~\ny",
    )
    assert masked_value == mock_encrypt.return_value
    clear_cache_secrets(request_id)


@mock.patch(
    "fides.api.ops.service.masking.strategy.masking_strategy_aes_encrypt.encrypt"
)
def test_mask_all_aes_modes(mock_encrypt: Mock):
    cache_secrets()
    for mode in AesEncryptionMaskingConfiguration.Mode:
        config = AesEncryptionMaskingConfiguration(mode=mode)
        strategy = AesEncryptionMaskingStrategy(configuration=config)
        strategy.mask(["arbitrary"], request_id)
    clear_cache_secrets(request_id)


def cache_secrets() -> None:
    secret_key = MaskingSecretCache[bytes](
        secret=b"y\xc5I\xd4\x92\xf6G\t\x80\xb1$\x06\x19t/\xc4",
        masking_strategy=AesEncryptionMaskingStrategy.name,
        secret_type=SecretType.key,
    )
    cache_secret(secret_key, request_id)
    secret_hmac_key = MaskingSecretCache[str](
        secret="other_key",
        masking_strategy=AesEncryptionMaskingStrategy.name,
        secret_type=SecretType.key_hmac,
    )
    cache_secret(secret_hmac_key, request_id)
    secret_hmac_salt = MaskingSecretCache[str](
        secret="some_salt",
        masking_strategy=AesEncryptionMaskingStrategy.name,
        secret_type=SecretType.salt_hmac,
    )
    cache_secret(secret_hmac_salt, request_id)


def test_mask_arguments_null_list():
    configuration = AesEncryptionMaskingConfiguration()
    masker = AesEncryptionMaskingStrategy(configuration)
    expected = [None]

    cache_secrets()

    masked = masker.mask([None], request_id)
    assert expected == masked
    clear_cache_secrets(request_id)


def test_mask_arguments_date():
    configuration = AesEncryptionMaskingConfiguration()
    masker = AesEncryptionMaskingStrategy(configuration)
    expected = ["Sb9RzoQls/Nymd23qY4ZXoy/HBDrZAxeRgKNYv5LwwxlsPE="]

    cache_secrets()

    masked = masker.mask([datetime(2000, 1, 1)], request_id)
    assert expected == masked
    clear_cache_secrets(request_id)
