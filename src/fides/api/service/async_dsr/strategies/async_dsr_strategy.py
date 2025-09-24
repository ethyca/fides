from abc import abstractmethod
from typing import Any, Dict, List

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.privacy_request.request_task import AsyncTaskType
from fides.api.schemas.saas.async_polling_configuration import PollingResult
from fides.api.service.connectors.query_configs.saas_query_config import SaaSQueryConfig
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.strategy import Strategy
from fides.api.util.collection_util import Row


class AsyncDSRStrategy(Strategy):
    """Abstract base class for async DSR strategies"""

    type: AsyncTaskType

    def async_retrieve_data(
        self,
        connection_config: ConnectionConfig,
        query_config: SaaSQueryConfig,
        request_task_id: str,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """
        Execute async retrieve data.
        """

    def async_mask_data(
        self,
        connection_config: ConnectionConfig,
        query_config: SaaSQueryConfig,
        request_task_id: str,
        rows: List[Row],
    ) -> int:
        """
        Execute async mask data.
        """
