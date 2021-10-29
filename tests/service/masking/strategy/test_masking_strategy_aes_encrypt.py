from unittest import mock
from unittest.mock import Mock

from fidesops.schemas.masking.masking_configuration import (
    AesEncryptionMaskingConfiguration,
)
from fidesops.service.masking.strategy.masking_strategy_aes_encrypt import (
    AesEncryptionMaskingStrategy,
)

GCM_CONFIGURATION = AesEncryptionMaskingConfiguration(
    mode=AesEncryptionMaskingConfiguration.Mode.GCM, nonce="Nonce", key="Key"
)
AES_STRATEGY = AesEncryptionMaskingStrategy(configuration=GCM_CONFIGURATION)


@mock.patch("fidesops.service.masking.strategy.masking_strategy_aes_encrypt.encrypt")
def test_mask_gcm_happypath(mock_encrypt: Mock):
    mock_encrypt.return_value = "encrypted"

    masked_value = AES_STRATEGY.mask("value")

    assert masked_value == mock_encrypt.return_value


@mock.patch("fidesops.service.masking.strategy.masking_strategy_aes_encrypt.encrypt")
def test_mask_all_aes_modes(mock_encrypt: Mock):
    for mode in AesEncryptionMaskingConfiguration.Mode:
        config = AesEncryptionMaskingConfiguration(mode=mode, nonce="Nonce", key="Key")
        strategy = AesEncryptionMaskingStrategy(configuration=config)
        strategy.mask("arbitrary")
