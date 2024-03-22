from typing import Callable, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Query, Session

from fides.api.common_exceptions import PrivacyRequestNotFound, RequestTaskNotFound
from fides.api.graph.config import TERMINATOR_ADDRESS, CollectionAddress
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.policy import CurrentStep
from fides.api.models.privacy_request import (
    PrivacyRequest,
    PrivacyRequestStatus,
    RequestTask,
    TaskStatus,
)
from fides.api.models.sql_models import System  # type: ignore[attr-defined]
from fides.api.task.graph_task import GraphTask
from fides.api.task.task_resources import TaskResources
from fides.api.tasks import DatabaseTask, celery_app
from fides.api.util.collection_util import Row


def order_tasks_by_input_key(
    input_keys: List[CollectionAddress], upstream_tasks: Query
) -> List[Optional[RequestTask]]:
    """Order tasks by input key. If task doesn't exist, add None in its place

    Data being passed to GraphTask.access_request is expected to have the same order
    as input keys so we know which data belongs to which upstream collection
    """
    tasks: List[Optional[RequestTask]] = []
    for key in input_keys:
        task = next(
            (
                upstream
                for upstream in upstream_tasks
                if upstream.collection_address == key.value
            ),
            None,
        )
        tasks.append(task)
    return tasks


def collect_task_resources(
    session: Session, privacy_request: PrivacyRequest
) -> TaskResources:
    """Build the TaskResources artifact which has historically been used for GraphTask"""
    return TaskResources(
        privacy_request,
        privacy_request.policy,
        session.query(ConnectionConfig).all(),
        session,
    )


def prerequisite_task_checks(
    session: Session, privacy_request_id: str, privacy_request_task_id: str
):
    """Verify privacy request and task request exist and upstream tasks are complete"""
    privacy_request: PrivacyRequest = PrivacyRequest.get(
        db=session, object_id=privacy_request_id
    )
    request_task: RequestTask = RequestTask.get(
        db=session, object_id=privacy_request_task_id
    )

    if not privacy_request:
        raise PrivacyRequestNotFound(
            f"Privacy request with id {privacy_request_id} not found"
        )

    if not request_task:
        raise RequestTaskNotFound(f"Request Task with id {request_task} not found")

    upstream_results = session.query(RequestTask).filter(False)
    if request_task.status == TaskStatus.pending:
        upstream_results: Query = session.query(RequestTask).filter(
            RequestTask.privacy_request_id == privacy_request_id,
            RequestTask.status == PrivacyRequestStatus.complete,
            RequestTask.action_type == request_task.action_type,
            RequestTask.collection_address.in_(request_task.upstream_tasks),
        )

        if not upstream_results.count() == len(request_task.upstream_tasks):
            raise RequestTaskNotFound(
                f"Cannot start Privacy Request Task {request_task.id} - status is {request_task.status}"
            )
    return privacy_request, request_task, upstream_results


@celery_app.task(base=DatabaseTask, bind=True)
def run_access_node(
    self: DatabaseTask, privacy_request_id: str, privacy_request_task_id: str
) -> None:
    """Run an individual task in the access graph"""
    with self.get_new_session() as session:
        privacy_request, request_task, upstream_results = prerequisite_task_checks(
            session, privacy_request_id, privacy_request_task_id
        )
        logger.info(
            "Starting access task {}. Privacy Request: {}, Request Task {}",
            request_task.collection_address,
            privacy_request.id,
            request_task.id,
        )

        if request_task.is_terminator_task:
            # If we've reached the last node in the access graph, mark it as complete
            request_task.update_status(session, TaskStatus.complete)

        if request_task.status == TaskStatus.complete:
            # If the task is already complete, queue downstream tasks if applicable
            queue_downstream_tasks(
                session,
                request_task,
                privacy_request,
                run_access_node,
                CurrentStep.upload_access,
            )
            return

        # Build GraphTask resource to facilitate execution
        task_resources: TaskResources = collect_task_resources(session, privacy_request)
        graph_task: GraphTask = GraphTask(request_task, task_resources)
        ordered_upstream_tasks: List[Optional[RequestTask]] = order_tasks_by_input_key(
            graph_task.execution_node.input_keys, upstream_results
        )
        # Pass in access data dependencies in the same order as the input keys.
        # If we don't have access data for an upstream node, pass in an empty list
        upstream_access_data: List[List[Row]] = [
            upstream.access_data if upstream else []
            for upstream in ordered_upstream_tasks
        ]
        # Run the main access function!
        graph_task.access_request(*upstream_access_data)
        request_task.update_status(session, TaskStatus.complete)
        logger.info(
            "Access task {} complete. Privacy Request: {}, Request Task {}",
            request_task.collection_address,
            privacy_request.id,
            request_task.id,
        )

        queue_downstream_tasks(
            session,
            request_task,
            privacy_request,
            run_access_node,
            CurrentStep.upload_access,
        )
        return


