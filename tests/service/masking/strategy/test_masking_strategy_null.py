from fidesops.schemas.masking.masking_configuration import NullMaskingConfiguration
from fidesops.service.masking.strategy.masking_strategy_nullify import NullMaskingStrategy



def test_mask_with_value():
    config = NullMaskingConfiguration()
    masker = NullMaskingStrategy(configuration=config)
    assert masker.mask("something else") is None


def test_mask_no_value():
    config = NullMaskingConfiguration()
    masker = NullMaskingStrategy(configuration=config)
    assert masker.mask(None) is None
