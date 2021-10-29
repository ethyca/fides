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


def test_mask_one_strategy(hash_strategy: PolicyMaskingSpec):
    policy_masking_spec = [hash_strategy]
    value = "22475"
    expected_masked_value = "7d6f1a312135fe11d1c47bc2a44413c4449b434ea0ce30ea3e438de557579a340548af12863c1e966547669e8b7cfc844e6c18aabae6c97c9eb1f0d388158bf5"

    masked_value = mask(value, policy_masking_spec)

    assert masked_value == expected_masked_value


def test_mask_one_strategy_format_preservation(
    hash_strategy_format_preservation: PolicyMaskingSpec,
):
    policy_masking_spec = [hash_strategy_format_preservation]
    value = "meow@meow.com"
    expected_masked_value = "774a23fae48c0c950258fe40e5e08cc867440dfa8086e93efe6414e3df9ec334af3cd34ba90df9e95b1d8e370c1677c071eb34dd1c90293b7aaae4c261e5bda9@masked.com"

    masked_value = mask(value, policy_masking_spec)

    assert masked_value == expected_masked_value


def test_mask_multi_strategies(
    string_rewrite_strategy: PolicyMaskingSpec, hash_strategy: PolicyMaskingSpec
):
    policy_masking_spec = [string_rewrite_strategy, hash_strategy]
    value = "22475"

    expected_masked_value = "832ac8125bbda9887b394fd8f23157804d45ee6c2b8dc7c51fe6d6eef0a93fe1b7c98e2b96ac453f432f2e3ac651fa914ff0bb52a75687f748e0c9b9209f4a64"

    masked_value = mask(value, policy_masking_spec)

    assert masked_value == expected_masked_value


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
    expected_masked_value = None

    masked_value = mask(value, policy_masking_spec)

    assert masked_value == expected_masked_value
