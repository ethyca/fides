from fidesops.schemas.masking.masking_configuration import (
    StringRewriteMaskingConfiguration,
)
from fidesops.service.masking.strategy.masking_strategy_string_rewrite import (
    StringRewriteMaskingStrategy,
)


def test_mask_with_value():
    request_id = "1234"
    config = StringRewriteMaskingConfiguration(rewrite_value="cool")
    masker = StringRewriteMaskingStrategy(configuration=config)
    assert "cool" == masker.mask(["something else"], request_id)[0]


def test_mask_with_multi_value():
    request_id = "1234"
    config = StringRewriteMaskingConfiguration(rewrite_value="cool")
    masker = StringRewriteMaskingStrategy(configuration=config)
    masked = masker.mask(["something else", "some more"], request_id)
    assert "cool" == masked[0]
    assert "cool" == masked[1]


def test_mask_no_value():
    request_id = "1234"
    config = StringRewriteMaskingConfiguration(rewrite_value="cool")
    masker = StringRewriteMaskingStrategy(configuration=config)
    assert None is masker.mask(None, request_id)
