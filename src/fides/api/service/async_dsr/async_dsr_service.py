from io import BytesIO
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
    AttachmentType,
)
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.privacy_request.request_task import RequestTaskSubRequest
from fides.api.models.storage import get_active_default_storage_config
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.schemas.saas.async_polling_configuration import PollingResult
from fides.api.schemas.saas.saas_config import ReadSaaSRequest
from fides.api.service.async_dsr.async_dsr_strategy_factory import (
    get_strategy as get_async_strategy,
)
from fides.api.service.async_dsr.async_dsr_strategy_polling import (
    PollingAsyncDSRStrategy,
)
from fides.api.service.connectors.query_configs.saas_query_config import SaaSQueryConfig
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.connectors.saas_connector import SaaSConnector
from fides.api.task.execute_request_tasks import (
    create_graph_task,
    log_task_queued,
    queue_request_task,
)
from fides.api.task.graph_task import GraphTask
from fides.api.task.task_resources import TaskResources
from fides.api.tasks import DatabaseTask, celery_app
from fides.api.util.collection_util import Row
from fides.api.util.logger_context_utils import LoggerContextKeys, log_context
from fides.api.util.memory_watchdog import memory_limiter


@celery_app.task(base=DatabaseTask, bind=True)
@memory_limiter
@log_context(
    capture_args={
        "privacy_request_id": LoggerContextKeys.privacy_request_id,
        "polling_task_id": LoggerContextKeys.task_id,
    }
)
def execute_polling_task(
    self: DatabaseTask,
    polling_task_id: str,
) -> None:
    """Executes a polling request task from the status onward"""
    with self.get_new_session() as db:
        polling_task: Optional[RequestTask] = RequestTask.get(
            db, object_id=polling_task_id
        )
        if not polling_task:
            raise PrivacyRequestError(
                f"RequestTask with ID {polling_task_id} not found"
            )

        privacy_request: PrivacyRequest = polling_task.privacy_request
        # Check that the privacy request is in requires_input. Setting that status to avoid erroring out in requeue_interrupted_tasks
        if privacy_request.status != PrivacyRequestStatus.in_processing:
            polling_task.status = ExecutionLogStatus.error
            polling_task.save(db)
            raise PrivacyRequestError(
                f"Cannot execute polling task {polling_task.id} for privacy request {privacy_request.id} with status {privacy_request.status.value}"
            )

        connection_config = get_connection_config_from_task(db, polling_task)

        with TaskResources(
            privacy_request,
            privacy_request.policy,
            [connection_config],
            polling_task,
            db,
        ) as resources:
            graph_task: GraphTask = create_graph_task(db, polling_task, resources)

            saas_connector: SaaSConnector = graph_task.connector  # type: ignore
            saas_connector.set_privacy_request_state(
                privacy_request,
                graph_task.execution_node,
                polling_task,
            )
            query_config: SaaSQueryConfig = saas_connector.query_config(
                graph_task.execution_node
            )  # type: ignore

            if polling_task.action_type == ActionType.access:
                logger.info(f"Executing read polling requests for {polling_task.id}")

                execute_read_polling_requests(
                    db, polling_task, query_config, saas_connector
                )
            elif polling_task.action_type == ActionType.erasure:
                execute_erasure_polling_requests(db, polling_task, query_config)


# Could move to RequestTask class
def get_connection_config_from_task(
    db: Session, request_task: RequestTask
) -> ConnectionConfig:
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


