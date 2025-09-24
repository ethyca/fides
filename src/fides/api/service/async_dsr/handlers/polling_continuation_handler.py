"""
Polling continuation handler for async DSR operations.

This handler orchestrates the polling continuation process, managing the lifecycle
of polling requests and coordinating between status checking, result processing,
and task completion.
"""

# Type checking imports
from typing import TYPE_CHECKING, Any, Dict, List

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.models.privacy_request import RequestTask
from fides.api.models.privacy_request.request_task import RequestTaskSubRequest
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.service.async_dsr.handlers.polling_request_handler import (
    PollingRequestHandler,
)
from fides.api.service.async_dsr.handlers.polling_result_handler import (
    PollingResultHandler,
)
from fides.api.service.async_dsr.strategies.async_dsr_strategy_factory import (
    get_strategy,
)
from fides.api.service.async_dsr.utils import save_polling_results
from fides.api.util.collection_util import Row

if TYPE_CHECKING:
    from fides.api.service.connectors.query_configs.saas_query_config import (
        SaaSQueryConfig,
    )
    from fides.api.service.connectors.saas_connector import SaaSConnector


class PollingContinuationHandler:
    """
    Handler for polling continuation operations.

    Orchestrates the polling continuation process by managing status checks,
    result processing, and determining polling completion status.
    """

    def __init__(self, db: Session):
        self.db = db

    def execute_polling_requests(
        self,
        polling_task: RequestTask,
        query_config: "SaaSQueryConfig",
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
            masking_request = query_config.get_masking_request()
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

                    # Create polling handler and check status
                    polling_handler = PollingRequestHandler(
                        strategy.status_request, strategy.result_request
                    )
                    status = polling_handler.get_status_request(
                        client, param_values, connector.secrets
                    )

                    if status:
                        # Mark sub-request complete and get results
                        sub_request.update_status(
                            self.db, ExecutionLogStatus.complete.value
                        )
                        polling_result = polling_handler.get_result_request(
                            client, param_values, connector.secrets
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
