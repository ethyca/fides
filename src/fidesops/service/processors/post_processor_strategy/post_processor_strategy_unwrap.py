import logging
from typing import Any, List, Optional, Dict, Union

import pydash as pydash

from fidesops.schemas.saas.strategy_configuration import (
    UnwrapPostProcessorConfiguration,
    StrategyConfiguration,
)
from fidesops.service.processors.post_processor_strategy.post_processor_strategy import (
    PostProcessorStrategy,
)


STRATEGY_NAME = "unwrap"

logger = logging.getLogger(__name__)


class UnwrapPostProcessorStrategy(PostProcessorStrategy):
    """
    Given a path to a dict/list, returns the dict/list
    E.g.
    data = {
        "exact_matches": {
            "members": [
                {"howdy": 123},
                {"meow": 841}
            ]
        }
    }
    data_path = exact_matches.members
    result = [
                {"howdy": 123},
                {"meow": 841}
            ]

    If given a list, the unwrap will apply to the dicts inside the list.
    """

    def __init__(self, configuration: UnwrapPostProcessorConfiguration):
        self.data_path = configuration.data_path

    def get_strategy_name(self) -> str:
        return STRATEGY_NAME

    def process(
        self,
        data: Union[List[Dict[str, Any]], Dict[str, Any]],
        identity_data: Dict[str, Any] = None,
    ) -> Optional[Any]:
        """
        :param data: A list or dict
        :param identity_data: Dict of cached identity data
        :return: unwrapped list or dict
        """
        unwrapped = None
        if isinstance(data, dict):
            unwrapped = pydash.get(data, self.data_path)

        elif isinstance(data, list):
            unwrapped = []
            for item in data:
                unwrapped.append(pydash.get(item, self.data_path))
            # flatten the list to account for the event where the output of unwrapped
            # is a list of lists
            unwrapped = pydash.flatten(unwrapped)

        if unwrapped is None:
            logger.warning(
                f"{self.data_path} could not be found for the following post processing strategy: {self.get_strategy_name()}"
            )

        return unwrapped

    @staticmethod
    def get_configuration_model() -> StrategyConfiguration:
        return UnwrapPostProcessorConfiguration
