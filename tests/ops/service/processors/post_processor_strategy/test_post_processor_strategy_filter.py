from typing import Any, Dict
from unittest import mock

import pytest

from fides.api.common_exceptions import FidesopsException
from fides.api.models.privacy_request import PrivacyRequest
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
    result = processor.process(data, identity_data)
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
    result = processor.process(data, identity_data)
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
        "must be a string, list of strings, integer or list of integers, found 'dict'"
    )


def test_filter_invalid_field_value_string_array():
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
        "The field 'attribute.email_contacts' list must contain either all strings or all integers."
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


@mock.patch("fides.api.models.privacy_request.PrivacyRequest.get_raw_access_results")
def test_filter_by_invalid_dataset_reference(mock_method):

    config = FilterPostProcessorConfiguration(
        field="customerId",
        value={"dataset_reference": "<instance_fides_key>.customer"},
    )
    data = [
        {
            "order_id": 22340,
            "customerId": 1397429347,
            "email_contact": "somebody@email.com",
            "name": "Somebody Awesome",
        },
        {
            "order_id": 22355,
            "customerId": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
        },
    ]
    mock_method.return_value = {
        "<instance_fides_key>:customer": [
            {
                "id": 238475234,
                "name": "Somebody Cool",
            }
        ]
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data, privacy_request=PrivacyRequest())
    assert result == []


@mock.patch("fides.api.models.privacy_request.PrivacyRequest.get_raw_access_results")
def test_filter_by_dataset_reference_int_filter_value(mock_method):
    config = FilterPostProcessorConfiguration(
        field="customerId",
        value={"dataset_reference": "<instance_fides_key>.customer.id"},
    )
    data = [
        {
            "order_id": 22340,
            "customerId": 1397429347,
            "email_contact": "somebody@email.com",
            "name": "Somebody Awesome",
        },
        {
            "order_id": 22355,
            "customerId": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
        },
    ]
    mock_method.return_value = {
        "<instance_fides_key>:customer": [
            {
                "id": 238475234,
                "name": "Somebody Cool",
            }
        ]
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data, privacy_request=PrivacyRequest())
    assert result == [
        {
            "order_id": 22355,
            "customerId": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
        },
    ]


@mock.patch("fides.api.models.privacy_request.PrivacyRequest.get_raw_access_results")
def test_filter_by_dataset_reference_int_filter_value_with_exact_and_case_sensitive(
    mock_method,
):
    config = FilterPostProcessorConfiguration(
        field="customerId",
        value={"dataset_reference": "<instance_fides_key>.customer.id"},
        exact=False,
        case_sensitive=False,
    )
    data = [
        {
            "order_id": 22340,
            "customerId": 1397429347,
            "email_contact": "somebody@email.com",
            "name": "Somebody Awesome",
        },
        {
            "order_id": 22355,
            "customerId": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
        },
    ]
    mock_method.return_value = {
        "<instance_fides_key>:customer": [
            {
                "id": 238475234,
                "name": "Somebody Cool",
            }
        ]
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data, privacy_request=PrivacyRequest())
    assert result == [
        {
            "order_id": 22355,
            "customerId": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
        },
    ]


@mock.patch("fides.api.models.privacy_request.PrivacyRequest.get_raw_access_results")
def test_filter_by_dataset_reference_multiple_int_filter_values(mock_method):
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
        {
            "id": 6397439648,
            "email_contact": "another-somebody@email.com",
            "name": "Somebody Nice",
        },
        {
            "id": 839565221,
            "email_contact": "somebody-but-you@email.com",
            "name": "Somebody Sweet",
        },
    ]
    mock_method.return_value = {
        "<instance_fides_key>:customer": [
            {
                "id": 238475234,
                "email_contact": "somebody-else@email.com",
                "name": "Somebody Cool",
            },
            {
                "id": 839565221,
                "email_contact": "somebody-but-you@email.com",
                "name": "Somebody Sweet",
            },
        ]
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data, privacy_request=PrivacyRequest())
    assert result == [
        {
            "id": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
        },
        {
            "id": 839565221,
            "email_contact": "somebody-but-you@email.com",
            "name": "Somebody Sweet",
        },
    ]


@mock.patch("fides.api.models.privacy_request.PrivacyRequest.get_raw_access_results")
def test_filter_by_dataset_reference_int_filter_value_list_field(mock_method):
    config = FilterPostProcessorConfiguration(
        field="random_numbers",
        value={"dataset_reference": "<instance_fides_key>.customer.wanted_number"},
    )
    data = [
        {
            "id": 1397429347,
            "email_contact": "somebody@email.com",
            "name": "Somebody Awesome",
            "random_numbers": [1234, 6778, 2310],
        },
        {
            "id": 839565221,
            "email_contact": "somebody-but-you@email.com",
            "name": "Somebody Sweet",
            "random_numbers": [1234, 333, 8973],
        },
        {
            "id": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
            "random_numbers": [451, 2100, 6778],
        },
    ]
    mock_method.return_value = {
        "<instance_fides_key>:customer": [{"id": 238475234, "wanted_number": 6778}]
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data, privacy_request=PrivacyRequest())
    assert result == [
        {
            "id": 1397429347,
            "email_contact": "somebody@email.com",
            "name": "Somebody Awesome",
            "random_numbers": [1234, 6778, 2310],
        },
        {
            "id": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
            "random_numbers": [451, 2100, 6778],
        },
    ]


