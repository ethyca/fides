from abc import abstractmethod
from typing import Any, Dict, List, Union

import pytest

from fides.api.common_exceptions import NoSuchStrategyException
from fides.api.schemas.saas.strategy_configuration import StrategyConfiguration
from fides.api.service.processors.post_processor_strategy.post_processor_strategy import (
    PostProcessorStrategy,
)


class SomeStrategyConfiguration(StrategyConfiguration):
    some_key: str = "default value"


class SomeStrategy(PostProcessorStrategy):
    name = "some postprocessor strategy"
    configuration_model = SomeStrategyConfiguration

    def __init__(self, configuration: SomeStrategyConfiguration):
        self.some_config = configuration.some_key

    def process(
        self, data: Any, identity_data: Dict[str, Any] = None
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        pass


class SomeSubStrategy(SomeStrategy):
    """
    A strategy class that subclasses another strategy class
    Its parent class is also a valid strategy, i.e. it has a name
    """

    name = "some subclassed strategy"


class AnotherSubStrategy(SomeStrategy):
    """
    A strategy class that subclasses another strategy class
    This is to test two subclasses at the same level
    in the strategy class hierarchy
    """

    name = "another subclassed strategy"


class SomeSubSubStrategy(SomeSubStrategy):
    """
    A strategy class that subclasses another strategy subclass
    This is to test a 3-level strategy hierarchy
    """

    name = "some sub-subclassed strategy"


class SomeAbstractStrategyClass(PostProcessorStrategy):
    """
    This class does not provide a name, which indicates
    that it's "abstract", i.e. it should not be retrievable
    """

    @abstractmethod
    def some_abstract_method(self):
        """Placeholder for an abstract method"""


class DifferentStrategySubClass(SomeAbstractStrategyClass):
    """
    This strategy class subclasses an abstract strategy class
    that does not provide a name and is not a strategy
    """

    name = "different subclassed strategy"
    configuration_model = SomeStrategyConfiguration

    def some_abstract_method(self):
        pass

    def __init__(self, configuration: SomeStrategyConfiguration):
        self.some_config = configuration.some_key

    def process(
        self, data: Any, identity_data: Dict[str, Any] = None
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        pass


class TestStrategyRetrieval:
    """
    Unit tests for abstract strategy retrieval functionality.
    Uses PostProcessorStrategy as an example
    """

    def test_valid_strategy(self):
        """
        Test registering a valid Strategy
        """

        config = SomeStrategyConfiguration(some_key="non default value")
        retrieved_strategy = PostProcessorStrategy.get_strategy(
            SomeStrategy.name, config.model_dump(mode="json")
        )
        assert isinstance(retrieved_strategy, SomeStrategy)
        assert retrieved_strategy.some_config == "non default value"

    def test_multi_level_inheritance_strategy(self):
        """
        Test that strategy classes with multiple levels
        of inheritance can be properly retrieved
        """

        config = SomeStrategyConfiguration(some_key="non default value")
        retrieved_strategy = PostProcessorStrategy.get_strategy(
            SomeStrategy.name, config.model_dump(mode="json")
        )
        assert isinstance(retrieved_strategy, SomeStrategy)

        retrieved_strategy = PostProcessorStrategy.get_strategy(
            SomeSubStrategy.name, config.model_dump(mode="json")
        )
        assert isinstance(retrieved_strategy, SomeSubStrategy)
        assert issubclass(type(retrieved_strategy), SomeStrategy)

        retrieved_strategy = PostProcessorStrategy.get_strategy(
            AnotherSubStrategy.name, config.model_dump(mode="json")
        )
        assert isinstance(retrieved_strategy, AnotherSubStrategy)
        assert issubclass(type(retrieved_strategy), SomeStrategy)

        retrieved_strategy = PostProcessorStrategy.get_strategy(
            SomeSubSubStrategy.name, config.model_dump(mode="json")
        )
        assert isinstance(retrieved_strategy, SomeSubSubStrategy)
        assert issubclass(type(retrieved_strategy), SomeStrategy)
        assert issubclass(type(retrieved_strategy), SomeSubStrategy)

        retrieved_strategy = PostProcessorStrategy.get_strategy(
            DifferentStrategySubClass.name, config.model_dump(mode="json")
        )
        assert isinstance(retrieved_strategy, DifferentStrategySubClass)
        assert issubclass(type(retrieved_strategy), SomeAbstractStrategyClass)

    def test_retrieve_nonexistent_strategy(self):
        """
        Test attempt to retrieve a nonexistent strategy
        """

        with pytest.raises(NoSuchStrategyException) as exc:
            PostProcessorStrategy.get_strategy("a nonexistent strategy", {})
        assert "'a nonexistent strategy'" in str(exc.value)
        assert "some postprocessor strategy" in str(exc.value)

    def test_get_strategies(self):
        """
        Test `get_strategies` method returns expected list of strategies
        """
        strats = PostProcessorStrategy.get_strategies()
        expected_strats = [
            SomeStrategy,
            SomeSubStrategy,
            SomeSubSubStrategy,
            DifferentStrategySubClass,
        ]
        for expected_strat in expected_strats:
            assert expected_strat in strats

        assert SomeAbstractStrategyClass not in strats
