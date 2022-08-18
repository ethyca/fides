import pytest
from fidesops.ops.service.masking.strategy.masking_strategy_aes_encrypt import (
    AesEncryptionMaskingStrategy,
)
from fidesops.ops.service.masking.strategy.masking_strategy_factory import (
    MaskingStrategyFactory,
    NoSuchStrategyException,
)
from fidesops.ops.service.masking.strategy.masking_strategy_hash import (
    HashMaskingStrategy,
)
from fidesops.ops.service.masking.strategy.masking_strategy_string_rewrite import (
    StringRewriteMaskingStrategy,
)


def test_get_strategy_hash():
    strategy = MaskingStrategyFactory.get_strategy("hash", {})
    assert isinstance(strategy, HashMaskingStrategy)


def test_get_strategy_rewrite():
    config = {"rewrite_value": "val"}
    strategy = MaskingStrategyFactory.get_strategy("string_rewrite", config)
    assert isinstance(strategy, StringRewriteMaskingStrategy)


def test_get_strategy_aes_encrypt():
    config = {"mode": "GCM", "key": "keycard", "nonce": "none"}
    strategy = MaskingStrategyFactory.get_strategy("aes_encrypt", config)
    assert isinstance(strategy, AesEncryptionMaskingStrategy)


def test_get_strategy_invalid():
    with pytest.raises(NoSuchStrategyException):
        MaskingStrategyFactory.get_strategy("invalid", {})
