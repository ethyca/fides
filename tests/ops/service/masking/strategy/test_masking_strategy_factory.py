import pytest

from fides.api.ops.common_exceptions import NoSuchStrategyException
from fides.api.ops.service.masking.strategy.masking_strategy import MaskingStrategy
from fides.api.ops.service.masking.strategy.masking_strategy_aes_encrypt import (
    AesEncryptionMaskingStrategy,
)
from fides.api.ops.service.masking.strategy.masking_strategy_hash import (
    HashMaskingStrategy,
)
from fides.api.ops.service.masking.strategy.masking_strategy_string_rewrite import (
    StringRewriteMaskingStrategy,
)


def test_get_strategy_hash():
    strategy = MaskingStrategy.get_strategy("hash", {})
    assert isinstance(strategy, HashMaskingStrategy)


def test_get_strategy_rewrite():
    config = {"rewrite_value": "val"}
    strategy = MaskingStrategy.get_strategy("string_rewrite", config)
    assert isinstance(strategy, StringRewriteMaskingStrategy)


def test_get_strategy_aes_encrypt():
    config = {"mode": "GCM", "key": "keycard", "nonce": "none"}
    strategy = MaskingStrategy.get_strategy("aes_encrypt", config)
    assert isinstance(strategy, AesEncryptionMaskingStrategy)


def test_get_strategy_invalid():
    with pytest.raises(NoSuchStrategyException):
        MaskingStrategy.get_strategy("invalid", {})
