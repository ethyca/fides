"""
Async request handlers for access and erasure operations.

This module contains specialized handlers for processing different types of
async requests, including initial setup, callback completion, and polling continuation.
"""

# Type checking imports
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import AwaitingAsyncProcessing, AwaitingAsyncTask
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.privacy_request.request_task import AsyncTaskType
from fides.api.schemas.policy import Policy
from fides.api.schemas.saas.async_polling_configuration import (
    PollingResultRequest,
    PollingStatusRequest,
)
from fides.api.service.async_dsr.handlers.polling_request_handler import (
    PollingRequestHandler,
)
from fides.api.service.async_dsr.utils import (
    classify_async_type,
    handle_polling_initial_request,
)
from fides.api.util.collection_util import Row

if TYPE_CHECKING:
    from fides.api.service.connectors.query_configs.saas_query_config import (
        SaaSQueryConfig,
    )
    from fides.api.service.connectors.saas_connector import SaaSConnector
    from fides.api.task.graph_task import ExecutionNode


class AsyncAccessHandler:
    """Handles all async access request logic"""

    def __init__(
        self,
        status_request: Optional[PollingStatusRequest],
        result_request: Optional[PollingResultRequest],
    ):
        self.status_request = status_request
        self.result_request = result_request

    def handle_async_request(
        self,
        request_task: RequestTask,
        connection_config: ConnectionConfig,
        query_config: "SaaSQueryConfig",
        input_data: Dict[str, List[Any]],
        session: Session,
    ) -> List[Row]:
        """
        Main async access handler - routes to appropriate sub-handler.

        Handles ALL async access logic including initial setup, callbacks, and polling continuation.
        """
        # Derive related objects from request_task and query_config
        privacy_request = request_task.privacy_request
        policy = privacy_request.policy

        from fides.api.service.connectors.saas_connector import SaaSConnector

        connector = SaaSConnector(connection_config)

        async_type = classify_async_type(request_task, query_config)

        if async_type == "callback_completion":
            return self.handle_callback_completion(request_task)
        elif async_type == "polling_continuation":
            return self.handle_polling_continuation(
                connector, request_task, query_config, session
            )
        elif async_type == "initial_async":
            return self.handle_initial_setup(
                connector,
                request_task,
                query_config,
                privacy_request,
                input_data,
                policy,
                session,
            )
        else:
            # Should not reach here if detection logic is correct
            logger.warning(f"Unexpected async type '{async_type}' for request task {request_task.id}")
            return []

    def handle_callback_completion(self, request_task: RequestTask) -> List[Row]:
        """Handle completed callback requests"""
        logger.info(
            "Access callback succeeded for request task '{}'", request_task.id
        )
        return request_task.get_access_data()

    def handle_polling_continuation(
        self,
        connector: "SaaSConnector",
        request_task: RequestTask,
        query_config: "SaaSQueryConfig",
        session: Session,
    ) -> List[Row]:
        """Handle polling continuation requests"""
        logger.info(f"Continuing polling for access task {request_task.id}")

        # Ensure request_task is attached to the session
        if Session.object_session(request_task) != session:
            request_task = session.merge(request_task)

        # Use the provided session
        from fides.api.service.async_dsr.handlers.polling_continuation_handler import (
            PollingContinuationHandler,
        )

        polling_complete = PollingContinuationHandler(session).execute_polling_requests(
            request_task, query_config, connector
        )

        if not polling_complete:
            # Polling still in progress - raise exception to keep task in polling status

            raise AwaitingAsyncProcessing("Polling in progress")

        # Polling is complete - return the accumulated data
        return request_task.get_access_data()

    def handle_initial_setup(
        self,
        connector: "SaaSConnector",
        request_task: RequestTask,
        query_config: "SaaSQueryConfig",
        privacy_request: PrivacyRequest,
        input_data: Dict[str, List[Any]],
        policy: Policy,
        session: Session,
    ) -> List[Row]:
        """Handle initial async request setup for access requests"""

        read_requests = query_config.get_read_requests_by_identity()

        # Filter to get only the requests that need async processing
        async_requests_to_process = [
            req for req in read_requests if req.async_config and request_task.id
        ]

        # If there are no async requests, we shouldn't be in this handler.
        if not async_requests_to_process:
            logger.warning(
                f"Async handler was called, but no async-configured read requests were found for task {request_task.id}."
            )
            return []

        # Process all identified async requests
        for read_request in async_requests_to_process:
            # Validate async strategy with proper enum value checking
            from fides.api.service.async_dsr.strategies.async_dsr_strategy_factory import (
                get_strategy,
            )

            strategy = get_strategy(
                read_request.async_config.strategy,
                read_request.async_config.configuration,
            )

            request_task.async_type = AsyncTaskType(strategy.type)
            session.add(request_task)
            session.commit()

            if request_task.async_type == AsyncTaskType.polling:
                # This handler is only for the *initial* setup. We assume no sub-requests exist yet,
                # as `classify_async_type` would have routed us to the continuation handler otherwise.
                logger.info(
                    f"Creating initial polling sub-requests for task {request_task.id}"
                )

                handle_polling_initial_request(
                    privacy_request,
                    request_task,
                    query_config,
                    strategy,  # type: ignore
                    read_request,
                    input_data,
                    policy,
                    session,
                    connector.create_client(),
                )
                # Refresh the request_task to see newly created sub-requests
                session.refresh(request_task)

        # Since we have processed at least one async request, enter the polling state.
        connection_name = connector.configuration.name or connector.saas_config.name
        message = f"Polling {connection_name} for access results. Results may take some time to be available."
        raise AwaitingAsyncProcessing(message)


