from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.task_resources import TaskResources


def requeue_polling_request(
    db: Session,
    async_task: RequestTask,
) -> None:
    """Re-queue a Privacy request that polls async tasks for a given privacy request"""
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
        # graph_task: GraphTask = create_graph_task(db, async_task, resources)
        # Currently, upstream tasks and "input keys" (which are built by data dependencies)
        # are the same, but they may not be the same in the future.
        # upstream_tasks = async_task.upstream_tasks_objects(db)
        # upstream_access_data: List[List[Row]] = _build_upstream_access_data(
        #    graph_task.execution_node.input_keys, upstream_tasks
        # )
        # TODO: Implement the polling strategy
        logger.info(f"found resources: {resources}")
        return None


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
