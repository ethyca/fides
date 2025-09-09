from typing import Any, Dict, Optional

from fides.api.tasks import DatabaseTask, celery_app
from fides.api.util.logger_context_utils import LoggerContextKeys, log_context
from fides.api.util.memory_watchdog import memory_limiter
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.async_dsr.async_dsr_strategy import AsyncDSRStrategy
from fides.api.service.async_dsr.async_dsr_strategy_polling_base import PollingAsyncDSRBaseStrategy
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
    privacy_request_id: str,
    polling_task_id: str,
) -> None:
    """Executes a polling request task from the status onward"""
    with self.get_new_session() as db:
        polling_task: RequestTask = RequestTask.get(db, object_id=polling_task_id)
        privacy_request: PrivacyRequest = polling_task.privacy_request
        # Check that the privacy request is in processing
        if  privacy_request.status != PrivacyRequestStatus.in_processing:
            polling_task.status = ExecutionLogStatus.error
            polling_task.save(db)
            raise PrivacyRequestError(
                f"Cannot execute Polling Task {polling_task.id} for privacy request {privacy_request.id} with status {privacy_request.status.value}"
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

                execute_read_polling_requests(db, polling_task, query_config, saas_connector)
            elif polling_task.action_type == ActionType.erasure:
                execute_erasure_polling_requests(db, polling_task, query_config)


## Could move to Request Task Class
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
    read_requests = query_config.get_read_requests_by_identity() #Check: Cant we get the request directly from the task?
    logger.info(f"Read requests: {read_requests}")
    for read_request in read_requests:
        if read_request.async_config:
            strategy: PollingAsyncDSRBaseStrategy = AsyncDSRStrategy.get_strategy(  # type: ignore
                read_request.async_config.strategy,
                read_request.async_config.configuration,
            )
            client: AuthenticatedClient = connector.create_client()

            # Get missing parameters from available context
            privacy_request: PrivacyRequest = polling_task.privacy_request
            secrets: Dict[str, Any] = connector.secrets

            identity_data = {
                **privacy_request.get_persisted_identity().labeled_dict(),
                **privacy_request.get_cached_identity_data(),
            }

            param_values = _prepare_param_values_for_polling(
                secrets,
                identity_data,
                polling_task,
            )

            logger.info(f"Param values: {param_values}")
            status = strategy.get_status_request(
                client,
                param_values
            )

            if status:
                execute_result_request(
                    db,
                    polling_task,
                    strategy,
                    client,
                    param_values
                )
            else:
                logger.info(f"Polling request - {polling_task.id} still not Ready. ")
                continue


def execute_result_request(
    db: Session,
    polling_task: RequestTask,
    strategy: PollingAsyncDSRBaseStrategy,
    client: AuthenticatedClient,
    param_values: Dict[str, Any],
) -> None:
    """Execute the result request of a successfull polling task"""
    result = strategy.get_result_request(
        client,
        param_values
    )
    logger.info(f"Result: {result}")
    if result:
        # Save updated data back to the request task.
        polling_task.access_data = result
        logger.info(
            f"Polling request - {polling_task.id} is ready. Added {len(result) if isinstance(result, list) else 1} results"
        )

    else:
        polling_task.access_data = []
        logger.info(
            f"Polling request - {polling_task.id} is ready but returned no results"
        )

    polling_task.callback_succeeded = (
        True  # Setting this task as successful, finished
    )
    polling_task.update_status(db, ExecutionLogStatus.pending)
    polling_task.save(db)
    log_task_queued(polling_task, "polling success")
    queue_request_task(polling_task, privacy_request_proceed=True)


def execute_erasure_polling_requests(
    db: Session,
    polling_task: RequestTask,
    query_config: SaaSQueryConfig,
) -> None:
    """Execute the erasure polling requests for a given privacy request"""
    # TODO: Implement erasure polling logic. Or consider if we can generalize polling for all tasks
    logger.info(f"Erasure polling not yet implemented. Task {polling_task.id} passed")


def _get_request_id_from_storage(
    request_task: RequestTask
) -> Optional[str]:
    """Helper method to get request_id from stored data or param_values."""
    # Try to get from stored request_data first
    if request_task and request_task.request_data:
        stored_data = request_task.request_data.request_data
        if stored_data and "request_id" in stored_data:
            return stored_data["request_id"]

    logger.error(f"Request ID not found in stored data")
    return None


def _prepare_param_values_for_polling(
    secrets: Dict[str, Any],
    identity_data: Dict[str, Any],
    request_task: RequestTask
) -> Dict[str, Any]:
    """Prepare parameter values including request_id from various sources."""
    param_values = secrets.copy()
    param_values.update(identity_data)

    param_values.update({"request_id": _get_request_id_from_storage(request_task)})

    return param_values
