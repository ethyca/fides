import pytest

from fidesops.service.masking.strategy.masking_strategy_aes_encrypt import (
    AesEncryptionMaskingStrategy,
)
from fidesops.service.masking.strategy.masking_strategy_factory import (
    NoSuchStrategyException,
    get_strategy,
)
from fidesops.service.masking.strategy.masking_strategy_hash import HashMaskingStrategy
from fidesops.service.masking.strategy.masking_strategy_string_rewrite import (
    StringRewriteMaskingStrategy,
)


def test_get_strategy_hash():
    strategy = get_strategy("hash", {})
    assert isinstance(strategy, HashMaskingStrategy)


def test_get_strategy_rewrite():
    config = {"rewrite_value": "val"}
    strategy = get_strategy("string_rewrite", config)
    assert isinstance(strategy, StringRewriteMaskingStrategy)


def test_get_strategy_aes_encrypt():
    config = {"mode": "GCM", "key": "keycard", "nonce": "none"}
    strategy = get_strategy("aes_encrypt", config)
    assert isinstance(strategy, AesEncryptionMaskingStrategy)


def test_get_strategy_invalid():
    with pytest.raises(NoSuchStrategyException):
        get_strategy("invalid", {})
