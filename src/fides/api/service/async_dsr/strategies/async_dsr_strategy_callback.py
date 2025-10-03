from typing import Any, Dict, List

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import AwaitingAsyncTask
from fides.api.models.privacy_request.request_task import AsyncTaskType, RequestTask
from fides.api.service.async_dsr.strategies.async_dsr_strategy import AsyncDSRStrategy
from fides.api.service.async_dsr.utils import AsyncPhase, get_async_phase
from fides.api.service.connectors.query_configs.saas_query_config import SaaSQueryConfig
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.util.collection_util import Row


class AsyncCallbackStrategy(AsyncDSRStrategy):
    """
    Enhanced strategy for callback async DSR requests.
    Works for both access and erasure operations with internal phase-based organization.
    """

    type = AsyncTaskType.callback

    def __init__(self, session: Session):
        self.session = session

    def async_retrieve_data(
        self,
        client: AuthenticatedClient,
        request_task_id: str,
        query_config: SaaSQueryConfig,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Execute async retrieve data with internal phase routing."""
        request_task = self._get_request_task(request_task_id)
        async_phase = get_async_phase(request_task, query_config)

        if async_phase == AsyncPhase.initial_async:
            return self._initial_request_access(
                client, request_task, query_config, input_data
            )
        if async_phase == AsyncPhase.callback_completion:
            return self._callback_completion_access(request_task)

        logger.warning(
            f"Unexpected async phase '{async_phase}' for callback access task {request_task.id}"
        )
        return []

    def async_mask_data(
        self,
        client: AuthenticatedClient,
        request_task_id: str,
        query_config: SaaSQueryConfig,
        rows: List[Row],
    ) -> int:
        """Execute async mask data with internal phase routing."""
        request_task = self._get_request_task(request_task_id)
        async_phase = get_async_phase(request_task, query_config)

        if async_phase == AsyncPhase.initial_async:
            return self._initial_request_erasure(
                client, request_task, query_config, rows
            )
        if async_phase == AsyncPhase.callback_completion:
            return self._callback_completion_erasure(request_task)

        logger.warning(
            f"Unexpected async phase '{async_phase}' for callback erasure task {request_task.id}"
        )
        return 0

    # Private helper methods

    def _initial_request_access(
        self,
        client: AuthenticatedClient,
        request_task: RequestTask,
        query_config: SaaSQueryConfig,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Handle initial setup for access callback requests."""
        logger.info(f"Initial callback request for access task {request_task.id}")

        read_requests = query_config.get_read_requests_by_identity()

        # Filter to get only the requests that need async processing
        async_requests_to_process = [
            req for req in read_requests if req.async_config and request_task.id
        ]

        # If there are no async requests, we shouldn't be in this handler.
        if not async_requests_to_process:
            logger.warning(
                f"Async callback handler was called, but no async-configured read requests were found for task {request_task.id}."
            )
            return []

        # Set async_type once for the request task
        request_task.async_type = AsyncTaskType.callback
        self.session.commit()

        # For callback strategy, we execute the initial request to trigger the callback
        # then wait for the external system to call us back via webhook.
        # The callback endpoint logic will then queue the request task for it
        # to be executed again with
        # AsyncCallbackStrategy.async_retrieve_data -> _callback_completion_access

        # Execute the initial callback request to trigger the async process
        privacy_request = request_task.privacy_request
        policy = privacy_request.policy

        for read_request in async_requests_to_process:
            if read_request.path:  # Only execute if there's an actual request to make
                try:
                    # Set the current request context
                    query_config.current_request = read_request
                    prepared_request = query_config.generate_query(input_data, policy)
                    # Execute the initial request to trigger the callback
                    client.send(prepared_request, read_request.ignore_errors)
                    logger.info(
                        f"Executed initial callback request for access task {request_task.id}"
                    )
                except ValueError as exc:
                    if read_request.skip_missing_param_values:
                        logger.debug(
                            "Skipping optional access callback request: {}",
                            exc,
                        )
                        continue
                    raise exc

        # Asynchronous callback access request detected in saas config.
        # We raise AwaitingAsyncTask to put this task in an awaiting_processing state.
        raise AwaitingAsyncTask(
            f"Awaiting callback from {request_task.dataset_name} for access results"
        )

    def _initial_request_erasure(
        self,
        client: AuthenticatedClient,
        request_task: RequestTask,
        query_config: SaaSQueryConfig,
        rows: List[Row],
    ) -> int:
        """Handle initial setup for erasure callback requests."""
        logger.info(f"Initial callback request for erasure task {request_task.id}")

        privacy_request = request_task.privacy_request
        policy = privacy_request.policy

        # For erasure, we only execute masking requests (delete/update requests)
        masking_request = query_config.get_masking_request()

        if not masking_request:
            logger.warning(
                f"No masking request found for erasure task {request_task.id}"
            )
            return 0

        rows_updated = 0

        # Check if the masking request has async_config and set async_type once
        if masking_request.async_config and request_task.id:
            request_task.async_type = AsyncTaskType.callback
            self.session.commit()

            if masking_request.path:
                for row in rows:
                    try:
                        prepared_request = query_config.generate_update_stmt(
                            row, policy, privacy_request
                        )
                        client.send(prepared_request, masking_request.ignore_errors)
                        rows_updated += 1
                    except ValueError as exc:
                        if masking_request.skip_missing_param_values:
                            logger.debug(
                                "Skipping optional masking request: {}",
                                exc,
                            )
                            continue
                        raise exc

            raise AwaitingAsyncTask("Awaiting erasure callback results")

        logger.warning(
            f"No async configuration found for erasure task {request_task.id}"
        )
        return rows_updated

    def _callback_completion_access(self, request_task: RequestTask) -> List[Row]:
        """Handle completion of access callback requests."""
        logger.info(f"Access callback succeeded for request task '{request_task.id}'")
        return request_task.get_access_data()

    def _callback_completion_erasure(self, request_task: RequestTask) -> int:
        """Handle completion of erasure callback requests."""
        logger.info(f"Masking callback succeeded for request task '{request_task.id}'")
        return request_task.rows_masked or 0
