from abc import abstractmethod
from typing import Any, Dict, List

from fides.api.models.privacy_request.request_task import AsyncTaskType
from fides.api.service.connectors.query_configs.saas_query_config import SaaSQueryConfig
from fides.api.service.strategy import Strategy
from fides.api.util.collection_util import Row


class AsyncDSRStrategy(Strategy):
    """Abstract base class for async DSR strategies"""

    type: AsyncTaskType

    @abstractmethod
    def async_retrieve_data(
        self,
        request_task_id: str,
        query_config: SaaSQueryConfig,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """
        Execute async retrieve data.
        """

    @abstractmethod
    def async_mask_data(
        self,
        request_task_id: str,
        query_config: SaaSQueryConfig,
        rows: List[Row],
    ) -> int:
        """
        Execute async mask data.
        """
