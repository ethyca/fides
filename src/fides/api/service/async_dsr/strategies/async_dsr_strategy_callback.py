from typing import Any, Dict, List

from fides.api.api.deps import get_autoclose_db_session as get_db
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.privacy_request.request_task import AsyncTaskType, RequestTask
from fides.api.service.async_dsr.handlers.async_request_handlers import (
    AsyncAccessHandler,
    AsyncErasureHandler,
)
from fides.api.service.async_dsr.strategies.async_dsr_strategy import AsyncDSRStrategy
from fides.api.service.connectors.query_configs.saas_query_config import SaaSQueryConfig
from fides.api.util.collection_util import Row


class CallbackAsyncDSRStrategy(AsyncDSRStrategy):
    """
    Strategy for callback async DSR requests.

    This strategy implements the abstract methods but they are not actively used
    since callback handling is done through webhook endpoints, not polling.
    """

    type = AsyncTaskType.callback

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
        with get_db() as session:
            # Look up the request task using the service's session
            request_task = (
                session.query(RequestTask)
                .filter(RequestTask.id == request_task_id)
                .first()
            )
            if not request_task:
                raise ValueError(f"RequestTask with id {request_task_id} not found")

            # Delegate to the existing handler with minimal parameters
            async_access_handler = AsyncAccessHandler()
            return async_access_handler.handle_async_request(
                request_task,
                connection_config,
                query_config,
                input_data,
                session,
            )

    def async_mask_data(
        self,
        connection_config: ConnectionConfig,
        query_config: SaaSQueryConfig,
        request_task_id: str,
        rows: List[Row],
        node: ExecutionNode,
    ) -> int:
        """
        Execute async mask data.
        """
        with get_db() as session:
            # Look up the request task using the service's session
            request_task = (
                session.query(RequestTask)
                .filter(RequestTask.id == request_task_id)
                .first()
            )
            if not request_task:
                raise ValueError(f"RequestTask with id {request_task_id} not found")

            # Delegate to the existing handler with minimal parameters
            return AsyncErasureHandler.handle_async_request(
                request_task,
                connection_config,
                query_config,
                rows,
                node,
                session,
            )
