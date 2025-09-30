# datetime and timedelta imports would be used in RequestTaskSubRequest helper methods
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Union, cast
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
from fides.api.models.privacy_request.request_task import (
    AsyncTaskType,
    RequestTask,
    RequestTaskSubRequest,
)
from fides.api.models.storage import get_active_default_storage_config
from fides.api.models.worker_task import ExecutionLogStatus

# ExecutionLogStatus would be used in RequestTaskSubRequest helper methods
from fides.api.schemas.policy import ActionType
from fides.api.schemas.saas.async_polling_configuration import (
    AsyncPollingConfiguration,
    PollingResult,
)
from fides.api.schemas.saas.saas_config import ReadSaaSRequest, SaaSRequest
from fides.api.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.service.async_dsr.handlers.polling_request_handler import (
    PollingRequestHandler,
)
from fides.api.service.async_dsr.handlers.polling_response_handler import (
    PollingResponseProcessor,
)
from fides.api.service.async_dsr.strategies.async_dsr_strategy import AsyncDSRStrategy
from fides.api.service.async_dsr.utils import AsyncPhase, get_async_phase
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestOverrideFactory,
    SaaSRequestType,
)
from fides.api.util.collection_util import Row
from fides.api.util.saas_util import map_param_values
from fides.config import CONFIG

if TYPE_CHECKING:
    from fides.api.models.privacy_request.privacy_request import PrivacyRequest
    from fides.api.service.connectors.query_configs.saas_query_config import (
        SaaSQueryConfig,
    )


