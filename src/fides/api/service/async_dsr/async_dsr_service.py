"""
Core business logic service for async DSR operations.

This service provides the main orchestration and coordination for async DSR operations,
managing the lifecycle of polling requests and coordinating between different components.
"""

# Type checking imports
from typing import TYPE_CHECKING, Any, Dict, List

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.privacy_request import RequestTask
from fides.api.models.privacy_request.request_task import RequestTaskSubRequest
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.service.async_dsr.handlers.polling_result_handler import (
    PollingResultHandler,
)
from fides.api.service.async_dsr.utils import (
    execute_result_request,
    save_polling_results,
)
from fides.api.service.connectors.query_configs.saas_query_config import SaaSQueryConfig
from fides.api.util.collection_util import Row

if TYPE_CHECKING:
    from fides.api.service.connectors.saas_connector import SaaSConnector
    from fides.api.task.graph_task import ExecutionNode


class AsyncDSRService:
    """
    Core service for async DSR operations.

    Orchestrates polling execution, manages task lifecycle,
    and coordinates between detection, handling, and storage components.
    """

    def __init__(self, db: Session):
        self.db = db

    def handle_async_access_request(
        self,
        connection_config: ConnectionConfig,
        query_config: SaaSQueryConfig,
        request_task_id: str,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """
        Handle async access request using minimal parameters.
        Uses the service's database session to avoid detachment issues.
        """
        from fides.api.models.privacy_request import RequestTask
        from fides.api.service.async_dsr.handlers.async_request_handlers import (
            AsyncAccessHandler,
        )

        session = self.db

        # Look up the request task using the service's session
        request_task = (
            session.query(RequestTask).filter(RequestTask.id == request_task_id).first()
        )
        if not request_task:
            raise ValueError(f"RequestTask with id {request_task_id} not found")

        # Delegate to the existing handler with minimal parameters
        return AsyncAccessHandler.handle_async_request(
            request_task,
            connection_config,
            query_config,
            input_data,
            session,
        )

    def handle_async_erasure_request(
        self,
        connection_config: ConnectionConfig,
        query_config: SaaSQueryConfig,
        request_task_id: str,
        rows: List[Row],
        node: "ExecutionNode",
    ) -> int:
        """
        Handle async erasure request using minimal parameters.
        Uses the service's database session to avoid detachment issues.
        """
        from fides.api.models.privacy_request import RequestTask
        from fides.api.service.async_dsr.handlers.async_request_handlers import (
            AsyncErasureHandler,
        )

        session = self.db

        # Look up the request task using the service's session
        request_task = (
            session.query(RequestTask).filter(RequestTask.id == request_task_id).first()
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

    def execute_polling_requests(
        self,
        polling_task: RequestTask,
        query_config: SaaSQueryConfig,
        connector: "SaaSConnector",
    ) -> bool:
        """
        Main polling execution orchestrator.

        Coordinates the entire polling process including status checking,
        result processing, and task lifecycle management.

        Args:
            polling_task: The polling task to execute
            query_config: Query configuration for the requests
            connector: SaaS connector instance

        Returns:
            bool: True if all polling is complete, False if still in progress

        Raises:
            PrivacyRequestError: If polling execution fails
        """
        # Get appropriate requests based on action type
        if polling_task.action_type == ActionType.access:
            requests = query_config.get_read_requests_by_identity()
            rows_accumulator: List[Row] = []
            affected_records_accumulator = None
        elif polling_task.action_type == ActionType.erasure:
            # For erasure, we need masking/deletion requests
            from sqlalchemy.orm import Session

            session = Session.object_session(polling_task)
            masking_request = query_config.get_masking_request(session)
            if not masking_request:
                raise PrivacyRequestError(
                    f"No masking request found for erasure task {polling_task.id}"
                )
            requests = [masking_request]
            rows_accumulator = None
            affected_records_accumulator: List[int] = []
        else:
            raise PrivacyRequestError(
                f"Unsupported action type: {polling_task.action_type}"
            )

        for request in requests:
            if request.async_config:
                from fides.api.service.async_dsr.strategies.async_dsr_strategy_factory import (
                    get_strategy,
                )

                strategy = get_strategy(
                    request.async_config.strategy,
                    request.async_config.configuration,
                )
                client = connector.create_client()
                sub_requests: List[RequestTaskSubRequest] = (
                    polling_task.sub_requests.all()
                )

                for sub_request in sub_requests:
                    if (
                        sub_request.sub_request_status
                        == ExecutionLogStatus.complete.value
                    ):
                        logger.info(
                            f"Polling sub request - {sub_request.id} for task {polling_task.id} already completed."
                        )
                        continue

                    param_values = sub_request.param_values

                    # Check status
                    status = strategy.get_status_request(
                        client, param_values, connector.secrets
                    )

                    if status:
                        # Mark sub-request complete and get results
                        sub_request.update_status(
                            self.db, ExecutionLogStatus.complete.value
                        )
                        polling_result = execute_result_request(
                            strategy,
                            client,
                            param_values,
                            connector.secrets,
                        )

                        # Handle results based on action type
                        if polling_task.action_type == ActionType.access:
                            PollingResultHandler.handle_access_result(
                                self.db,
                                polling_result,
                                polling_task,
                                polling_task.privacy_request,
                                rows_accumulator,
                            )
                        elif polling_task.action_type == ActionType.erasure:
                            PollingResultHandler.handle_erasure_result(
                                polling_result,
                                polling_task,
                                affected_records_accumulator,
                            )
                    else:
                        logger.info(
                            f"Polling sub request - {sub_request.id} for task {polling_task.id} still not ready."
                        )

        # # Refresh the polling task to get the latest sub-request statuses
        # self.db.refresh(polling_task)

        # Check if all sub-requests are complete
        all_sub_requests: List[RequestTaskSubRequest] = polling_task.sub_requests.all()
        completed_sub_requests = [
            sr
            for sr in all_sub_requests
            if sr.sub_request_status == ExecutionLogStatus.complete.value
        ]

        # Save results to polling_task (RequestTask)
        save_polling_results(
            self.db, polling_task, rows_accumulator, affected_records_accumulator
        )

        if len(completed_sub_requests) < len(all_sub_requests):
            logger.info(
                f"Polling task {polling_task.id} has {len(completed_sub_requests)}/{len(all_sub_requests)} sub-requests complete."
            )
            return False  # Polling still in progress

        # All sub-requests are complete - save final results
        logger.info(
            f"All sub-requests complete for polling task {polling_task.id}. Polling complete."
        )
        return True  # Polling is complete
