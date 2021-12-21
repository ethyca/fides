from fidesops.schemas.masking.masking_configuration import NullMaskingConfiguration
from fidesops.service.masking.strategy.masking_strategy_nullify import (
    NullMaskingStrategy,
)


def test_mask_with_value():
    request_id = "123"
    config = NullMaskingConfiguration()
    masker = NullMaskingStrategy(configuration=config)
    assert masker.mask("something else", request_id) is None


def test_mask_no_value():
    request_id = "123"
    config = NullMaskingConfiguration()
    masker = NullMaskingStrategy(configuration=config)
    assert masker.mask(None, request_id) is None