@mock.patch("fides.api.models.privacy_request.PrivacyRequest.get_raw_access_results")
def test_filter_by_dataset_reference_multiple_int_filter_values_and_list_field(
    mock_method,
):
    config = FilterPostProcessorConfiguration(
        field="random_numbers",
        value={"dataset_reference": "<instance_fides_key>.customer.wanted_number"},
    )
    data = [
        {
            "id": 1397429347,
            "email_contact": "somebody@email.com",
            "name": "Somebody Awesome",
            "random_numbers": [1234, 6778, 2310],
        },
        {
            "id": 6397439648,
            "email_contact": "another-somebody@email.com",
            "name": "Somebody Nice",
            "random_numbers": [6666, 278, 221, 9851],
        },
        {
            "id": 839565221,
            "email_contact": "somebody-but-you@email.com",
            "name": "Somebody Sweet",
            "random_numbers": [1234, 333, 8973],
        },
        {
            "id": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
            "random_numbers": [451, 2100, 6778],
        },
    ]
    mock_method.return_value = {
        "<instance_fides_key>:customer": [
            {"id": 238475234, "wanted_number": 6778},
            {"id": 1397429347, "wanted_number": 1234},
        ]
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data, privacy_request=PrivacyRequest())
    assert result == [
        {
            "id": 1397429347,
            "email_contact": "somebody@email.com",
            "name": "Somebody Awesome",
            "random_numbers": [1234, 6778, 2310],
        },
        {
            "id": 839565221,
            "email_contact": "somebody-but-you@email.com",
            "name": "Somebody Sweet",
            "random_numbers": [1234, 333, 8973],
        },
        {
            "id": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
            "random_numbers": [451, 2100, 6778],
        },
    ]


@mock.patch("fides.api.models.privacy_request.PrivacyRequest.get_raw_access_results")
def test_filter_by_dataset_reference_wrong_filter_value(mock_method):
    config = FilterPostProcessorConfiguration(
        field="customerId",
        value={"dataset_reference": "<instance_fides_key>.customer.id"},
    )
    data = [
        {
            "order_id": 22340,
            "customerId": 1397429347,
            "email_contact": "somebody@email.com",
            "name": "Somebody Awesome",
        },
        {
            "order_id": 22355,
            "customerId": 238475234,
            "email_contact": "somebody-else@email.com",
            "name": "Somebody Cool",
        },
    ]
    mock_method.return_value = {
        "<instance_fides_key>:customer": [
            {
                "id": "somebody-else@email.com",
                "name": "Somebody Cool",
            }
        ]
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data, privacy_request=PrivacyRequest())
    assert result == []


