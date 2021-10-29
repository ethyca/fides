from fidesops.schemas.masking.masking_configuration import (
    StringRewriteMaskingConfiguration,
)
from fidesops.service.masking.strategy.masking_strategy_string_rewrite import (
    StringRewriteMaskingStrategy,
)


def test_mask_with_value():
    config = StringRewriteMaskingConfiguration(rewrite_value="cool")
    masker = StringRewriteMaskingStrategy(configuration=config)
    assert "cool" == masker.mask("something else")


def test_mask_no_value():
    config = StringRewriteMaskingConfiguration(rewrite_value="cool")
    masker = StringRewriteMaskingStrategy(configuration=config)
    assert None is masker.mask(None)
