from typing import Any, Dict

import pytest

from fides.api.common_exceptions import FidesopsException
from fides.api.schemas.saas.strategy_configuration import (
    FilterPostProcessorConfiguration,
)
from fides.api.service.processors.post_processor_strategy.post_processor_strategy_filter import (
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
    identity_data: Dict[str, Any] = {"phone_number": "123-1234-1235"}
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


def test_filter_non_exact_match():
    config = FilterPostProcessorConfiguration(
        field="email_contact", value="somebody@email.com", exact=False
    )
    data = {
        "id": 238475234,
        "email_contact": "[Somebody] somebody@email.com",
        "name": "Somebody Cool",
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == data


def test_filter_case_insensitive_match():
    config = FilterPostProcessorConfiguration(
        field="email_contact", value="SOMEBODY@email.com", case_sensitive=False
    )
    data = {
        "id": 238475234,
        "email_contact": "somebody@email.com",
        "name": "Somebody Cool",
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == data


def test_filter_nested_field():
    config = FilterPostProcessorConfiguration(
        field="attribute.email_contact", value="somebody@email.com"
    )
    data = {
        "id": 238475234,
        "attribute": {"email_contact": "somebody@email.com"},
        "name": "Somebody Cool",
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == data


def test_filter_nested_array_field():
    config = FilterPostProcessorConfiguration(
        field="attribute.email_contacts", value="somebody@email.com"
    )
    data = {
        "id": 238475234,
        "attribute": {"email_contacts": ["somebody@email.com"]},
        "name": "Somebody Cool",
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == data


def test_filter_nested_array_field_non_exact_match():
    config = FilterPostProcessorConfiguration(
        field="attribute.email_contacts", value="somebody@email.com", exact=False
    )
    data = {
        "id": 238475234,
        "attribute": {"email_contacts": ["[Somebody] somebody@email.com"]},
        "name": "Somebody Cool",
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == data


def test_filter_nested_array_field_case_insensitive_match():
    config = FilterPostProcessorConfiguration(
        field="attribute.email_contacts",
        value="somebody@email.com",
        case_sensitive=False,
    )
    data = {
        "id": 238475234,
        "attribute": {"email_contacts": ["SOMEBODY@email.com"]},
        "name": "Somebody Cool",
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == data


def test_filter_nested_array_field_non_exact_case_insensitive_match():
    config = FilterPostProcessorConfiguration(
        field="attribute.email_contacts",
        value="somebody@email.com",
        exact=False,
        case_sensitive=False,
    )
    data = {
        "id": 238475234,
        "attribute": {"email_contacts": ["[Somebody] SOMEBODY@email.com"]},
        "name": "Somebody Cool",
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == data


def test_filter_nested_array_field_exact_case_sensitive_match():
    config = FilterPostProcessorConfiguration(
        field="attribute.email_contacts", value="somebody@email.com"
    )
    data = {
        "id": 238475234,
        "attribute": {"email_contacts": ["[Somebody] SOMEBODY@email.com"]},
        "name": "Somebody Cool",
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == []


def test_filter_invalid_field_value():
    config = FilterPostProcessorConfiguration(
        field="attribute", value="somebody@email.com"
    )
    data = {
        "id": 238475234,
        "attribute": {"email_contacts": ["somebody@email.com"]},
        "name": "Somebody Cool",
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    with pytest.raises(FidesopsException) as exc:
        processor.process(data)
    assert str(exc.value) == (
        "Field value 'attribute' for filter postprocessor "
        "must be a string, integer or list of strings, found 'dict'"
    )


def test_filter_invalid_field_value_array():
    config = FilterPostProcessorConfiguration(
        field="attribute.email_contacts", value="somebody@email.com"
    )
    data = {
        "id": 238475234,
        "attribute": {"email_contacts": ["somebody@email.com", {"phone": 123}]},
        "name": "Somebody Cool",
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    with pytest.raises(FidesopsException) as exc:
        processor.process(data)
    assert str(exc.value) == (
        "Every value in the 'attribute.email_contacts' list must be a string"
    )


def test_nested_array_path():
    config = FilterPostProcessorConfiguration(
        field="agreement.orgs.members.email", value="somebody@email.com"
    )
    data = [
        {
            "agreement": {
                "id": 1,
                "orgs": [{"members": [{"email": "somebody@email.com"}]}],
            }
        },
        {
            "agreement": {
                "id": 2,
                "orgs": [{"members": [{"email": "somebody_else@email.com"}]}],
            }
        },
    ]
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == [
        {
            "agreement": {
                "id": 1,
                "orgs": [{"members": [{"email": "somebody@email.com"}]}],
            }
        }
    ]


def test_filter_by_dataset_reference():
    identity_data: Dict[str, Any] = {"email": "somebody@email.com"}
    config = FilterPostProcessorConfiguration(
        field="id",
        value={"dataset_reference": "<instance_fides_key>.customer.id"},
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
    access_data = {
        "<instance_fides_key>:customer": [
            {
                "id": 238475234,
                "email_contact": "somebody-else@email.com",
                "name": "Somebody Cool",
            }
        ]
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data, identity_data, access_data)
    assert result == [
        {
            "id": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
        }
    ]
