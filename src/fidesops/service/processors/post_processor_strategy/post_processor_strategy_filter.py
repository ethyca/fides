import logging
from typing import Any, Dict, List, Union

from fidesops.schemas.saas.strategy_configuration import (
    FilterPostProcessorConfiguration,
    IdentityParamRef,
    StrategyConfiguration,
)
from fidesops.service.processors.post_processor_strategy.post_processor_strategy import (
    PostProcessorStrategy,
)

STRATEGY_NAME = "filter"

logger = logging.getLogger(__name__)


class FilterPostProcessorStrategy(PostProcessorStrategy):
    """
    Filters object or array given field name and value
    Value can be reference a dynamic identity passed in through the request OR hard-coded value.
    E.g.
    data = [
        {
            "id": 1397429347
            "email_contact": somebody@email.com
            "name": Somebody Awesome
        },
        {
            "id": 238475234
            "email_contact": somebody-else@email.com
            "name": Somebody Cool
        }
    ]
    field: email_contact
    value: {"identity": email}, where email == somebody@email.com
    result = {
        id: 1397429347
        email_contact: somebody@email.com
        name: Somebody Awesome
    }
    """

    def __init__(self, configuration: FilterPostProcessorConfiguration):
        self.field = configuration.field
        self.value = configuration.value

    def get_strategy_name(self) -> str:
        return STRATEGY_NAME

    def process(
        self,
        data: Union[List[Dict[str, Any]], Dict[str, Any]],
        identity_data: Dict[str, Any] = None,
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        :param data: A list or a dict
        :param identity_data: dict of cached identity data
        :return: filtered dict, list of dicts, or empty list
        """

        if not data:
            return []

        # find value to filter by
        filter_value = self.value
        if isinstance(self.value, IdentityParamRef):
            if identity_data is None or identity_data.get(self.value.identity) is None:
                logger.warning(
                    f"Could not retrieve identity reference '{self.value.identity}' "
                    "due to missing identity data for the following post processing "
                    f"strategy: {self.get_strategy_name()}"
                )
                return []
            filter_value = identity_data.get(self.value.identity)

        try:
            if isinstance(data, list):
                return [item for item in data if item[self.field] == filter_value]
            return data if data[self.field] == filter_value else []
        except KeyError:
            logger.warning(
                f"{self.field} could not be found on data for the following post processing strategy: {self.get_strategy_name()}"
            )
            return []

    @staticmethod
    def get_configuration_model() -> StrategyConfiguration:
        return FilterPostProcessorConfiguration
