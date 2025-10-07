from abc import abstractmethod
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from fides.api.models.privacy_request.request_task import AsyncTaskType, RequestTask
from fides.api.service.connectors.query_configs.saas_query_config import SaaSQueryConfig
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.strategy import Strategy
from fides.api.util.collection_util import Row


class AsyncDSRStrategy(Strategy):
    """Abstract base class for async DSR strategies"""

    type: AsyncTaskType
    session: Session

    @abstractmethod
    def async_retrieve_data(
        self,
        client: AuthenticatedClient,
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
        client: AuthenticatedClient,
        request_task_id: str,
        query_config: SaaSQueryConfig,
        rows: List[Row],
    ) -> int:
        """
        Execute async mask data.
        """

    def _get_request_task(self, request_task_id: str) -> RequestTask:
        """Get request task by ID or raise ValueError if not found."""
        request_task = (
            self.session.query(RequestTask)
            .filter(RequestTask.id == request_task_id)
            .first()
        )
        if not request_task:
            raise ValueError(f"RequestTask with ID {request_task_id} not found")
        return request_task
