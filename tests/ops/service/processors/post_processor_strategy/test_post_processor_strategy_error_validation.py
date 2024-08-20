from typing import Any, Dict

import pytest

from fides.api.common_exceptions import ValidationError
from fides.api.schemas.saas.strategy_configuration import (
    ErrorValidationPostProcessorConfiguration,
)
from fides.api.service.processors.post_processor_strategy.post_processor_strategy_error_validation import (
    ErrorValidationPostProcessorStrategy,
)


def test_http_code_must_be_recognized():
    config = ErrorValidationPostProcessorConfiguration(
        http_code=497,
        error_message_field="error_msg",
        expected_message="Some Error Msg",
    )
    ## What validation error do we have here?
    with pytest.raises(ValidationError):
        processor = ErrorValidationPostProcessorStrategy(configuration=config)


def test_error_message_is_removed_when_expected():
    print("To Be Done")


def test_error_message_is_kept_when_not_expected():
    print("To Be Done")


def test_data_is_undisturbed_when_no_error_message():
    print("To be Done")


def test_list_of_error_messages_is_checked_properly():
    print("To Be Implemented")
    ##TODO: What do we use when we want a Data provider on pytest?
    ##The idea would be to have a list of 3 expected error messages
    ## And set the error message one by one
