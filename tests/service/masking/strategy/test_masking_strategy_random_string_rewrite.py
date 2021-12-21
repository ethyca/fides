from fidesops.schemas.masking.masking_configuration import (
    RandomStringMaskingConfiguration,
)
from fidesops.service.masking.strategy.masking_strategy_random_string_rewrite import (
    RandomStringRewriteMaskingStrategy,
)


def test_mask_with_value():
    request_id = "123432"
    config = RandomStringMaskingConfiguration(length=6)
    masker = RandomStringRewriteMaskingStrategy(configuration=config)
    assert 6 == len(masker.mask("string to mask", request_id))

    config = RandomStringMaskingConfiguration(length=25)
    masker = RandomStringRewriteMaskingStrategy(configuration=config)
    assert 25 == len(masker.mask("string to mask", request_id))


def test_mask_no_value():
    request_id = "123432"
    config = RandomStringMaskingConfiguration(length=6)
    masker = RandomStringRewriteMaskingStrategy(configuration=config)
    assert None is masker.mask(None, request_id)
