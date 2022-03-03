import logging
from typing import Any, Optional, Dict

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
    Given a path to a dict, returns the dict/list
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
    """

    def __init__(self, configuration: UnwrapPostProcessorConfiguration):
        self.data_path = configuration.data_path

    def get_strategy_name(self) -> str:
        return STRATEGY_NAME

    def process(
        self, data: Dict[str, Any], identity_data: Dict[str, Any] = None
    ) -> Optional[Any]:
        """
        :param data: A dict
        :param identity_data: Dict of cached identity data
        :return: unwrapped list or dict
        """
        if not isinstance(data, dict):
            logger.warning(
                f"Data is either None or not in expected format. Skipping processing for the following post processing strategy: {self.get_strategy_name()}."
            )
            return data
        unwrapped = pydash.objects.get(data, self.data_path, None)
        if unwrapped is None:
            logger.warning(
                f"{self.data_path} could not be found for the following post processing strategy: {self.get_strategy_name()}"
            )
        return unwrapped

    @staticmethod
    def get_configuration_model() -> StrategyConfiguration:
        return UnwrapPostProcessorConfiguration