def queue_downstream_tasks(
    session: Session,
    request_task: RequestTask,
    privacy_request: PrivacyRequest,
    run_node_function: Callable,
    next_step: CurrentStep,
):
    """Queue downstream tasks of the current node if the downstream task has all its upstream tasks completed.

    If we've reached the terminator task, restart the privacy request from the appropriate checkpoint.
    """
    pending_downstream_tasks: Query = request_task.pending_downstream_tasks(session)
    for downstream_task in pending_downstream_tasks:
        if downstream_task.upstream_tasks_complete(session):
            logger.info(
                "Queuing {} task {} from {} {}. Privacy Request: {}, Request Task {}. Upstream nodes complete.",
                downstream_task.action_type.value,
                downstream_task.collection_address,
                request_task.action_type.value,
                request_task.collection_address,
                privacy_request.id,
                downstream_task.id,
            )
            run_node_function.delay(
                privacy_request_id=privacy_request.id,
                privacy_request_task_id=downstream_task.id,
            )
        else:
            logger.info(
                "Cannot queue {} task {}. Privacy Request: {}, Request Task {}. Waiting for upstream nodes.",
                downstream_task.action_type.value,
                downstream_task.collection_address,
                privacy_request.id,
                downstream_task.id,
            )

    if request_task.request_task_address == TERMINATOR_ADDRESS:
        from fides.api.service.privacy_request.request_runner_service import (
            queue_privacy_request,
        )

        queue_privacy_request(
            privacy_request_id=privacy_request.id,
            from_step=next_step.value,
        )


@celery_app.task(base=DatabaseTask, bind=True)
def run_erasure_node(
    self: DatabaseTask, privacy_request_id: str, privacy_request_task_id: str
) -> None:
    """Run an individual task in the erasure graph"""
    with self.get_new_session() as session:
        privacy_request, request_task, upstream_results = prerequisite_task_checks(
            session, privacy_request_id, privacy_request_task_id
        )
        logger.info(
            "Starting erasure task {}. Privacy Request: {}, Request Task {}",
            request_task.collection_address,
            privacy_request.id,
            request_task.id,
        )

        if request_task.is_terminator_task:
            # If we've reached the last node in the erasure graph, mark it as complete
            request_task.update_status(session, TaskStatus.complete)

        if request_task.status == TaskStatus.complete:
            # If the task is already complete, queue downstream tasks if applicable
            queue_downstream_tasks(
                session,
                request_task,
                privacy_request,
                run_erasure_node,
                CurrentStep.finalize_erasure,
            )
            return

        # Set to pending in case of retry
        request_task.update_status(session, TaskStatus.pending)
        # Build GraphTask resource to facilitate execution
        task_resources = collect_task_resources(session, privacy_request)
        graph_task: GraphTask = GraphTask(request_task, task_resources)
        # Get access data that was saved in the erasure format that was collected from the
        # access task for the same node.  This data is used to build the masking request
        retrieved_data: List[Row] = request_task.data_for_erasures or []
        # Get access data in erasure format from upstream tasks of the current node. This is useful
        # for email connectors where the access request doesn't actually retrieve data
        upstream_retrieved_data: List[List[Row]] = request_task.erasure_input_data or []
        # Run the main erasure function!
        graph_task.erasure_request(retrieved_data, upstream_retrieved_data)
        request_task.update_status(session, TaskStatus.complete)

        logger.info(
            "Erasure task {} complete. Privacy Request: {}, Request Task {}",
            request_task.collection_address,
            privacy_request.id,
            request_task.id,
        )

        queue_downstream_tasks(
            session,
            request_task,
            privacy_request,
            run_erasure_node,
            CurrentStep.finalize_erasure,
        )
        return


@celery_app.task(base=DatabaseTask, bind=True)
def run_consent_node(
    self: DatabaseTask, privacy_request_id: str, privacy_request_task_id: str
) -> None:
    """Run an individual task in the consent graph"""
    with self.get_new_session() as session:
        privacy_request, request_task, upstream_results = prerequisite_task_checks(
            session, privacy_request_id, privacy_request_task_id
        )
        logger.info(
            "Starting consent task {}. Privacy Request: {}, Request Task {}",
            request_task.collection_address,
            privacy_request.id,
            request_task.id,
        )

        if request_task.is_terminator_task:
            # If we've reached the last node in the access graph, mark it as complete
            request_task.update_status(session, TaskStatus.complete)

        if request_task.status == TaskStatus.complete:
            # If the task is already complete, queue downstream tasks if applicable
            queue_downstream_tasks(
                session,
                request_task,
                privacy_request,
                run_consent_node,
                CurrentStep.finalize_consent,
            )
            return

        task_resources: TaskResources = collect_task_resources(session, privacy_request)
        # Build GraphTask resource to facilitate execution
        task = GraphTask(request_task, task_resources)
        # TODO catch errors if no upstream result
        task.consent_request(upstream_results[0].consent_data)

        request_task.update_status(session, TaskStatus.complete)
        logger.info(
            "Consent task {} complete. Privacy Request: {}, Request Task {}",
            request_task.collection_address,
            privacy_request.id,
            request_task.id,
        )

        queue_downstream_tasks(
            session,
            request_task,
            privacy_request,
            run_consent_node,
            CurrentStep.finalize_consent,
        )
        return
