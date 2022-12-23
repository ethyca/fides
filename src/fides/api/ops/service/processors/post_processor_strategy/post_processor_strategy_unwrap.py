from typing import Any, Dict, List, Union

import pydash
from loguru import logger

from fides.api.ops.schemas.saas.strategy_configuration import (
    UnwrapPostProcessorConfiguration,
)
from fides.api.ops.service.processors.post_processor_strategy.post_processor_strategy import (
    PostProcessorStrategy,
)


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

    name = "unwrap"
    configuration_model = UnwrapPostProcessorConfiguration

    def __init__(self, configuration: UnwrapPostProcessorConfiguration):
        self.data_path = configuration.data_path

    def process(
        self,
        data: Union[List[Dict[str, Any]], Dict[str, Any]],
        identity_data: Dict[str, Any] = None,
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        :param data: A list or dict
        :param identity_data: dict of cached identity data
        :return: unwrapped list, dict, or empty list
        """

        result = []
        if isinstance(data, dict):
            unwrapped = pydash.get(data, self.data_path)
            if unwrapped is None:
                logger.warning(
                    "{} could not be found for the following post processing strategy: {}",
                    self.data_path,
                    self.name,
                )
            else:
                result = unwrapped
        elif isinstance(data, list):
            for item in data:
                unwrapped = pydash.get(item, self.data_path)
                if unwrapped is None:
                    logger.warning(
                        "{} could not be found for the following post processing strategy: {}",
                        self.data_path,
                        self.name,
                    )
                else:
                    result.append(unwrapped)
            # flatten the list to account for the event where the output of unwrapped
            # is a list of lists
            result = pydash.flatten(result)

        return result
