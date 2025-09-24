"""
Pure utility functions for async DSR operations.

This module contains utility functions with no business logic dependencies.
These are helper functions that can be used across the async DSR system.
"""

from io import BytesIO

# Type checking imports
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import pydash
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import FidesopsException, PrivacyRequestError
from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
    AttachmentType,
)
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.privacy_request.request_task import (
    AsyncTaskType,
    RequestTaskSubRequest,
)
from fides.api.models.storage import get_active_default_storage_config
from fides.api.schemas.saas.async_polling_configuration import PollingResult
from fides.api.schemas.saas.saas_config import ReadSaaSRequest
from fides.api.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.util.collection_util import Row

if TYPE_CHECKING:
    from fides.api.service.async_dsr.strategies.async_dsr_strategy_polling import (
        PollingAsyncDSRStrategy,
    )
    from fides.api.service.connectors.query_configs.saas_query_config import (
        SaaSQueryConfig,
    )
    from fides.api.service.connectors.saas.authenticated_client import (
        AuthenticatedClient,
    )


def has_async_requests(query_config: "SaaSQueryConfig") -> bool:
    """Check if any read/delete requests have async configuration"""
    read_requests = query_config.get_read_requests_by_identity()

    # For masking requests, we need a session to get the masking request
    # Since this is a utility function, we'll just check read requests for async config
    # The masking request async config will be checked in the actual handlers
    all_requests = read_requests

    return any(request.async_config is not None for request in all_requests)


def is_polling_continuation(request_task: RequestTask) -> bool:
    """Check if this is a polling continuation (not initial request)"""
    async_type_check = request_task.async_type == AsyncTaskType.polling
    sub_requests_count = request_task.sub_requests.count()

    logger.warning(
        f"is_polling_continuation for task {request_task.id}: "
        f"async_type={request_task.async_type} (polling={async_type_check}), "
        f"sub_requests_count={sub_requests_count}"
    )

    return async_type_check and sub_requests_count > 0


def is_callback_completion(request_task: RequestTask) -> bool:
    """Check if this is a completed callback request"""
    return request_task.callback_succeeded


def is_async_request(request_task: RequestTask, query_config: "SaaSQueryConfig") -> bool:
    """
    Check if this is an async request (callback, continuation, or initial async).

    This is the main entry point for async detection.
    """
    return (
        is_callback_completion(request_task)
        or is_polling_continuation(request_task)
        or has_async_requests(query_config)
    )


def classify_async_type(request_task: RequestTask, query_config: "SaaSQueryConfig") -> str:
    """
    Classify the type of async request for routing purposes.

    Returns:
        - "callback_completion": Callback has completed
        - "polling_continuation": Continuing an existing polling process
        - "initial_async": Initial async request setup
        - "sync": Not an async request
    """
    if is_callback_completion(request_task):
        return "callback_completion"
    elif is_polling_continuation(request_task):
        return "polling_continuation"
    elif has_async_requests(query_config):
        return "initial_async"
    else:
        return "sync"


def get_connection_config_from_task(
    db: Session, request_task: RequestTask
) -> ConnectionConfig:
    """
    Get ConnectionConfig from a RequestTask.

    This utility function retrieves the connection configuration
    associated with a request task by looking up the dataset configuration.
    """
    dataset_config = DatasetConfig.filter(
        db=db,
        conditions=(DatasetConfig.fides_key == request_task.dataset_name),
    ).first()
    if not dataset_config:
        raise PrivacyRequestError(
            f"DatasetConfig with fides_key {request_task.dataset_name} not found."
        )

    connection_config = ConnectionConfig.get(
        db=db, object_id=dataset_config.connection_config_id
    )
    if not connection_config:
        raise PrivacyRequestError(
            f"ConnectionConfig with id {dataset_config.connection_config_id} not found."
        )

    return connection_config


def save_polling_results(
    db: Session,
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
        polling_task.save(db)
    elif affected_records is not None:
        # Erasure request - accumulate affected records count
        current_count = polling_task.rows_masked or 0
        polling_task.rows_masked = current_count + sum(affected_records)
        polling_task.save(db)


def execute_result_request(
    strategy: "PollingAsyncDSRStrategy",
    client: "AuthenticatedClient",
    param_values: dict,
    secrets: dict,
) -> PollingResult:
    """
    Execute a result request using the provided strategy.

    This utility function executes the result request and returns
    the polling result for further processing.
    """
    return strategy.get_result_request(client, param_values, secrets)


def store_polling_attachment(
    db: Session,
    request_task: RequestTask,
    privacy_request: PrivacyRequest,
    attachment_data: bytes,
    filename: str,
    content_type: str = "application/octet-stream",
) -> str:
    """
    Store polling attachment data and return attachment ID.

    This utility function handles the storage of attachment data
    from polling results and creates the necessary database records.
    """
    try:
        # Get active storage config
        storage_config = get_active_default_storage_config(db)
        if not storage_config:
            raise PrivacyRequestError("No active storage configuration found")

        # Create attachment record and upload to storage
        attachment = Attachment.create_and_upload(
            db=db,
            data={
                "file_name": filename,
                "attachment_type": AttachmentType.include_with_access_package,
                "storage_key": storage_config.key,
            },
            attachment_file=BytesIO(attachment_data),
        )

        # Create attachment references
        AttachmentReference.create(
            db=db,
            data={
                "attachment_id": attachment.id,
                "reference_id": request_task.id,
                "reference_type": AttachmentReferenceType.request_task,
            },
        )

        AttachmentReference.create(
            db=db,
            data={
                "attachment_id": attachment.id,
                "reference_id": privacy_request.id,
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


def handle_polling_initial_request(
    privacy_request: PrivacyRequest,
    request_task: RequestTask,
    query_config: "SaaSQueryConfig",
    strategy: "PollingAsyncDSRStrategy",
    read_request: ReadSaaSRequest,
    input_data: Dict[str, Any],
    policy: Policy,
    session: Session,
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
            correlation_id = pydash.get(response_data, read_request.correlation_id_path)
            if not correlation_id:
                raise FidesopsException(
                    f"Could not extract correlation ID from response using path: {read_request.correlation_id_path}"
                )
        except ValueError as e:
            raise FidesopsException(f"Invalid JSON response from initial request: {e}")

        param_value_map["correlation_id"] = str(correlation_id)
        # Use the provided session for sub-request creation
        logger.warning(f"About to create sub-request for task {request_task.id}")
        save_sub_request_data(session, request_task, param_value_map)
        logger.warning(f"Created sub-request for task {request_task.id}")

        # Verify it was created
        final_count = (
            session.query(RequestTaskSubRequest)
            .filter(RequestTaskSubRequest.request_task_id == request_task.id)
            .count()
        )
        logger.warning(
            f"Sub-request count after creation for task {request_task.id}: {final_count}"
        )


def save_sub_request_data(
    db: Session,
    request_task: RequestTask,
    param_values_map: Dict[str, Any],
) -> None:
    """
    Saves the request data for future use in the request task on async requests.
    """
    # Create new sub-request entry
    sub_request = RequestTaskSubRequest.create(
        db,
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
        db.query(RequestTaskSubRequest)
        .filter(RequestTaskSubRequest.request_task_id == request_task.id)
        .count()
    )
    logger.warning(
        f"Sub-request count after creation for task {request_task.id}: {count_after_create}"
    )
