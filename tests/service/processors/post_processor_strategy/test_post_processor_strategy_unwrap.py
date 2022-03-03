from fidesops.schemas.saas.strategy_configuration import UnwrapPostProcessorConfiguration
from fidesops.service.processors.post_processor_strategy.post_processor_strategy_unwrap import \
    UnwrapPostProcessorStrategy


def test_unwrap_to_list():
    config = UnwrapPostProcessorConfiguration(
        data_path="exact_matches.members"
    )
    data = {
        "exact_matches": {
            "contacts": {"slenderman": 321},
            "members": [
                {"howdy": 123},
                {"meow": 841}
            ]
        }
    }
    processor = UnwrapPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == [
        {"howdy": 123},
        {"meow": 841}
    ]


def test_unwrap_to_object():
    config = UnwrapPostProcessorConfiguration(
        data_path="exact_matches.contacts"
    )
    data = {
        "exact_matches": {
            "contacts": {"slenderman": 321},
            "members": [
                {"howdy": 123},
                {"meow": 841}
            ]
        }
    }
    processor = UnwrapPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result == {"slenderman": 321}


def test_unwrap_path_not_found():
    config = UnwrapPostProcessorConfiguration(
        data_path="exact_matches.not_found"
    )
    data = {
        "exact_matches": {
            "contacts": {"slenderman": 321},
            "members": [
                {"howdy": 123},
                {"meow": 841}
            ]
        }
    }
    processor = UnwrapPostProcessorStrategy(configuration=config)
    result = processor.process(data)
    assert result is None


def test_unwrap_unexpected_format():
    config = UnwrapPostProcessorConfiguration(
        data_path="exact_matches.members"
    )
    data = "not-a-list-or-dict"
    processor = UnwrapPostProcessorStrategy(configuration=config)
    assert processor.process(data) == data


def test_unwrap_no_value():
    config = UnwrapPostProcessorConfiguration(
        data_path="exact_matches.members"
    )
    processor = UnwrapPostProcessorStrategy(configuration=config)
    assert None is processor.process(None)
