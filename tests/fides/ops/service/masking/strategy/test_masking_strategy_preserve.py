from fides.api.schemas.masking.masking_configuration import PreserveMaskingConfiguration
from fides.api.service.masking.strategy.masking_strategy_preserve import (
    PreserveMaskingStrategy,
)


def test_mask_with_value():
    request_id = "123"
    config = PreserveMaskingConfiguration()
    masker = PreserveMaskingStrategy(configuration=config)
    original_value = "something else"
    result = masker.mask([original_value], request_id)
    assert result[0] == original_value


def test_mask_with_multi_value():
    request_id = "123"
    config = PreserveMaskingConfiguration()
    masker = PreserveMaskingStrategy(configuration=config)
    original_values = ["something else", "some more"]
    result = masker.mask(original_values, request_id)
    assert result[0] == original_values[0]
    assert result[1] == original_values[1]


def test_mask_no_value():
    request_id = "123"
    config = PreserveMaskingConfiguration()
    masker = PreserveMaskingStrategy(configuration=config)
    assert masker.mask(None, request_id) is None


def test_mask_empty_list():
    request_id = "123"
    config = PreserveMaskingConfiguration()
    masker = PreserveMaskingStrategy(configuration=config)
    result = masker.mask([], request_id)
    assert result == []


def test_mask_with_none_in_list():
    request_id = "123"
    config = PreserveMaskingConfiguration()
    masker = PreserveMaskingStrategy(configuration=config)
    original_values = ["value1", None, "value3"]
    result = masker.mask(original_values, request_id)
    assert result == original_values


def test_secrets_required():
    config = PreserveMaskingConfiguration()
    masker = PreserveMaskingStrategy(configuration=config)
    assert masker.secrets_required() is False


def test_data_type_supported():
    assert PreserveMaskingStrategy.data_type_supported("string") is True
    assert PreserveMaskingStrategy.data_type_supported("integer") is True
    assert PreserveMaskingStrategy.data_type_supported(None) is True


def test_get_description():
    description = PreserveMaskingStrategy.get_description()
    assert description.name == "preserve"
    assert "preserves" in description.description.lower()
    assert description.configurations == []
