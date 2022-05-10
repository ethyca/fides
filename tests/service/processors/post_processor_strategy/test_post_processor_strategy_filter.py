import pytest
from typing import Dict, Any
from fidesops.common_exceptions import FidesopsException
from fidesops.schemas.saas.strategy_configuration import (
    FilterPostProcessorConfiguration,
)
from fidesops.service.processors.post_processor_strategy.post_processor_strategy_filter import (
    FilterPostProcessorStrategy,
)


def test_filter_array_by_identity_reference():
    identity_data: Dict[str, Any] = {"email": "somebody@email.com"}
    config = FilterPostProcessorConfiguration(
        field="email_contact", value={"identity": "email"}
    )
    data = [
        {
            "id": 1397429347,
            "email_contact": "somebody@email.com",
            "name": "Somebody Awesome",
        },
        {
            "id": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
        },
    ]
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data, identity_data)
    assert result == [
        {
            "id": 1397429347,
            "email_contact": "somebody@email.com",
            "name": "Somebody Awesome",
        }
    ]


def test_filter_array_by_identity_reference_no_results():
    identity_data: Dict[str, Any] = {"email": "someone-nice@email.com"}
    config = FilterPostProcessorConfiguration(
        field="email_contact", value={"identity": "email"}
    )
    data = [
        {
            "id": 1397429347,
            "email_contact": "somebody@email.com",
            "name": "Somebody Awesome",
        },
        {
            "id": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
        },
    ]
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data, identity_data)
    assert result == []


def test_filter_array_with_static_val():
    config = FilterPostProcessorConfiguration(
        field="email_contact", value="somebody@email.com"
    )
    data = [
        {
            "id": 1397429347,
            "email_contact": "somebody@email.com",
            "name": "Somebody Awesome",
        },
        {
            "id": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
        },
    ]
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == [
        {
            "id": 1397429347,
            "email_contact": "somebody@email.com",
            "name": "Somebody Awesome",
        }
    ]


def test_filter_object():
    config = FilterPostProcessorConfiguration(
        field="email_contact", value="somebody-else@email.com"
    )
    data = {
        "id": 238475234,
        "email_contact": "somebody-else@email.com",
        "name": "Somebody Cool",
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == {
        "id": 238475234,
        "email_contact": "somebody-else@email.com",
        "name": "Somebody Cool",
    }


def test_filter_object_no_results():
    config = FilterPostProcessorConfiguration(
        field="email_contact", value="somebody@email.com"
    )
    data = {
        "id": 238475234,
        "email_contact": "somebody-else@email.com",
        "name": "Somebody Cool",
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == []


def test_filter_nonexistent_field():
    config = FilterPostProcessorConfiguration(
        field="nonexistent_field", value="somebody@email.com"
    )
    data = {
        "id": 238475234,
        "email_contact": "somebody@email.com",
        "name": "Somebody Cool",
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == []


def test_filter_by_nonexistent_identity_reference():
    identity_data: Dict[str, Any] = {"phone": "123-1234-1235"}
    config = FilterPostProcessorConfiguration(
        field="email_contact", value={"identity": "email"}
    )
    data = [
        {
            "id": 1397429347,
            "email_contact": "somebody@email.com",
            "name": "Somebody Awesome",
        },
        {
            "id": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
        },
    ]
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == []


def test_filter_by_identity_reference_with_no_identity_data():
    identity_data = None
    config = FilterPostProcessorConfiguration(
        field="email_contact", value={"identity": "email"}
    )
    data = [
        {
            "id": 1397429347,
            "email_contact": "somebody@email.com",
            "name": "Somebody Awesome",
        },
        {
            "id": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
        },
    ]
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == []


def test_filter_no_value():
    config = FilterPostProcessorConfiguration(
        field="email_contact", value="somebody@email.com"
    )
    processor = FilterPostProcessorStrategy(configuration=config)
    assert processor.process(None) == []
