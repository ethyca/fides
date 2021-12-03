import pytest

from fidesops.service.masking.strategy.masking_strategy_hash import HASH
from fidesops.service.masking.strategy.masking_strategy_string_rewrite import (
    STRING_REWRITE,
)
from fidesops.schemas.policy import PolicyMaskingSpec
from fidesops.service.masking.masking_processor import mask
from fidesops.service.masking.strategy.masking_strategy_factory import (
    NoSuchStrategyException,
)


@pytest.fixture
def hash_strategy() -> PolicyMaskingSpec:
    return PolicyMaskingSpec(strategy=HASH, configuration={"algorithm": "SHA-512"})


@pytest.fixture
def hash_strategy_format_preservation() -> PolicyMaskingSpec:
    return PolicyMaskingSpec(
        strategy=HASH,
        configuration={
            "algorithm": "SHA-512",
            "format_preservation": {"suffix": "@masked.com"},
        },
    )


@pytest.fixture
def string_rewrite_strategy() -> PolicyMaskingSpec:
    return PolicyMaskingSpec(
        strategy=STRING_REWRITE, configuration={"rewrite_value": "File"}
    )


def test_mask_hash_strategy(hash_strategy: PolicyMaskingSpec):
    policy_masking_spec = [hash_strategy]
    value = "22475"
    with pytest.raises(NoSuchStrategyException):
        mask(value, policy_masking_spec)


def test_mask_hash_strategy_format_preservation(
    hash_strategy_format_preservation: PolicyMaskingSpec,
):
    policy_masking_spec = [hash_strategy_format_preservation]
    value = "meow@meow.com"
    with pytest.raises(NoSuchStrategyException):
        mask(value, policy_masking_spec)


def test_mask_multi_strategies(
    string_rewrite_strategy: PolicyMaskingSpec, hash_strategy: PolicyMaskingSpec
):
    policy_masking_spec = [string_rewrite_strategy, hash_strategy]
    value = "22475"

    with pytest.raises(NoSuchStrategyException):
        mask(value, policy_masking_spec)


def test_mask_no_strategies():
    value = "22475"

    masked_value = mask(value, [])

    assert masked_value == value


def test_mask_invalid_strategy():
    policy_masking_spec = [PolicyMaskingSpec(strategy="fake", configuration={})]
    value = "22475"

    with pytest.raises(NoSuchStrategyException):
        mask(value, policy_masking_spec)


def test_mask_no_input(hash_strategy: PolicyMaskingSpec):
    policy_masking_spec = [hash_strategy]
    value = None

    with pytest.raises(NoSuchStrategyException):
        mask(value, policy_masking_spec)