class AsyncErasureHandler:
    """Handles all async erasure request logic"""

    @staticmethod
    def handle_async_request(
        request_task: RequestTask,
        query_config: "SaaSQueryConfig",
        rows: List[Row],
        node: "ExecutionNode",
        session: Session,
    ) -> int:
        """
        Main async erasure handler - routes to appropriate sub-handler.

        Handles ALL async erasure logic including initial setup, callbacks, and polling continuation.
        """
        # Derive related objects from request_task and query_config
        privacy_request = request_task.privacy_request
        policy = privacy_request.policy

        from fides.api.service.connectors.saas_connector import SaaSConnector

        connector = SaaSConnector(query_config.connection_config)

        async_type = classify_async_type(request_task, query_config)

        if async_type == "callback_completion":
            return AsyncErasureHandler.handle_callback_completion(request_task)
        elif async_type == "polling_continuation":
            return AsyncErasureHandler.handle_polling_continuation(
                connector, request_task, query_config, session
            )
        elif async_type == "initial_async":
            return AsyncErasureHandler.handle_initial_setup(
                connector,
                request_task,
                query_config,
                privacy_request,
                rows,
                policy,
                node,
                session,
            )
        else:
            # Should not reach here if detection logic is correct
            logger.warning(f"Unexpected async type '{async_type}' for request task {request_task.id}")
            return 0

    @staticmethod
    def handle_callback_completion(request_task: RequestTask) -> int:
        """Handle completed callback requests"""
        logger.info(
            "Masking callback succeeded for request task '{}'", request_task.id
        )
        # If we've received the callback for this node, return rows_masked directly
        return request_task.rows_masked or 0

    @staticmethod
    def handle_polling_continuation(
        connector: "SaaSConnector",
        request_task: RequestTask,
        query_config: "SaaSQueryConfig",
        session: Session,
    ) -> int:
        """Handle polling continuation requests"""
        logger.info(f"Continuing polling for erasure task {request_task.id}")

        # Use the provided session
        from fides.api.service.async_dsr.handlers.polling_continuation_handler import (
            PollingContinuationHandler,
        )

        polling_complete = PollingContinuationHandler(session).execute_polling_requests(
            request_task, query_config, connector
        )

        if not polling_complete:
            # Polling still in progress - raise exception to keep task in polling status
            from fides.api.common_exceptions import AwaitingAsyncProcessing

            raise AwaitingAsyncProcessing("Polling in progress")

        # Polling is complete - return the accumulated count
        return request_task.rows_masked or 0

    @staticmethod
    def handle_initial_setup(
        connector: "SaaSConnector",
        request_task: RequestTask,
        query_config: "SaaSQueryConfig",
        privacy_request: PrivacyRequest,
        rows: List[Row],
        policy: Policy,
        node: "ExecutionNode",
    ) -> int:
        """Handle initial async request setup for erasure requests"""

        # For erasure, we look at masking requests (delete/update requests)
        # Use the provided session
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
            if request.async_config and request_task.id:  # Only supported in DSR 3.0
                # Validate async strategy with proper enum value checking
                from fides.api.service.async_dsr.strategies.async_dsr_strategy_factory import (
                    get_strategy,
                )

                strategy = get_strategy(
                    request.async_config.strategy,
                    request.async_config.configuration,
                )

                request_task.async_type = AsyncTaskType(strategy.type)

                if request.async_config.strategy == AsyncTaskType.callback.value:
                    # For callback strategy, we typically need to execute the initial request
                    # to trigger the async callback process, then wait for callback
                    # Execute the initial masking request here before raising AwaitingAsyncTask
                    if (
                        request.path
                    ):  # Only execute if there's an actual request to make
                        # Execute the initial masking request
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
                                        "Skipping optional masking request on node {}: {}",
                                        node.address.value,
                                        exc,
                                    )
                                    continue
                                raise exc

                    # Asynchronous callback masking request detected in saas config.
                    # If the masking request was marked to expect async results, original responses are ignored
                    # and we raise an AwaitingAsyncTask to put this task in an awaiting_processing state.
                    raise AwaitingAsyncTask()
                elif request.async_config.strategy == AsyncTaskType.polling.value:
                    # For polling strategy, we execute the initial request to start the async process
                    # then wait for polling to check results

                    # Check if sub-requests already exist to prevent duplicate execution
                    existing_sub_requests = request_task.sub_requests.count()
                    if existing_sub_requests == 0:
                        logger.info(
                            f"Executing initial masking request for polling task {request_task.id}"
                        )
                        if (
                            request.path
                        ):  # Only execute if there's an actual request to make
                            # Execute the initial masking request
                            client = connector.create_client()
                            for row in rows:
                                try:
                                    prepared_request = (
                                        query_config.generate_update_stmt(
                                            row, policy, privacy_request
                                        )
                                    )
                                    client.send(prepared_request, request.ignore_errors)
                                    rows_updated += 1
                                except ValueError as exc:
                                    if request.skip_missing_param_values:
                                        logger.debug(
                                            "Skipping optional masking request on node {}: {}",
                                            node.address.value,
                                            exc,
                                        )
                                        continue
                                    raise exc
                    else:
                        logger.info(
                            f"Sub-requests already exist for erasure task {request_task.id}, skipping initial request execution"
                        )

                    # Asynchronous polling masking request detected in saas config.
                    # If the masking request was marked to expect async results, original responses are ignored
                    # and we raise an AwaitingAsyncProcessing to put this task in a polling state.
                    connection_name = connector.configuration.name or connector.saas_config.name
                    message = f"Polling {connection_name} for erasure results. Results may take some time to be available."
                    raise AwaitingAsyncProcessing(message)

        # Should not reach here if we detected async requests correctly
        logger.warning(
            f"No async configuration found for erasure task {request_task.id}"
        )
        return rows_updated
