from typing import Any, Dict

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


def requeue_polling_request(
    db: Session,
    async_task: RequestTask,
) -> None:
    """Re-queue a Privacy request that polls async tasks for a given privacy request"""
    # Check that the privacy request is approved or in processing
    privacy_request: PrivacyRequest = async_task.privacy_request
    logger.info(
        f"Privacy request {privacy_request.id} status: {privacy_request.status.value}"
    )

    if privacy_request.status not in [
        PrivacyRequestStatus.approved,
        PrivacyRequestStatus.in_processing,
    ]:
        raise PrivacyRequestError(
            f"Cannot re-queue privacy request {privacy_request.id} with status {privacy_request.status.value}"
        )

    logger.info(
        "Polling starting for {} task {} {}",
        async_task.action_type,
        async_task.collection_address,
        async_task.id,
    )

    connection_config = get_connection_config_from_task(db, async_task)

    with TaskResources(
        privacy_request,
        privacy_request.policy,
        [connection_config],
        async_task,
        db,
    ) as resources:
        graph_task: GraphTask = create_graph_task(db, async_task, resources)

        saas_connector: SaaSConnector = graph_task.connector  # type: ignore
        saas_connector.set_privacy_request_state(
            privacy_request,
            graph_task.execution_node,
            async_task,
        )
        query_config: SaaSQueryConfig = saas_connector.query_config(
            graph_task.execution_node
        )  # type: ignore
        if async_task.action_type == ActionType.access:
            logger.info(f"Executing read polling requests for {async_task.id}")

            execute_read_polling_requests(db, async_task, query_config, saas_connector)
        elif async_task.action_type == ActionType.erasure:
            execute_erasure_polling_requests(db, async_task, query_config)


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
    async_task: RequestTask,
    query_config: SaaSQueryConfig,
    connector: SaaSConnector,
) -> None:
    """Execute the read polling requests for a given privacy request"""
    read_requests = query_config.get_read_requests_by_identity()
    logger.info(f"Read requests: {read_requests}")
    for read_request in read_requests:
        if read_request.async_config:
            strategy: PollingAsyncDSRStrategy = AsyncDSRStrategy.get_strategy(  # type: ignore
                read_request.async_config.strategy,
                read_request.async_config.configuration,
            )
            client: AuthenticatedClient = connector.create_client()

            # Get missing parameters from available context
            privacy_request: PrivacyRequest = async_task.privacy_request
            secrets: Dict[str, Any] = connector.secrets
            identity_data = {
                **privacy_request.get_persisted_identity().labeled_dict(),
                **privacy_request.get_cached_identity_data(),
            }

            status = strategy.get_status_request(
                client,
                secrets,
                identity_data,
            )

            if status:
                execute_read_result_request(
                    db,
                    async_task,
                    strategy,
                    client,
                    secrets,
                    identity_data,
                )
            else:
                logger.info(f"Polling request - {async_task.id} still not Ready. ")
                continue


def execute_read_result_request(
    db: Session,
    async_task: RequestTask,
    strategy: PollingAsyncDSRStrategy,
    client: AuthenticatedClient,
    secrets: Dict[str, Any],
    identity_data: Dict[str, Any],
) -> None:

    result = strategy.get_result_request(
        client,
        secrets,
        identity_data,
    )
    logger.info(f"Result: {result}")
    if result:
        # Save updated data back to the request task.
        async_task.access_data = result
        logger.info(
            f"Polling request - {async_task.id} is ready. Added {len(result) if isinstance(result, list) else 1} results"
        )

    else:
        async_task.access_data = []
        logger.info(
            f"Polling request - {async_task.id} is ready but returned no results"
        )

    async_task.callback_succeeded = (
        True  # Setting this task as successful, so it wont loop anymore
    )
    async_task.update_status(db, ExecutionLogStatus.pending)
    async_task.save(db)
    log_task_queued(async_task, "callback")
    queue_request_task(async_task, privacy_request_proceed=True)


def execute_erasure_polling_requests(
    db: Session,
    async_task: RequestTask,
    query_config: SaaSQueryConfig,
) -> None:
    """Execute the erasure polling requests for a given privacy request"""
    # TODO: Implement erasure polling logic
    logger.info(f"Erasure polling not yet implemented. Task {async_task.id} passed")