@mock.patch("fides.api.models.privacy_request.PrivacyRequest.get_raw_access_results")
def test_filter_by_dataset_reference_invalid_field_value_int_array(mock_method):
    config = FilterPostProcessorConfiguration(
        field="attribute.id",
        value={"dataset_reference": "<instance_fides_key>.customer.id"},
    )
    data = {
        "order_id": 238475234,
        "attribute": {"id": [1234, 2444, "hi"]},
        "name": "Somebody Cool",
    }
    mock_method.return_value = {
        "<instance_fides_key>:customer": [
            {
                "id": 1234,
                "name": "Somebody Cool",
            }
        ]
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    with pytest.raises(FidesopsException) as exc:
        processor.process(data, privacy_request=PrivacyRequest)
    assert str(exc.value) == (
        "The field 'attribute.id' list must contain either all strings or all integers."
    )


@mock.patch("fides.api.models.privacy_request.PrivacyRequest.get_raw_access_results")
def test_filter_by_dataset_reference_multiple_string_filter_values(mock_method):
    config = FilterPostProcessorConfiguration(
        field="user",
        value={"dataset_reference": "<instance_fides_key>.customer.userName"},
    )
    data = [
        {
            "recipient_id": 1397429347,
            "email_contact": "somebody@email.com",
            "user": "MabelEthy",
        },
        {
            "recipient_id": 6397439648,
            "email_contact": "another-somebody@email.com",
            "user": "isabelEthy",
        },
        {
            "recipient_id": 839565221,
            "email_contact": "somebody-but-you@email.com",
            "user": "Laurenethy",
        },
        {
            "recipient_id": 238475234,
            "email_contact": "somebody-else@email.com",
            "user": "rogerEthy",
        },
    ]
    mock_method.return_value = {
        "<instance_fides_key>:customer": [
            {"id": 238475234, "userName": "isabelEthy"},
            {"id": 1397429347, "userName": "rogerEthy"},
        ]
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data, privacy_request=PrivacyRequest())
    assert result == [
        {
            "recipient_id": 6397439648,
            "email_contact": "another-somebody@email.com",
            "user": "isabelEthy",
        },
        {
            "recipient_id": 238475234,
            "email_contact": "somebody-else@email.com",
            "user": "rogerEthy",
        },
    ]


@mock.patch("fides.api.models.privacy_request.PrivacyRequest.get_raw_access_results")
def test_filter_by_dataset_reference_string_filter_values_exact_false_case_sensitive_false(
    mock_method,
):
    config = FilterPostProcessorConfiguration(
        field="user",
        value={"dataset_reference": "<instance_fides_key>.customer.userName"},
        exact=False,
        case_sensitive=False,
    )
    data = [
        {
            "recipient_id": 1397429347,
            "email_contact": "somebody@email.com",
            "user": "MabelEthy",
        },
        {
            "recipient_id": 6397439648,
            "email_contact": "another-somebody@email.com",
            "user": "name_isabelEthy",
        },
        {
            "recipient_id": 839565221,
            "email_contact": "somebody-but-you@email.com",
            "user": "Laurenethy",
        },
        {
            "recipient_id": 238475234,
            "email_contact": "somebody-else@email.com",
            "user": "rogerEthy1",
        },
    ]
    mock_method.return_value = {
        "<instance_fides_key>:customer": [
            {"id": 238475234, "userName": "isabelethy"},
            {"id": 1397429347, "userName": "rogerethy"},
        ]
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data, privacy_request=PrivacyRequest())
    assert result == [
        {
            "recipient_id": 6397439648,
            "email_contact": "another-somebody@email.com",
            "user": "name_isabelEthy",
        },
        {
            "recipient_id": 238475234,
            "email_contact": "somebody-else@email.com",
            "user": "rogerEthy1",
        },
    ]


@mock.patch("fides.api.models.privacy_request.PrivacyRequest.get_raw_access_results")
def test_filter_by_dataset_reference_multiple_list_filter_values(mock_method):
    config = FilterPostProcessorConfiguration(
        field="user",
        value={"dataset_reference": "<instance_fides_key>.customer.userName"},
    )
    data = [
        {
            "recipient_id": 1397429347,
            "email_contact": "somebody@email.com",
            "user": "MabelEthy",
        },
        {
            "recipient_id": 6397439648,
            "email_contact": "another-somebody@email.com",
            "user": "isabelEthy",
        },
        {
            "recipient_id": 839565221,
            "email_contact": "somebody-but-you@email.com",
            "user": "LaurenEthy",
        },
        {
            "recipient_id": 238475234,
            "email_contact": "somebody-else@email.com",
            "user": "rogerEthy",
        },
    ]
    mock_method.return_value = {
        "<instance_fides_key>:customer": [
            {"id": 238475234, "userName": ["isabelEthy", "LaurenEthy"]},
            {"id": 1397429347, "userName": ["rogerEthy", "michaelEthy"]},
        ]
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    result = processor.process(data, privacy_request=PrivacyRequest())
    assert result == [
        {
            "recipient_id": 6397439648,
            "email_contact": "another-somebody@email.com",
            "user": "isabelEthy",
        },
        {
            "recipient_id": 839565221,
            "email_contact": "somebody-but-you@email.com",
            "user": "LaurenEthy",
        },
        {
            "recipient_id": 238475234,
            "email_contact": "somebody-else@email.com",
            "user": "rogerEthy",
        },
    ]


@mock.patch("fides.api.models.privacy_request.PrivacyRequest.get_raw_access_results")
def test_filter_by_dataset_reference_invalid_filter_value(mock_method):
    config = FilterPostProcessorConfiguration(
        field="user",
        value={"dataset_reference": "<instance_fides_key>.customer.userName"},
    )
    data = [
        {
            "recipient_id": 1397429347,
            "email_contact": "somebody@email.com",
            "user": "MabelEthy",
        },
        {
            "recipient_id": 6397439648,
            "email_contact": "another-somebody@email.com",
            "user": "isabelEthy",
        },
    ]
    mock_method.return_value = {
        "<instance_fides_key>:customer": [
            {"id": 238475234, "userName": {"test": "value"}},
            {"id": 1397429347, "userName": {"test": "value"}},
        ]
    }
    processor = FilterPostProcessorStrategy(configuration=config)
    with pytest.raises(FidesopsException) as exc:
        processor.process(data, privacy_request=PrivacyRequest())
    assert str(exc.value) == (
        "The filter_value '[{'test': 'value'}, {'test': 'value'}]' list must contain either all strings or all integers."
    )