def execute_read_polling_requests(
    db: Session,
    polling_task: RequestTask,
    query_config: SaaSQueryConfig,
    connector: SaaSConnector,
) -> None:
    """Execute the read polling requests for a given privacy request"""
    read_requests: List[ReadSaaSRequest] = query_config.get_read_requests_by_identity()
    rows: List[Row] = []
    pending_requests = False
    for read_request in read_requests:
        if read_request.async_config:

            strategy: PollingAsyncDSRStrategy = get_async_strategy(  # type: ignore
                read_request.async_config.strategy,
                read_request.async_config.configuration,
            )
            client: AuthenticatedClient = connector.create_client()
            sub_requests: List[RequestTaskSubRequest] = polling_task.sub_requests.all()
            for sub_request in sub_requests:
                if sub_request.sub_request_status == ExecutionLogStatus.complete.value:
                    logger.info(
                        f"Polling sub request - {sub_request.id} for task {polling_task.id} already completed. "
                    )
                    continue
                param_values = sub_request.param_values

                status = strategy.get_status_request(
                    client, param_values, connector.secrets
                )
                if status:
                    sub_request.update_status(db, ExecutionLogStatus.complete.value)
                    polling_result = execute_result_request(
                        strategy,
                        client,
                        param_values,
                        connector.secrets,
                    )

                    # Handle different result types
                    if polling_result.result_type == "rows":
                        # Structured data - add to rows collection
                        if isinstance(polling_result.data, list):
                            rows.extend(polling_result.data)
                        else:
                            logger.warning(
                                f"Expected list for rows result, got {type(polling_result.data)}"
                            )

                    elif polling_result.result_type == "attachment":
                        # File attachment - store and link to request task
                        try:
                            attachment_id = store_polling_attachment(
                                db=db,
                                file_content=polling_result.data,
                                metadata=polling_result.metadata,
                                request_task=polling_task,
                                privacy_request=polling_task.privacy_request,
                            )
                            logger.info(
                                f"Stored attachment {attachment_id} for task {polling_task.id}"
                            )

                            # Add attachment metadata to collection data (like manual tasks do)
                            # This ensures the DSR builder can find and process the attachment
                            attachment_record = (
                                db.query(Attachment)
                                .filter(Attachment.id == attachment_id)
                                .first()
                            )
                            if attachment_record:
                                # Try to enrich with size & URL
                                try:
                                    size, url = attachment_record.retrieve_attachment()
                                    attachment_info = {
                                        "file_name": attachment_record.file_name,
                                        "download_url": str(url) if url else None,
                                        "file_size": size,
                                    }
                                except Exception as exc:  # pylint: disable=broad-except
                                    logger.warning(
                                        f"Could not retrieve attachment content for {attachment_record.file_name}: {exc}"
                                    )
                                    attachment_info = {
                                        "file_name": attachment_record.file_name,
                                        "download_url": None,
                                        "file_size": None,
                                    }

                                # Add attachment to the polling results - mirror manual task format
                                # Use "attachments" as the field name to match DSR builder expectations
                                attachments_item = None
                                for item in rows:
                                    if isinstance(item, dict) and "attachments" in item:
                                        attachments_item = item
                                        break

                                if attachments_item is None:
                                    # Create new attachments item
                                    attachments_item = {"attachments": []}
                                    rows.append(attachments_item)

                                # Add attachment to the list
                                attachments_item["attachments"].append(attachment_info)
                                logger.info(
                                    f"Added attachment {attachment_record.file_name} to attachments"
                                )
                        except Exception as e:
                            logger.error(
                                f"Failed to store attachment for task {polling_task.id}: {e}"
                            )
                            raise PrivacyRequestError(f"Attachment storage failed: {e}")

                    else:
                        raise PrivacyRequestError(
                            f"Unsupported result type: {polling_result.result_type}"
                        )
                else:
                    logger.info(
                        f"Polling sub request - {sub_request.id}  for task {polling_task.id} still not Ready. "
                    )
                    pending_requests = True
                    continue

    if pending_requests:
        # Save results for future polling
        save_polling_task_data(db, polling_task, rows)
        logger.info(f"Polling task {polling_task.id} still has pending requests.")
        return

    # Task is complete - save final results and mark complete
    save_polling_task_data(db, polling_task, rows)
    polling_task.update_status(db, ExecutionLogStatus.complete)
    log_task_queued(polling_task, "polling success")
    queue_request_task(polling_task, privacy_request_proceed=True)


def save_polling_task_data(
    db: Session, polling_task: RequestTask, rows: List[Row]
) -> None:
    """Save the polling task data"""
    rows.extend(polling_task.access_data)
    polling_task.access_data = rows
    polling_task.save(db)


def execute_result_request(
    strategy: PollingAsyncDSRStrategy,
    client: AuthenticatedClient,
    param_values: Dict[str, Any],
    secrets: Dict[str, Any],
) -> PollingResult:
    """Execute the result request of a successful polling task"""
    result = strategy.get_result_request(client, param_values, secrets)
    logger.info(
        f"Polling result type: {result.result_type}, metadata: {result.metadata}"
    )
    return result


def execute_erasure_polling_requests(
    polling_task: RequestTask,
) -> None:
    """Execute the erasure polling requests for a given privacy request"""
    # TODO: Implement erasure polling logic. Or consider if we can generalize polling for all tasks
    logger.info(f"Erasure polling not yet implemented. Task {polling_task.id} passed")


def store_polling_attachment(
    db: Session,
    file_content: bytes,
    metadata: Dict[str, Any],
    request_task: RequestTask,
    privacy_request: PrivacyRequest,
) -> str:
    """
    Store attachment file and create database records linking to RequestTask.
    Returns the attachment ID.
    """

    # Extract metadata
    filename = metadata.get("filename", f"polling_result_{request_task.id}")

    # Get default storage config (you might want to make this configurable)
    storage_config = get_active_default_storage_config(db)
    if not storage_config:
        raise PrivacyRequestError("No default storage configuration found")

    # Create file-like object from bytes
    file_obj = BytesIO(file_content)

    try:
        # Create attachment record with upload
        attachment = Attachment.create_and_upload(
            db=db,
            data={
                "file_name": filename,
                "attachment_type": AttachmentType.include_with_access_package,
                "storage_key": storage_config.key,
                "user_id": None,  # System-generated attachment
            },
            attachment_file=file_obj,
        )

        AttachmentReference.create(
            db=db,
            data={
                "attachment_id": attachment.id,
                "reference_id": privacy_request.id,
                "reference_type": AttachmentReferenceType.privacy_request,
            },
        )

        AttachmentReference.create(
            db=db,
            data={
                "attachment_id": attachment.id,
                "reference_id": request_task.id,  # Reference the request task, not privacy request
                "reference_type": AttachmentReferenceType.request_task,
            },
        )

        logger.info(
            f"Successfully stored polling attachment {attachment.id} for request_task {request_task.id}"
        )
        return attachment.id

    except Exception as e:
        logger.error(f"Failed to store polling attachment: {e}")
        raise PrivacyRequestError(f"Failed to store polling attachment: {e}")
