from typing import Any, Dict, List, Optional, Union

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.models.privacy_request.request_task import RequestTaskSubRequest
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.schemas.saas.saas_config import ReadSaaSRequest
from fides.api.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.service.async_dsr.async_dsr_strategy_factory import (
    get_strategy as get_async_strategy,
)
from fides.api.service.async_dsr.async_dsr_strategy_polling_base import (
    PollingAsyncDSRBaseStrategy,
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
    privacy_request_id: str,
    polling_task_id: str,
) -> None:
    """Executes a polling request task from the status onward"""
    with self.get_new_session() as db:
        polling_task: Optional[RequestTask] = RequestTask.get(
            db, object_id=polling_task_id
        )
        if not polling_task:
            raise PrivacyRequestError(
                f"RequestTask with id {polling_task_id} not found"
            )

        privacy_request: PrivacyRequest = polling_task.privacy_request
        # Check that the privacy request is in requires_input. Setting that status to avoid erroring out in requeue_interrupted_tasks
        if privacy_request.status != PrivacyRequestStatus.requires_input:
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

                execute_read_polling_requests(
                    db, polling_task, query_config, saas_connector
                )
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
    read_requests: List[ReadSaaSRequest] = query_config.get_read_requests_by_identity()
    rows: List[Row] = []
    pending_requests = False
    for read_request in read_requests:
        if read_request.async_config:

            strategy: PollingAsyncDSRBaseStrategy = get_async_strategy(  # type: ignore
                read_request.async_config.strategy,
                read_request.async_config.configuration,
            )
            client: AuthenticatedClient = connector.create_client()
            sub_requests: List[RequestTaskSubRequest] = polling_task.sub_requests.all()
            for sub_request in sub_requests:
                if sub_request.sub_request_status == ExecutionLogStatus.complete:
                    logger.info(
                        f"Polling sub request - {sub_request.id}  for task {polling_task.id} already completed. "
                    )
                    continue
                param_values = sub_request.param_values

                status = strategy.get_status_request(client, param_values)
                if status:
                    sub_request.update_status(db, ExecutionLogStatus.complete)
                    result = execute_result_request(
                        db, polling_task, strategy, client, param_values
                    )
                    if isinstance(result, list[Row]):
                        rows.extend(result)
                    elif isinstance(result, str):
                        raise PrivacyRequestError(f"Link Support not yet implemented")
                    elif isinstance(result, bytes):
                        raise PrivacyRequestError(f"File Support not yet implemented")
                    else:
                        raise PrivacyRequestError(
                            f"Unsupported result type: {type(result)}"
                        )
                else:
                    logger.info(
                        f"Polling sub request - {sub_request.id}  for task {polling_task.id} still not Ready. "
                    )
                    pending_requests = True
                    continue

    if pending_requests:
        # Save results for future polling
        polling_task.access_data = rows.extend(polling_task.access_data)
        polling_task.save(db)
        logger.info(f"Polling task - {polling_task.id} still has pending requests. ")
        return

    polling_task.access_data = rows.extend(polling_task.access_data)
    polling_task.update_status(db, ExecutionLogStatus.complete)
    polling_task.save(db)
    log_task_queued(polling_task, "polling success")
    queue_request_task(polling_task, privacy_request_proceed=True)


def execute_result_request(
    db: Session,
    polling_task: RequestTask,
    strategy: PollingAsyncDSRBaseStrategy,
    client: AuthenticatedClient,
    param_values: Dict[str, Any],
) -> Union[List[Row], str, bytes]:
    """Execute the result request of a successfull polling task"""
    result = strategy.get_result_request(client, param_values)
    logger.info(f"Result: {result}")
    return result


def execute_erasure_polling_requests(
    db: Session,
    polling_task: RequestTask,
    query_config: SaaSQueryConfig,
) -> None:
    """Execute the erasure polling requests for a given privacy request"""
    # TODO: Implement erasure polling logic. Or consider if we can generalize polling for all tasks
    logger.info(f"Erasure polling not yet implemented. Task {polling_task.id} passed")
