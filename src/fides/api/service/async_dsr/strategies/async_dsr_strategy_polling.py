from typing import Any, Dict, List

from fides.api.api.deps import get_autoclose_db_session as get_db
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.privacy_request.request_task import AsyncTaskType, RequestTask
from fides.api.schemas.saas.async_polling_configuration import (
    PollingAsyncDSRConfiguration,
)
from fides.api.service.async_dsr.handlers.async_request_handlers import (
    AsyncAccessHandler,
    AsyncErasureHandler,
)
from fides.api.service.async_dsr.strategies.async_dsr_strategy import AsyncDSRStrategy
from fides.api.service.connectors.query_configs.saas_query_config import SaaSQueryConfig
from fides.api.util.collection_util import Row


class PollingAsyncDSRStrategy(AsyncDSRStrategy):
    """
    Unified strategy for polling async DSR requests.
    Works for both access and erasure operations.
    """

    type = AsyncTaskType.polling
    configuration_model = PollingAsyncDSRConfiguration

    def __init__(self, configuration: PollingAsyncDSRConfiguration):
        self.status_request = configuration.status_request
        self.result_request = configuration.result_request

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
            async_access_handler = AsyncAccessHandler(
                self.status_request,
                self.result_request,
            )
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
