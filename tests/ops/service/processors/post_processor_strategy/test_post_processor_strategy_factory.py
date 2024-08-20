import pytest

from fides.api.common_exceptions import NoSuchStrategyException, ValidationError
from fides.api.service.processors.post_processor_strategy.post_processor_strategy import (
    PostProcessorStrategy,
)
from fides.api.service.processors.post_processor_strategy.post_processor_strategy_filter import (
    FilterPostProcessorStrategy,
)
from fides.api.service.processors.post_processor_strategy.post_processor_strategy_unwrap import (
    UnwrapPostProcessorStrategy,
)

from fides.api.service.processors.post_processor_strategy.post_processor_strategy_error_validation import (
    ErrorValidationPostProcessorStrategy,
)


def test_get_strategy_filter():
    config = {"field": "email_contact", "value": "somebody@email.com"}
    strategy = PostProcessorStrategy.get_strategy(
        strategy_name="filter", configuration=config
    )
    assert isinstance(strategy, FilterPostProcessorStrategy)


def test_get_strategy_unwrap():
    config = {"data_path": "exact_matches.members"}
    strategy = PostProcessorStrategy.get_strategy(
        strategy_name="unwrap", configuration=config
    )
    assert isinstance(strategy, UnwrapPostProcessorStrategy)


def test_strategy_error_validation():
    config = {
        "http_code": 400,
        "error_message_field": "error_msg",
        "expected_message": "This is an Example",
    }
    strategy = PostProcessorStrategy.get_strategy(
        strategy_name="error_validation", configuration=config
    )
    assert isinstance(strategy, ErrorValidationPostProcessorStrategy)


def test_get_strategy_invalid_config():
    with pytest.raises(ValidationError):
        PostProcessorStrategy.get_strategy(
            strategy_name="unwrap", configuration={"invalid": "thing"}
        )


def test_get_strategy_invalid_strategy():
    with pytest.raises(NoSuchStrategyException):
        PostProcessorStrategy.get_strategy("invalid", {})
