from typing import TYPE_CHECKING, Any, Dict, List

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import AwaitingAsyncTask
from fides.api.models.privacy_request.request_task import AsyncTaskType, RequestTask
from fides.api.service.async_dsr.strategies.async_dsr_strategy import AsyncDSRStrategy
from fides.api.service.async_dsr.utils import (
    AsyncPhase,
    get_async_phase,
    get_connection_config_from_task,
)
from fides.api.util.collection_util import Row

if TYPE_CHECKING:
    from fides.api.service.connectors.query_configs.saas_query_config import (
        SaaSQueryConfig,
    )


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
        request_task_id: str,
        query_config: "SaaSQueryConfig",
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Execute async retrieve data with internal phase routing."""
        request_task = self._get_request_task(request_task_id)
        async_phase = get_async_phase(request_task, query_config)

        if async_phase == AsyncPhase.initial_async:
            return self._initial_request_access(request_task, query_config, input_data)
        elif async_phase == AsyncPhase.callback_completion:
            return self._callback_completion_access(request_task)
        else:
            logger.warning(
                f"Unexpected async phase '{async_phase}' for callback access task {request_task.id}"
            )
            return []

    def async_mask_data(
        self,
        request_task_id: str,
        query_config: "SaaSQueryConfig",
        rows: List[Row],
    ) -> int:
        """Execute async mask data with internal phase routing."""
        request_task = self._get_request_task(request_task_id)
        async_phase = get_async_phase(request_task, query_config)

        if async_phase == AsyncPhase.initial_async:
            return self._initial_request_erasure(request_task, query_config, rows)
        elif async_phase == AsyncPhase.callback_completion:
            return self._callback_completion_erasure(request_task)
        else:
            logger.warning(
                f"Unexpected async phase '{async_phase}' for callback erasure task {request_task.id}"
            )
            return 0

    # Private helper methods

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

    def _create_connector(self, request_task: RequestTask):
        """Create SaaS connector from request task."""
        from fides.api.service.connectors.saas_connector import SaaSConnector

        connection_config = get_connection_config_from_task(self.session, request_task)
        return SaaSConnector(connection_config)

    def _initial_request_access(
        self,
        request_task: RequestTask,
        query_config: "SaaSQueryConfig",
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

        # Process all identified async requests
        for read_request in async_requests_to_process:
            # Set async_type based on our strategy type
            request_task.async_type = AsyncTaskType.callback
            self.session.add(request_task)
            self.session.commit()

        # For callback strategy, we execute the initial request to trigger the callback
        # then wait for the external system to call us back via webhook
        # The actual callback execution and data processing happens in the webhook endpoint
        # which will eventually call _callback_completion_access when the callback succeeds

        connection_config = get_connection_config_from_task(self.session, request_task)
        from fides.api.service.connectors.saas_connector import SaaSConnector

        connector = SaaSConnector(connection_config)
        connection_name = connector.configuration.name or connector.saas_config.name

        # Execute the initial callback request to trigger the async process
        privacy_request = request_task.privacy_request
        policy = privacy_request.policy
        client = connector.create_client()

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
            f"Awaiting callback from {connection_name} for access results"
        )

    def _initial_request_erasure(
        self,
        request_task: RequestTask,
        query_config: "SaaSQueryConfig",
        rows: List[Row],
    ) -> int:
        """Handle initial setup for erasure callback requests."""
        logger.info(f"Initial callback request for erasure task {request_task.id}")

        privacy_request = request_task.privacy_request
        policy = privacy_request.policy
        connector = self._create_connector(request_task)

        # For erasure, we look at masking requests (delete/update requests)
        masking_request = query_config.get_masking_request()
        read_requests = (
            query_config.get_read_requests_by_identity()
        )  # May also have async config for erasure

        all_requests = []
        if masking_request:
            all_requests.append(masking_request)
        all_requests.extend(read_requests)
        rows_updated = 0

        for request in all_requests:
            if request.async_config and request_task.id:
                # Set async_type based on our strategy type
                request_task.async_type = AsyncTaskType.callback
                self.session.add(request_task)
                self.session.commit()

                if request.path:
                    client = connector.create_client()
                    for row in rows:
                        try:
                            prepared_request = query_config.generate_update_stmt(
                                row, policy, privacy_request
                            )
                            client.send(prepared_request, request.ignore_errors)
                            rows_updated += 1
                        except ValueError as exc:
                            if request.skip_missing_param_values:
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
