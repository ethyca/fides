from typing import List

from loguru import logger
from requests import Response
from sqlalchemy.orm import Session

from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.async_dsr.async_dsr_strategy import AsyncDSRStrategy
from fides.api.service.connectors.base_connector import AuthenticatedClient
from fides.api.service.connectors.query_configs.saas_query_config import SaaSQueryConfig
from fides.api.service.connectors.saas_connector import SaaSConnector
from fides.api.service.privacy_request.privacy_request_service import (
    PrivacyRequestError,
)
from fides.api.task.execute_request_tasks import (
    _build_upstream_access_data,
    create_graph_task,
    queue_request_task,
)
from fides.api.task.graph_task import GraphTask
from fides.api.task.task_resources import TaskResources
from fides.api.util.collection_util import NodeInput, Row


# TODO update tests to this reference
def requeue_polling_request(
    db: Session,
    async_task: RequestTask,
) -> None:
    """Re-queue a Privacy request that polling async tasks for a given privacy request"""
    # Check that the privacy request is approved or in processing
    privacy_request: PrivacyRequest = async_task.privacy_request

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
        # From the graph task get the strategy?
        query_config: SaaSQueryConfig = graph_task.connector.query_config(
            graph_task.execution_node
        )
        if async_task.action_type == ActionType.access:
            upstream_tasks = async_task.upstream_tasks_objects(db)
            upstream_access_data: List[List[Row]] = _build_upstream_access_data(
                graph_task.execution_node.input_keys, upstream_tasks
            )
            input_data: NodeInput = graph_task.pre_process_input_data(
                *upstream_access_data, group_dependent_fields=True
            )
            execute_read_polling_requests(
                db,
                async_task,
                query_config,
                graph_task.connector,
                graph_task.execution_node,
                input_data,
            )
        elif async_task.action_type == ActionType.erasure:
            execute_erasure_polling_requests(db, async_task, query_config)

    # And then we requeue the task and move forward from that point
    # TODO: Verify that we are not going to duplicate the access request
    queue_request_task(async_task, privacy_request_proceed=True)


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
    node: ExecutionNode,
    input_data: NodeInput,
) -> None:
    """Execute the read polling requests for a given privacy request"""
    read_requests = query_config.get_read_requests_by_identity()
    for read_request in read_requests:
        if read_request.async_config:
            strategy = AsyncDSRStrategy.get_strategy(
                read_request.async_config.strategy,
                read_request.async_config.configuration,
            )
            client: AuthenticatedClient = connector.get_client()
            status_request = strategy.get_status_request(
                client,
                node,
                async_task.privacy_request.policy,
                async_task.privacy_request,
                input_data,
                async_task.privacy_request.get_secrets(db),
            )


def execute_erasure_polling_requests(
    db: Session,
    async_task: RequestTask,
    query_config: SaaSQueryConfig,
) -> None:
    """Execute the erasure polling requests for a given privacy request"""
    erasure_requests = query_config.get_erasure_request_by_action(ActionType.erasure)
    for erasure_request in erasure_requests:
        if erasure_request.async_config:
            # TODO: Implement the polling strategy
            pass