class AsyncPollingStrategy(AsyncDSRStrategy):
    """
    Enhanced strategy for polling async DSR requests.
    Works for both access and erasure operations with internal phase-based organization.
    """

    type = AsyncTaskType.polling
    configuration_model = AsyncPollingConfiguration

    def __init__(self, session: Session, configuration: AsyncPollingConfiguration):
        self.session = session
        self.status_request = configuration.status_request
        self.result_request = configuration.result_request

    def async_retrieve_data(
        self,
        client: AuthenticatedClient,
        request_task_id: str,
        query_config: "SaaSQueryConfig",
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """
        Execute async retrieve data with internal phase routing.
        """
        request_task = self._get_request_task(request_task_id)
        async_phase = get_async_phase(request_task, query_config)

        if async_phase == AsyncPhase.initial_async:
            return self._initial_request_access(
                client, request_task, query_config, input_data
            )

        if async_phase == AsyncPhase.polling_continuation:
            return self._polling_continuation_access(client, request_task, query_config)

        logger.warning(
            f"Unexpected async phase '{async_phase}' for polling access task {request_task.id}"
        )
        return []

    def async_mask_data(
        self,
        client: AuthenticatedClient,
        request_task_id: str,
        query_config: "SaaSQueryConfig",
        rows: List[Row],
    ) -> int:
        """
        Execute async mask data with internal phase routing.
        """
        request_task = self._get_request_task(request_task_id)
        async_phase = get_async_phase(request_task, query_config)

        if async_phase == AsyncPhase.initial_async:
            return self._initial_request_erasure(
                client, request_task, query_config, rows
            )

        if async_phase == AsyncPhase.polling_continuation:
            return self._polling_continuation_erasure(
                client, request_task, query_config
            )

        logger.warning(
            f"Unexpected async phase '{async_phase}' for polling erasure task {request_task.id}"
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

    def _initial_request_access(
        self,
        client: AuthenticatedClient,
        request_task: RequestTask,
        query_config: "SaaSQueryConfig",
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Handle initial setup for access polling requests."""
        logger.info(f"Initial polling request for access task {request_task.id}")

        policy = request_task.privacy_request.policy

        async_requests_to_process = [
            req
            for req in query_config.get_read_requests_by_identity()
            if req.async_config
        ]

        if not async_requests_to_process:
            logger.warning(
                f"No async-configured read requests found for task {request_task.id}"
            )
            return []

        request_task.async_type = AsyncTaskType.polling
        self.session.add(request_task)
        self.session.commit()

        for read_request in async_requests_to_process:
            logger.info(
                f"Creating initial polling sub-requests for task {request_task.id}"
            )
            self._handle_polling_initial_request(
                request_task,
                query_config,
                read_request,
                input_data,
                policy,
                client,
            )

        self.session.refresh(request_task)
        raise AwaitingAsyncProcessing(
            f"Waiting for next scheduled check of {request_task.dataset_name} access results."
        )

    def _initial_request_erasure(
        self,
        client: AuthenticatedClient,
        request_task: RequestTask,
        query_config: "SaaSQueryConfig",
        rows: List[Row],
    ) -> int:
        """Handle initial setup for erasure polling requests."""
        logger.info(f"Initial polling request for erasure task {request_task.id}")

        privacy_request = request_task.privacy_request
        policy = privacy_request.policy

        all_requests = []
        masking_request = query_config.get_masking_request()
        if masking_request:
            all_requests.append(masking_request)

        # Set async type once for the task
        request_task.async_type = AsyncTaskType.polling
        self.session.add(request_task)
        self.session.commit()

        for request in all_requests:
            if not (request.async_config and request_task.id):
                continue

            if request.path:
                logger.info(
                    f"Executing initial masking request for polling task {request_task.id}"
                )
                self._handle_polling_initial_erasure_request(
                    request_task,
                    query_config,
                    request,
                    rows,
                    policy,
                    privacy_request,
                    client,
                )

        # After processing all requests, raise AwaitingAsyncProcessing (like access flow)
        # But only if we actually created any sub-requests
        self.session.refresh(request_task)
        if request_task.sub_requests:
            raise AwaitingAsyncProcessing(
                f"Waiting for next scheduled check of {request_task.dataset_name} erasure results."
            )
        # If no sub-requests were created (no rows to process), the task is already complete
        return 0

    def _polling_continuation_access(
        self,
        client: AuthenticatedClient,
        request_task: RequestTask,
        query_config: "SaaSQueryConfig",
    ) -> List[Row]:
        """Handle polling continuation for access requests."""
        logger.info(f"Continuing polling for access task {request_task.id}")

        polling_complete = self._execute_polling_requests(
            client, request_task, query_config
        )

        if not polling_complete:
            raise AwaitingAsyncProcessing(
                f"Waiting for next scheduled check of {request_task.dataset_name} access results."
            )

        return request_task.get_access_data()

    def _polling_continuation_erasure(
        self,
        client: AuthenticatedClient,
        request_task: RequestTask,
        query_config: "SaaSQueryConfig",
    ) -> int:
        """Handle polling continuation for erasure requests."""
        logger.info(f"Continuing polling for erasure task {request_task.id}")

        polling_complete = self._execute_polling_requests(
            client, request_task, query_config
        )

        if not polling_complete:
            raise AwaitingAsyncProcessing(
                f"Waiting for next scheduled check of {request_task.dataset_name} erasure results."
            )

        return request_task.rows_masked or 0

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
        """Handles the setup for asynchronous initial requests."""
        query_config.action = "Polling - start"
        prepared_requests: List[Tuple[SaaSRequestParams, Dict[str, Any]]] = (
            query_config.generate_requests(input_data, policy, read_request)
        )
        logger.info(f"Prepared requests: {len(prepared_requests)}")

        for next_request, param_value_map in prepared_requests:
            logger.info(f"Executing initial request: {next_request}")
            response = client.send(next_request)

            if not response.ok:
                raise FidesopsException(
                    f"Initial async request failed with status code {response.status_code}: {response.text}"
                )

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
            self._save_sub_request_data(request_task, param_value_map)

    def _handle_polling_initial_erasure_request(
        self,
        request_task: RequestTask,
        query_config: "SaaSQueryConfig",
        request: SaaSRequest,
        rows: List[Row],
        policy: Policy,
        privacy_request: "PrivacyRequest",
        client: "AuthenticatedClient",
    ) -> None:
        """Handles the setup for asynchronous initial erasure requests."""
        logger.info(
            f"Processing {len(rows)} rows for erasure request in task {request_task.id}"
        )

        # Create sub-requests for erasure operations (similar to access operations)
        for row in rows or [{}]:
            try:
                # Generate parameter values first (like access requests)
                param_value_map = query_config.generate_update_param_values(
                    row, policy, privacy_request, request
                )

                # Generate the update request using the param_values
                prepared_request = query_config.generate_update_stmt(
                    row, policy, privacy_request
                )
                response = client.send(prepared_request, request.ignore_errors)

                # Extract correlation ID from response (required, like access requests)
                try:
                    response_data = response.json()
                    correlation_id = pydash.get(
                        response_data, request.correlation_id_path
                    )
                    if not correlation_id:
                        raise FidesopsException(
                            f"Could not extract correlation ID from response using path: {request.correlation_id_path}"
                        )
                except ValueError as exc:
                    raise FidesopsException(
                        f"Invalid JSON response from initial erasure request: {exc}"
                    )

                # Add correlation_id to the existing param_value_map (like access requests)
                param_value_map["correlation_id"] = str(correlation_id)
                self._save_sub_request_data(request_task, param_value_map)

            except ValueError as exc:
                if request.skip_missing_param_values:
                    logger.debug("Skipping optional masking request: {}", exc)
                    continue
                raise exc

    def _save_sub_request_data(
        self,
        request_task: RequestTask,
        param_values_map: Dict[str, Any],
    ) -> None:
        """Saves the request data for future use in the request task on async requests."""
        sub_request = RequestTaskSubRequest.create(
            self.session,
            data={
                "request_task_id": request_task.id,
                "param_values": param_values_map,
                "status": "pending",
            },
        )
        logger.info(
            f"Created sub-request {sub_request.id} for task '{request_task.id}'"
        )

    def _get_requests_for_action(
        self, polling_task: RequestTask, query_config: "SaaSQueryConfig"
    ) -> List[ReadSaaSRequest]:
        """
        Get the appropriate requests based on the action type.

        Args:
            polling_task: The polling task to get requests for
            query_config: The SaaS query configuration

        Returns:
            List of ReadSaaSRequest objects for the given action type

        Raises:
            PrivacyRequestError: If action type is unsupported or masking request not found
        """
        # Validate result_request is provided for access operations
        if polling_task.action_type == ActionType.access and not self.result_request:
            raise PrivacyRequestError(
                f"result_request is required for access operations but was not provided in polling configuration for task {polling_task.id}"
            )

        if polling_task.action_type == ActionType.access:
            return list(query_config.get_read_requests_by_identity())
        if polling_task.action_type == ActionType.erasure:
            masking_request = query_config.get_masking_request()
            if not masking_request:
                raise PrivacyRequestError(
                    f"No masking request found for erasure task {polling_task.id}"
                )
            return [cast(ReadSaaSRequest, masking_request)]
        raise PrivacyRequestError(
            f"Unsupported action type: {polling_task.action_type}"
        )

    def _check_sub_request_status(
        self, client: AuthenticatedClient, param_values: Dict[str, Any]
    ) -> bool:
        """
        Check the status of a sub-request using either override function or HTTP request.

        Args:
            client: The authenticated client
            param_values: The parameter values for the request

        Returns:
            bool: True if the request is complete, False if still in progress

        Raises:
            PrivacyRequestError: If status_path is required but not provided
        """
        # Create polling handler
        polling_handler = PollingRequestHandler(
            self.status_request, self.result_request
        )

        # Check for status override vs standard HTTP request
        if self.status_request.request_override:
            # Handle status override function directly
            override_function = SaaSRequestOverrideFactory.get_override(
                self.status_request.request_override,
                SaaSRequestType.POLLING_STATUS,
            )

            # Override functions return boolean status directly
            return cast(
                bool,
                override_function(
                    client=client,
                    param_values=param_values,
                    request_config=self.status_request,
                    secrets=client.configuration.secrets,
                ),
            )

        # Standard HTTP status request
        response = polling_handler.get_status_response(client, param_values)

        # Process status response
        status_path = self.status_request.status_path

        if status_path is None:
            raise PrivacyRequestError(
                "status_path is required when request_override is not provided"
            )

        return PollingResponseProcessor.evaluate_status_response(
            response,
            status_path,
            self.status_request.status_completed_value,
        )

    def _process_completed_sub_request(
        self,
        client: AuthenticatedClient,
        param_values: Dict[str, Any],
        sub_request: RequestTaskSubRequest,
        polling_task: RequestTask,
    ) -> None:
        """
        Process a completed sub-request by getting results and handling them appropriately.

        Args:
            client: The authenticated client
            param_values: The parameter values for the request
            sub_request: The completed sub-request
            polling_task: The parent polling task

        Raises:
            PrivacyRequestError: If polling result is not the expected type
        """
        # Handle erasure operations differently - they don't need result_request
        if polling_task.action_type == ActionType.erasure:
            # For erasure operations, just mark as complete and handle the result
            sub_request.update_status(self.session, ExecutionLogStatus.complete.value)
            self._handle_erasure_result(polling_task)
            logger.info(
                f"Sub-request {sub_request.id} for {polling_task.action_type} task {polling_task.id} completed"
            )
            return

        # For access operations, we need result_request to get the data
        if not self.result_request:
            raise PrivacyRequestError(
                f"result_request is required for processing completed sub-request {sub_request.id} but was not provided"
            )

        if self.result_request.request_override:
            # Handle override function directly
            override_function = SaaSRequestOverrideFactory.get_override(
                self.result_request.request_override,
                SaaSRequestType.POLLING_RESULT,
            )

            polling_result = override_function(
                client=client,
                param_values=param_values,
                request_config=self.result_request,
                secrets=client.configuration.secrets,
            )
        else:
            # Standard HTTP request processing
            polling_handler = PollingRequestHandler(
                self.status_request, self.result_request
            )
            response = polling_handler.get_result_response(client, param_values)

            # We need to reconstruct the request path for processing
            prepared_result_request = map_param_values(
                "result",
                "polling request",
                self.result_request,
                param_values,
            )

            polling_result = PollingResponseProcessor.process_result_response(
                prepared_result_request.path,
                response,
                self.result_request.result_path,
            )

        # Ensure we have the expected polling result type
        if not isinstance(polling_result, PollingResult):
            raise PrivacyRequestError("Polling result must be PollingResult instance")

        # Handle results for access operations
        self._handle_access_result(polling_result, polling_task)

        # Mark as complete using existing method
        sub_request.update_status(self.session, ExecutionLogStatus.complete.value)

        logger.info(
            f"Sub-request {sub_request.id} for task {polling_task.id} completed successfully"
        )

    def _check_polling_completion(self, polling_task: RequestTask) -> bool:
        """
        Check if all sub-requests for a polling task are complete.

        Args:
            polling_task: The polling task to check

        Returns:
            bool: True if all sub-requests are complete, False if still in progress
        """
        # Get all sub-requests and categorize by status
        all_sub_requests = polling_task.sub_requests.all()
        completed_sub_requests = [
            sub_request
            for sub_request in all_sub_requests
            if sub_request.status == "complete"
        ]
        failed_sub_requests = [
            sub_request
            for sub_request in all_sub_requests
            if sub_request.status == "error"
        ]

        if (
            len(completed_sub_requests) == len(all_sub_requests)
            and len(all_sub_requests) > 0
        ):
            # All sub-requests completed successfully - aggregate results
            logger.info(
                f"All sub-requests completed successfully for task {polling_task.id}"
            )
            return True

        # Still polling - some sub-requests are pending
        logger.info(
            f"Polling task {polling_task.id}: {len(completed_sub_requests)}/{len(all_sub_requests)} sub-requests complete, {len(failed_sub_requests)} failed"
        )
        return False

    def _process_sub_requests_for_request(
        self,
        client: AuthenticatedClient,
        request: ReadSaaSRequest,
        polling_task: RequestTask,
    ) -> None:
        """
        Process all sub-requests for a given request.

        Args:
            client: The authenticated client
            request: The SaaS request being processed
            polling_task: The parent polling task
        """
        sub_requests: List[RequestTaskSubRequest] = polling_task.sub_requests.all()

        for sub_request in sub_requests:
            # Skip already completed sub-requests
            if sub_request.status == "complete":
                continue

            param_values = sub_request.param_values

            try:
                # Check status of the sub-request
                status = self._check_sub_request_status(client, param_values)

                if status:
                    self._process_completed_sub_request(
                        client, param_values, sub_request, polling_task
                    )
                else:
                    logger.debug(
                        f"Sub-request {sub_request.id} for task {polling_task.id} still not ready"
                    )

            except Exception as exc:
                logger.error(
                    f"Error processing sub-request {sub_request.id} for task {polling_task.id}: {exc}"
                )
                sub_request.update_status(self.session, "error")
                raise exc

    def _execute_polling_requests(
        self,
        client: AuthenticatedClient,
        polling_task: RequestTask,
        query_config: "SaaSQueryConfig",
    ) -> bool:
        """
        Internal polling execution orchestrator with proper error handling and timeout management.

        Stores results on individual sub-requests and only aggregates when ALL are successful.
        Implements timeout checking and raises exceptions for errors and timeouts.

        Returns:
            bool: True if all polling is complete (success or failure), False if still in progress
        """
        # Check for timeout before processing requests
        self._check_polling_timeout(polling_task)

        # Get appropriate requests based on action type
        requests = self._get_requests_for_action(polling_task, query_config)

        # Process each request and its sub-requests
        for request in requests:
            if request.async_config:
                self._process_sub_requests_for_request(client, request, polling_task)

        # Check final status and return completion status
        return self._check_polling_completion(polling_task)

    def _handle_access_result(
        self, polling_result: PollingResult, request_task: RequestTask
    ) -> None:
        """Handle result for access requests."""
        if polling_result.result_type == "rows":
            existing_access_data = request_task.access_data or []
            if isinstance(polling_result.data, list):
                existing_access_data.extend(polling_result.data)
            else:
                existing_access_data.append(polling_result.data)
            request_task.access_data = existing_access_data

            # For structured data results, use the same data for erasures
            request_task.data_for_erasures = existing_access_data
            request_task.save(self.session)

        elif polling_result.result_type == "attachment":
            try:
                attachment_bytes = self._ensure_attachment_bytes(polling_result.data)
                attachment_id = self._store_polling_attachment(
                    request_task,
                    attachment_data=attachment_bytes,
                    filename=polling_result.metadata.get(
                        "filename", f"attachment_{str(uuid4())[:8]}"
                    ),
                )
                _add_attachment_metadata_to_rows(
                    self.session, attachment_id, request_task.access_data or []
                )

                # For attachment results, we need to provide data for erasures
                # This follows the same pattern as SaaSConnector.retrieve_data
                # which returns [{}] when there's a delete request but no read request
                request_task.data_for_erasures = [{}]
                request_task.save(self.session)
            except Exception as exc:
                raise PrivacyRequestError(f"Attachment storage failed: {exc}")
        else:
            raise PrivacyRequestError(
                f"Unsupported result type: {polling_result.result_type}"
            )

    def _handle_erasure_result(self, request_task: RequestTask) -> None:
        """Handle result for erasure requests."""
        # For erasure operations, just increment the rows_masked counter
        request_task.rows_masked = (request_task.rows_masked or 0) + 1
        request_task.save(self.session)
        logger.info(
            f"Erasure task {request_task.id} completed - rows_masked: {request_task.rows_masked}"
        )

    # Private helper functions

    @staticmethod
    def _ensure_attachment_bytes(data: Union[List[Row], bytes]) -> bytes:
        """Ensure attachment polling results provide bytes content."""
        if isinstance(data, bytes):
            return data
        raise PrivacyRequestError("Expected bytes data for attachment polling result")

    def _check_polling_timeout(self, polling_task: RequestTask) -> None:
        """
        Check if any sub-requests have exceeded the polling timeout.

        Raises:
            PrivacyRequestError: If any sub-request has timed out
        """

        timeout_days = CONFIG.execution.async_polling_request_timeout_days
        timeout_seconds = timeout_days * 24 * 60 * 60  # Convert days to seconds

        # Check timeout for incomplete sub-requests only
        timed_out_sub_requests = []

        for sub_request in polling_task.sub_requests:
            if sub_request.status != ExecutionLogStatus.complete.value:
                # Check if this sub-request has timed out
                if sub_request.created_at:
                    timeout_threshold = sub_request.created_at + timedelta(
                        seconds=timeout_seconds
                    )
                    current_time = datetime.now(timezone.utc)
                    if current_time > timeout_threshold:
                        timed_out_sub_requests.append(sub_request)

        if timed_out_sub_requests:
            sub_request_ids = [sr.id for sr in timed_out_sub_requests]
            raise PrivacyRequestError(
                f"Polling timeout exceeded for sub-requests {sub_request_ids} "
                f"in task {polling_task.id}. Timeout interval: {timeout_days} days"
            )


def _add_attachment_metadata_to_rows(
    db: Session, attachment_id: str, rows: List[Row]
) -> None:
    """Add attachment metadata to rows collection (like manual tasks do)."""
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
