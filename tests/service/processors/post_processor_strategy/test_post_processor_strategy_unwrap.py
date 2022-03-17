from fidesops.schemas.saas.strategy_configuration import (
    UnwrapPostProcessorConfiguration,
)
from fidesops.service.processors.post_processor_strategy.post_processor_strategy_unwrap import (
    UnwrapPostProcessorStrategy,
)


def test_unwrap_to_list():
    config = UnwrapPostProcessorConfiguration(data_path="exact_matches.members")
    data = {
        "exact_matches": {
            "contacts": {"slenderman": 321},
            "members": [{"howdy": 123}, {"meow": 841}],
        }
    }
    processor = UnwrapPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == [{"howdy": 123}, {"meow": 841}]


def test_unwrap_to_object():
    config = UnwrapPostProcessorConfiguration(data_path="exact_matches.contacts")
    data = {
        "exact_matches": {
            "contacts": {"slenderman": 321},
            "members": [{"howdy": 123}, {"meow": 841}],
        }
    }
    processor = UnwrapPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == {"slenderman": 321}


def test_unwrap_path_not_found():
    config = UnwrapPostProcessorConfiguration(data_path="exact_matches.not_found")
    data = {
        "exact_matches": {
            "contacts": {"slenderman": 321},
            "members": [{"howdy": 123}, {"meow": 841}],
        }
    }
    processor = UnwrapPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result is None


def test_unwrap_unexpected_format():
    config = UnwrapPostProcessorConfiguration(data_path="exact_matches.members")
    data = "not-a-list-or-dict"
    processor = UnwrapPostProcessorStrategy(configuration=config)
    assert processor.process(data) == None


def test_unwrap_no_value():
    config = UnwrapPostProcessorConfiguration(data_path="exact_matches.members")
    processor = UnwrapPostProcessorStrategy(configuration=config)
    assert None is processor.process(None)


def test_unwrap_list():
    config = UnwrapPostProcessorConfiguration(data_path="email")
    data = [
        {"email": {"personal": "me@email.com"}},
        {"email": {"personal": "someone@email.com"}},
    ]
    processor = UnwrapPostProcessorStrategy(configuration=config)
    assert processor.process(data) == [
        {"personal": "me@email.com"},
        {"personal": "someone@email.com"},
    ]


def test_two_step_unwrap():
    first_config = UnwrapPostProcessorConfiguration(data_path="results")
    second_config = UnwrapPostProcessorConfiguration(data_path="info")
    data = {
        "results": [
            {"info": {"email": "who@email.com", "preferences": {}}},
            {"info": {"email": "other@email.com", "preferences": {}}},
        ]
    }
    first_processor = UnwrapPostProcessorStrategy(configuration=first_config)
    second_processor = UnwrapPostProcessorStrategy(configuration=second_config)

    first_result = first_processor.process(data)
    assert second_processor.process(first_result) == [
        {"email": "who@email.com", "preferences": {}},
        {"email": "other@email.com", "preferences": {}},
    ]


def test_unwrap_to_nested_lists():
    config = UnwrapPostProcessorConfiguration(data_path="emails")
    data = [
        {"emails": [{"personal": "me@email.com"}, {"personal": "someone@email.com"}]}
    ]
    processor = UnwrapPostProcessorStrategy(configuration=config)
    assert processor.process(data) == [
        {"personal": "me@email.com"},
        {"personal": "someone@email.com"},
    ]
