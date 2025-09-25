from io import BytesIO
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from uuid import uuid4

import pydash
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    AwaitingAsyncProcessing,
    FidesopsException,
    PrivacyRequestError,
)
from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
    AttachmentType,
)
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import RequestTask
from fides.api.models.privacy_request.request_task import (
    AsyncTaskType,
    RequestTask,
    RequestTaskSubRequest,
)
from fides.api.models.storage import get_active_default_storage_config
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.saas.async_polling_configuration import (
    PollingAsyncDSRConfiguration,
)
from fides.api.schemas.saas.saas_config import ReadSaaSRequest
from fides.api.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.service.async_dsr.handlers.polling_request_handler import (
    PollingRequestHandler,
)
from fides.api.service.async_dsr.strategies.async_dsr_strategy import AsyncDSRStrategy
from fides.api.service.async_dsr.utils import (
    AsyncPhase,
    get_async_phase,
    get_connection_config_from_task,
)
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.util.collection_util import Row

if TYPE_CHECKING:
    from fides.api.service.connectors.query_configs.saas_query_config import (
        SaaSQueryConfig,
    )
    from fides.api.service.connectors.saas_connector import SaaSConnector


class AsyncPollingStrategy(AsyncDSRStrategy):
    """
    Enhanced strategy for polling async DSR requests.
    Works for both access and erasure operations with internal phase-based organization.
    """

    type = AsyncTaskType.polling
    configuration_model = PollingAsyncDSRConfiguration

    def __init__(self, session: Session, configuration: PollingAsyncDSRConfiguration):
        self.session = session
        self.status_request = configuration.status_request
        self.result_request = configuration.result_request

    def async_retrieve_data(
        self,
        request_task_id: str,
        query_config: "SaaSQueryConfig",
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """
        Execute async retrieve data with internal phase routing.
        """
        # Look up the request task using the strategy's session
        request_task = (
            self.session.query(RequestTask)
            .filter(RequestTask.id == request_task_id)
            .first()
        )
        if not request_task:
            raise ValueError(f"RequestTask with id {request_task_id} not found")

        async_phase = get_async_phase(request_task, query_config)

        if async_phase == AsyncPhase.initial_async:
            return self._initial_request_access(request_task, query_config, input_data)
        elif async_phase == AsyncPhase.polling_continuation:
            return self._polling_continuation_access(request_task, query_config)
        else:
            logger.warning(
                f"Unexpected async phase '{async_phase}' for polling access task {request_task.id}"
            )
            return []

    def async_mask_data(
        self,
        request_task_id: str,
        query_config: "SaaSQueryConfig",
        rows: List[Row],
    ) -> int:
        """
        Execute async mask data with internal phase routing.
        """
        # Look up the request task using the strategy's session
        request_task = (
            self.session.query(RequestTask)
            .filter(RequestTask.id == request_task_id)
            .first()
        )
        if not request_task:
            raise ValueError(f"RequestTask with id {request_task_id} not found")

        async_phase = get_async_phase(request_task, query_config)

        if async_phase == AsyncPhase.initial_async:
            return self._initial_request_erasure(request_task, query_config, rows)
        elif async_phase == AsyncPhase.polling_continuation:
            return self._polling_continuation_erasure(request_task, query_config)
        else:
            logger.warning(
                f"Unexpected async phase '{async_phase}' for polling erasure task {request_task.id}"
            )
            return 0

    # Private helper methods

    def _initial_request_access(
        self,
        request_task: RequestTask,
        query_config: "SaaSQueryConfig",
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Handle initial setup for access polling requests."""
        logger.info(f"Initial polling request for access task {request_task.id}")

        # Get derived objects from request_task
        privacy_request = request_task.privacy_request
        policy = privacy_request.policy
        connection_config = get_connection_config_from_task(self.session, request_task)

        from fides.api.service.connectors.saas_connector import SaaSConnector

        connector = SaaSConnector(connection_config)

        read_requests = query_config.get_read_requests_by_identity()

        # Filter to get only the requests that need async processing
        async_requests_to_process = [req for req in read_requests if req.async_config]

        # If there are no async requests, we shouldn't be in this handler.
        if not async_requests_to_process:
            logger.warning(
                f"Async handler was called, but no async-configured read requests were found for task {request_task.id}."
            )
            return []

        # Process all identified async requests
        for read_request in async_requests_to_process:
            # Set async_type based on our strategy type
            request_task.async_type = AsyncTaskType.polling
            self.session.add(request_task)
            self.session.commit()

            # This handler is only for the *initial* setup. We assume no sub-requests exist yet,
            # as `get_async_phase` would have routed us to the continuation handler otherwise.
            logger.info(
                f"Creating initial polling sub-requests for task {request_task.id}"
            )

            self._handle_polling_initial_request(
                request_task,
                query_config,
                read_request,
                input_data,
                policy,
                connector.create_client(),
            )
            # Refresh the request_task to see newly created sub-requests
            self.session.refresh(request_task)

        # Since we have processed at least one async request, enter the polling state.
        connection_name = connector.configuration.name or connector.saas_config.name
        message = (
            f"Waiting for next scheduled check of {connection_name} access results."
        )
        raise AwaitingAsyncProcessing(message)

    def _initial_request_erasure(
        self,
        request_task: RequestTask,
        query_config: "SaaSQueryConfig",
        rows: List[Row],
    ) -> int:
        """Handle initial setup for erasure polling requests."""
        logger.info(f"Initial polling request for erasure task {request_task.id}")

        # Get derived objects from request_task
        privacy_request = request_task.privacy_request
        policy = privacy_request.policy
        connection_config = get_connection_config_from_task(self.session, request_task)

        from fides.api.service.connectors.saas_connector import SaaSConnector

        connector = SaaSConnector(connection_config)

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
            if request.async_config and request_task.id:  # Only supported in DSR 3.0
                # Set async_type based on our strategy type
                request_task.async_type = AsyncTaskType.polling
                self.session.add(request_task)
                self.session.commit()

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
                else:
                    logger.info(
                        f"Sub-requests already exist for erasure task {request_task.id}, skipping initial request execution"
                    )

                # Asynchronous polling masking request detected in saas config.
                # If the masking request was marked to expect async results, original responses are ignored
                # and we raise an AwaitingAsyncProcessing to put this task in a polling state.
                connection_name = (
                    connector.configuration.name or connector.saas_config.name
                )
                message = f"Waiting for next scheduled check of {connection_name} erasure results."
                raise AwaitingAsyncProcessing(message)

        # Should not reach here if we detected async requests correctly
        logger.warning(
            f"No async configuration found for erasure task {request_task.id}"
        )
        return rows_updated

    def _polling_continuation_access(
        self, request_task: RequestTask, query_config: "SaaSQueryConfig"
    ) -> List[Row]:
        """Handle polling continuation for access requests."""
        logger.info(f"Continuing polling for access task {request_task.id}")

        # Create connector from request_task
        connection_config = get_connection_config_from_task(self.session, request_task)

        from fides.api.service.connectors.saas_connector import SaaSConnector

        connector = SaaSConnector(connection_config)

        polling_complete = self._execute_polling_requests(
            request_task, query_config, connector
        )

        if not polling_complete:
            # Polling still in progress - raise exception to keep task in polling status
            connection_name = connector.configuration.name or connector.saas_config.name
            message = (
                f"Waiting for next scheduled check of {connection_name} access results."
            )
            raise AwaitingAsyncProcessing(message)

        # Polling is complete - return the accumulated data
        return request_task.get_access_data()

    def _polling_continuation_erasure(
        self, request_task: RequestTask, query_config: "SaaSQueryConfig"
    ) -> int:
        """Handle polling continuation for erasure requests."""
        logger.info(f"Continuing polling for erasure task {request_task.id}")

        # Create connector from request_task
        connection_config = get_connection_config_from_task(self.session, request_task)
        from fides.api.service.connectors.saas_connector import SaaSConnector

        connector = SaaSConnector(connection_config)

        # Use internal orchestration (moved from PollingContinuationHandler)
        polling_complete = self._execute_polling_requests(
            request_task, query_config, connector
        )

        if not polling_complete:
            connection_name = connector.configuration.name or connector.saas_config.name
            message = f"Waiting for next scheduled check of {connection_name} erasure results."
            raise AwaitingAsyncProcessing(message)

        # Polling is complete - return the accumulated count
        return request_task.rows_masked or 0

    def _handle_access_result(
        self,
        db,
        polling_result,
        request_task,
        rows_accumulator: List[Row],
    ) -> None:
        """Handle result for access requests."""
        if polling_result.result_type == "rows":
            # Structured data - add to rows collection
            if isinstance(polling_result.data, list):
                rows_accumulator.extend(polling_result.data)
            else:
                logger.warning(
                    f"Expected list for rows result, got {type(polling_result.data)}"
                )

        elif polling_result.result_type == "attachment":
            # File attachment - store and link to request task
            try:
                attachment_id = self._store_polling_attachment(
                    request_task,
                    attachment_data=polling_result.data,
                    filename=polling_result.metadata.get(
                        "filename", f"attachment_{str(uuid4())[:8]}"
                    ),
                )

                # Add attachment metadata to collection data
                _add_attachment_metadata_to_rows(db, attachment_id, rows_accumulator)

            except Exception as exc:
                raise PrivacyRequestError(f"Attachment storage failed: {exc}")
        else:
            raise PrivacyRequestError(
                f"Unsupported result type: {polling_result.result_type}"
            )

    def _save_polling_results(
        self,
        polling_task: RequestTask,
        rows: Optional[List[Row]],
        affected_records: Optional[List[int]],
    ) -> None:
        """Save polling results to the request task."""
        if rows is not None:
            # Access request - save rows
            existing_data = polling_task.access_data or []
            existing_data.extend(rows)
            polling_task.access_data = existing_data
            polling_task.save(self.session)
        elif affected_records is not None:
            # Erasure request - accumulate affected records count
            current_count = polling_task.rows_masked or 0
            polling_task.rows_masked = current_count + sum(affected_records)
            polling_task.save(self.session)

    def _store_polling_attachment(
        self,
        request_task: RequestTask,
        attachment_data: bytes,
        filename: str,
    ) -> str:
        """
        Store polling attachment data and return attachment ID.

        This utility function handles the storage of attachment data
        from polling results and creates the necessary database records.
        """
        try:
            # Get active storage config
            storage_config = get_active_default_storage_config(self.session)
            if not storage_config:
                raise PrivacyRequestError("No active storage configuration found")

            # Create attachment record and upload to storage
            attachment = Attachment.create_and_upload(
                db=self.session,
                data={
                    "file_name": filename,
                    "attachment_type": AttachmentType.include_with_access_package,
                    "storage_key": storage_config.key,
                },
                attachment_file=BytesIO(attachment_data),
            )

            # Create attachment references
            AttachmentReference.create(
                db=self.session,
                data={
                    "attachment_id": attachment.id,
                    "reference_id": request_task.id,
                    "reference_type": AttachmentReferenceType.request_task,
                },
            )

            AttachmentReference.create(
                db=self.session,
                data={
                    "attachment_id": attachment.id,
                    "reference_id": request_task.privacy_request.id,
                    "reference_type": AttachmentReferenceType.privacy_request,
                },
            )

            logger.info(
                f"Successfully stored polling attachment {attachment.id} for request_task {request_task.id}"
            )
            return attachment.id

        except Exception as e:
            logger.error(f"Failed to store polling attachment: {e}")
            raise PrivacyRequestError(f"Failed to store polling attachment: {e}")

    def _handle_polling_initial_request(
        self,
        request_task: RequestTask,
        query_config: "SaaSQueryConfig",
        read_request: ReadSaaSRequest,
        input_data: Dict[str, Any],
        policy: Policy,
        client: "AuthenticatedClient",
    ) -> None:
        """
        Handles the setup for asynchronous initial requests.
        The main read request serves as the initial request.
        """
        query_config.action = "Polling - start"
        prepared_requests: List[Tuple[SaaSRequestParams, Dict[str, Any]]] = (
            query_config.generate_requests(input_data, policy, read_request)
        )
        logger.info(f"Prepared requests: {len(prepared_requests)}")
        # Execute the main read request as the initial request and extract correlation_id

        for next_request, param_value_map in prepared_requests:
            logger.info(f"Executing initial request: {next_request}")
            response = client.send(next_request)

            if not response.ok:
                raise FidesopsException(
                    f"Initial async request failed with status code {response.status_code}: {response.text}"
                )

            # Extract correlation_id from response using correlation_id_path
            try:
                response_data = response.json()
                correlation_id = pydash.get(
                    response_data, read_request.correlation_id_path
                )
                if not correlation_id:
                    raise FidesopsException(
                        f"Could not extract correlation ID from response using path: {read_request.correlation_id_path}"
                    )
            except ValueError as exc:
                raise FidesopsException(
                    f"Invalid JSON response from initial request: {exc}"
                )

            param_value_map["correlation_id"] = str(correlation_id)
            # Use the provided session for sub-request creation
            logger.warning(f"About to create sub-request for task {request_task.id}")
            self._save_sub_request_data(request_task, param_value_map)
            logger.warning(f"Created sub-request for task {request_task.id}")

            # Verify it was created
            final_count = (
                self.session.query(RequestTaskSubRequest)
                .filter(RequestTaskSubRequest.request_task_id == request_task.id)
                .count()
            )
            logger.warning(
                f"Sub-request count after creation for task {request_task.id}: {final_count}"
            )

    def _save_sub_request_data(
        self,
        request_task: RequestTask,
        param_values_map: Dict[str, Any],
    ) -> None:
        """
        Saves the request data for future use in the request task on async requests.
        """
        # Create new sub-request entry
        sub_request = RequestTaskSubRequest.create(
            self.session,
            data={
                "request_task_id": request_task.id,
                "param_values": param_values_map,
                "sub_request_status": "pending",
            },
        )
        logger.warning(
            f"Created sub-request {sub_request.id} for task '{request_task.id}': {param_values_map}"
        )

        # Verify it was created by querying immediately
        count_after_create = (
            self.session.query(RequestTaskSubRequest)
            .filter(RequestTaskSubRequest.request_task_id == request_task.id)
            .count()
        )
        logger.warning(
            f"Sub-request count after creation for task {request_task.id}: {count_after_create}"
        )

    def _execute_polling_requests(
        self,
        polling_task: RequestTask,
        query_config: "SaaSQueryConfig",
        connector: "SaaSConnector",
    ) -> bool:
        """
        Internal polling execution orchestrator.

        Coordinates the entire polling process including status checking,
        result processing, and task lifecycle management.

        Returns:
            bool: True if all polling is complete, False if still in progress
        """

        # Get appropriate requests based on action type
        if polling_task.action_type == ActionType.access:
            requests = query_config.get_read_requests_by_identity()
            rows_accumulator: List[Row] = []
            affected_records_accumulator = None
        elif polling_task.action_type == ActionType.erasure:
            masking_request = query_config.get_masking_request()
            if not masking_request:
                from fides.api.common_exceptions import PrivacyRequestError

                raise PrivacyRequestError(
                    f"No masking request found for erasure task {polling_task.id}"
                )
            requests = [masking_request]
            rows_accumulator = None
            affected_records_accumulator: List[int] = []
        else:
            from fides.api.common_exceptions import PrivacyRequestError

            raise PrivacyRequestError(
                f"Unsupported action type: {polling_task.action_type}"
            )

        for request in requests:
            if request.async_config:
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
                        self.status_request, self.result_request
                    )

                    # Check for status override vs standard HTTP request
                    if self.status_request.request_override:
                        # Handle status override function directly
                        from fides.api.service.saas_request.saas_request_override_factory import (
                            SaaSRequestOverrideFactory,
                            SaaSRequestType,
                        )

                        override_function = SaaSRequestOverrideFactory.get_override(
                            self.status_request.request_override,
                            SaaSRequestType.POLLING_STATUS,
                        )

                        # Override functions return boolean status directly
                        status = override_function(
                            client=client,
                            param_values=param_values,
                            request_config=self.status_request,
                            secrets=connector.secrets,
                        )
                    else:
                        # Standard HTTP status request
                        response = polling_handler.get_status_response(
                            client, param_values
                        )

                        # Process status response
                        from fides.api.service.async_dsr.handlers.polling_response_handler import (
                            PollingResponseProcessor,
                        )

                        status = PollingResponseProcessor.evaluate_status_response(
                            response,
                            self.status_request.status_path,
                            self.status_request.status_completed_value,
                        )

                    if status:
                        # Mark sub-request complete and get results
                        sub_request.update_status(
                            self.session, ExecutionLogStatus.complete.value
                        )

                        # Check for override vs standard HTTP request
                        if self.result_request.request_override:
                            # Handle override function directly
                            from fides.api.service.saas_request.saas_request_override_factory import (
                                SaaSRequestOverrideFactory,
                                SaaSRequestType,
                            )

                            override_function = SaaSRequestOverrideFactory.get_override(
                                self.result_request.request_override,
                                SaaSRequestType.POLLING_RESULT,
                            )

                            polling_result = override_function(
                                client=client,
                                param_values=param_values,
                                request_config=self.result_request,
                                secrets=connector.secrets,
                            )
                        else:
                            # Standard HTTP request processing
                            response = polling_handler.get_result_response(
                                client, param_values
                            )

                            # We need to reconstruct the request path for processing
                            from fides.api.util.saas_util import map_param_values

                            prepared_result_request = map_param_values(
                                "result",
                                "polling request",
                                self.result_request,
                                param_values,
                            )

                            polling_result = (
                                PollingResponseProcessor.process_result_response(
                                    response,
                                    prepared_result_request.path or "",
                                    self.result_request.result_path,
                                )
                            )

                        # Handle results based on action type
                        if polling_task.action_type == ActionType.access:
                            self._handle_access_result(
                                self.session,
                                polling_result,
                                polling_task,
                                rows_accumulator,
                            )
                        elif polling_task.action_type == ActionType.erasure:
                            _handle_erasure_result(
                                polling_result,
                                affected_records_accumulator,
                            )
                    else:
                        logger.info(
                            f"Polling sub request - {sub_request.id} for task {polling_task.id} still not ready."
                        )

        # Check if all sub-requests are complete
        all_sub_requests: List[RequestTaskSubRequest] = polling_task.sub_requests.all()
        completed_sub_requests = [
            sub_request
            for sub_request in all_sub_requests
            if sub_request.sub_request_status == ExecutionLogStatus.complete.value
        ]

        # Save results to polling_task (RequestTask)
        self._save_polling_results(
            polling_task, rows_accumulator, affected_records_accumulator
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


# Private helper functions


def _handle_erasure_result(
    polling_result, affected_records_accumulator: List[int]
) -> None:
    """Handle result for erasure requests."""
    if polling_result.result_type == "rows":
        # For erasure, rows typically contain info about what was deleted
        # The count represents affected records
        if isinstance(polling_result.data, list):
            affected_records_accumulator.append(len(polling_result.data))
        else:
            # If it's a single response with count info, try to extract it
            affected_records_accumulator.append(1)

    elif polling_result.result_type == "attachment":
        # Erasure attachments might contain reports of what was deleted
        # For now, count as 1 affected record per attachment
        affected_records_accumulator.append(1)

    else:
        raise PrivacyRequestError(
            f"Unsupported erasure result type: {polling_result.result_type}"
        )


def _add_attachment_metadata_to_rows(db, attachment_id: str, rows: List[Row]) -> None:
    """Add attachment metadata to rows collection (like manual tasks do)."""
    from fides.api.models.attachment import Attachment

    attachment_record = (
        db.query(Attachment).filter(Attachment.id == attachment_id).first()
    )

    if attachment_record:
        try:
            size, url = attachment_record.retrieve_attachment()
            attachment_info = {
                "file_name": attachment_record.file_name,
                "download_url": str(url) if url else None,
                "file_size": size,
            }
        except Exception as exc:
            logger.warning(
                f"Could not retrieve attachment content for {attachment_record.file_name}: {exc}"
            )
            attachment_info = {
                "file_name": attachment_record.file_name,
                "download_url": None,
                "file_size": None,
            }

        # Add attachment to the polling results
        attachments_item = None
        for item in rows:
            if isinstance(item, dict) and "retrieved_attachments" in item:
                attachments_item = item
                break

        if attachments_item is None:
            attachments_item = {"retrieved_attachments": []}
            rows.append(attachments_item)

        attachments_item["retrieved_attachments"].append(attachment_info)
