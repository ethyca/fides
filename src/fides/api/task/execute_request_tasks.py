from typing import Callable, List, Optional, Tuple

from celery.app.task import Task
from loguru import logger
from sqlalchemy.orm import Query, Session

from fides.api.common_exceptions import (
    PrivacyRequestCanceled,
    PrivacyRequestNotFound,
    RequestTaskNotFound,
    ResumeTaskException,
    UpstreamTasksNotReady,
)
from fides.api.graph.config import TERMINATOR_ADDRESS, CollectionAddress
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.policy import CurrentStep
from fides.api.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
    PrivacyRequestStatus,
    RequestTask,
)
from fides.api.schemas.policy import ActionType
from fides.api.task.graph_task import (
    GraphTask,
    mark_current_and_downstream_nodes_as_failed,
)
from fides.api.task.task_resources import TaskResources
from fides.api.tasks import DatabaseTask, celery_app
from fides.api.util.cache import cache_task_tracking_key
from fides.api.util.collection_util import Row

# DSR 3.0 task functions


def run_prerequisite_task_checks(
    session: Session, privacy_request_id: str, privacy_request_task_id: str
) -> Tuple[PrivacyRequest, RequestTask, Query]:
    """
    Upfront checks that run as soon as the RequestTask is executed by the worker.

    Returns resources for use in executing a task
    """
    privacy_request: Optional[PrivacyRequest] = PrivacyRequest.get(
        db=session, object_id=privacy_request_id
    )
    request_task: Optional[RequestTask] = RequestTask.get(
        db=session, object_id=privacy_request_task_id
    )

    if not privacy_request:
        raise PrivacyRequestNotFound(
            f"Privacy request with id {privacy_request_id} not found"
        )

    if privacy_request.status == PrivacyRequestStatus.canceled:
        raise PrivacyRequestCanceled(
            f"Cannot execute request task {privacy_request_task_id} of privacy request {privacy_request_id}: status is {privacy_request.status.value}"
        )

    if not request_task or not request_task.privacy_request_id == privacy_request.id:
        raise RequestTaskNotFound(
            f"Request Task with id {privacy_request_task_id} not found for privacy request {privacy_request_id}"
        )

    assert request_task  # For mypy

    upstream_results: Query = request_task.upstream_tasks_objects(session)

    # Only bother running this if the current task body needs to run
    if request_task.status == ExecutionLogStatus.pending:
        # Only running the upstream check instead of RequestTask.can_queue_request_task since
        # the node is already queued.
        if not request_task.upstream_tasks_complete(session, should_log=False):
            raise UpstreamTasksNotReady(
                f"Cannot start {request_task.action_type} task {request_task.collection_address}. Privacy Request: {privacy_request.id}, Request Task {request_task.id}.  Waiting for upstream tasks to finish."
            )

    return privacy_request, request_task, upstream_results


def create_graph_task(
    session: Session, request_task: RequestTask, resources: TaskResources
) -> GraphTask:
    """Hydrates a GraphTask from the saved collection details on the Request Task in the database

    This could fail if things like our Collection definitions have changed since we created the Task
    to begin with - this may be unrecoverable and a new Privacy Request should be created.
    """
    try:
        graph_task: GraphTask = GraphTask(resources)

    except Exception as exc:
        logger.debug(
            "Cannot execute task - error loading task from database. Privacy Request: {}, Request Task {}. Exception {}",
            request_task.privacy_request_id,
            request_task.id,
            str(exc),
        )
        # Normally the GraphTask takes care of creating the ExecutionLog, but in this case we can't create it in the first place!
        ExecutionLog.create(
            db=session,
            data={
                "connection_key": None,
                "dataset_name": request_task.dataset_name,
                "collection_name": request_task.collection_name,
                "fields_affected": [],
                "action_type": request_task.action_type,
                "status": ExecutionLogStatus.error,
                "privacy_request_id": request_task.privacy_request_id,
                "message": str(exc),
            },
        )
        mark_current_and_downstream_nodes_as_failed(request_task, session)

        raise ResumeTaskException(
            f"Cannot resume request task. Error hydrating task from database: Request Task {request_task.id} for Privacy Request {request_task.privacy_request_id}. {exc}"
        )

    return graph_task


def can_run_task_body(
    request_task: RequestTask,
) -> bool:
    """Return True if we can execute the task body. We should skip if the task is already
    complete or this is a root/terminator node"""
    if request_task.is_terminator_task:
        logger.info(
            "Terminator {} task reached. Privacy Request: {}, Request Task {}",
            request_task.action_type.value,
            request_task.privacy_request_id,
            request_task.id,
        )
        return False
    if request_task.is_root_task:
        # Shouldn't be possible but adding as a catch-all
        return False
    if request_task.status != ExecutionLogStatus.pending:
        logger_method(request_task)(
            "Skipping {} task {} with status {}. Privacy Request: {}, Request Task {}",
            request_task.action_type.value,
            request_task.collection_address,
            request_task.status.value,
            request_task.privacy_request_id,
            request_task.id,
        )
        return False

    return True


def queue_downstream_tasks(
    session: Session,
    request_task: RequestTask,
    privacy_request: PrivacyRequest,
    next_step: CurrentStep,
    privacy_request_proceed: bool,
) -> None:
    """Queue downstream tasks of the current node **if** the downstream task has all its upstream tasks completed.

    If we've reached the terminator task, restart the privacy request from the appropriate checkpoint.
    """
    pending_downstream: Query = request_task.get_pending_downstream_tasks(session)
    for downstream_task in pending_downstream:
        if downstream_task.can_queue_request_task(session, should_log=True):
            log_task_queued(downstream_task, request_task.collection_address)
            queue_request_task(downstream_task, privacy_request_proceed)

    if (
        request_task.request_task_address == TERMINATOR_ADDRESS
        and request_task.status != ExecutionLogStatus.complete
    ):
        # Only queue privacy request from the next step if we haven't reached the terminator before.
        # Multiple pathways could mark the same node as complete, so we may have already reached the
        # terminator node through a quicker path.
        from fides.api.service.privacy_request.request_runner_service import (
            queue_privacy_request,
        )

        if (
            privacy_request_proceed
        ):  # For Testing, this could be set to False, so we could just
            # run one of the graphs and not the entire privacy request
            queue_privacy_request(
                privacy_request_id=privacy_request.id,
                from_step=next_step.value,
            )
        request_task.update_status(session, ExecutionLogStatus.complete)


@celery_app.task(base=DatabaseTask, bind=True)
def run_access_node(
    self: DatabaseTask,
    privacy_request_id: str,
    privacy_request_task_id: str,
    privacy_request_proceed: bool = True,
) -> None:
    """Run an individual task in the access graph for DSR 3.0 and queue downstream nodes
    upon completion if applicable"""
    with self.get_new_session() as session:
        privacy_request, request_task, upstream_results = run_prerequisite_task_checks(
            session, privacy_request_id, privacy_request_task_id
        )
        log_task_starting(request_task)

        if can_run_task_body(request_task):
            # Build GraphTask resource to facilitate execution
            with TaskResources(
                privacy_request,
                privacy_request.policy,
                session.query(ConnectionConfig).all(),
                request_task,
                session,
            ) as resources:
                graph_task: GraphTask = create_graph_task(
                    session, request_task, resources
                )
                # Currently, upstream tasks and "input keys" (which are built by data dependencies)
                # are the same, but they may not be the same in the future.
                ordered_upstream_tasks: List[Optional[RequestTask]] = (
                    _order_tasks_by_input_key(
                        graph_task.execution_node.input_keys, upstream_results
                    )
                )
                # Pass in access data dependencies in the same order as the input keys.
                # If we don't have access data for an upstream node, pass in an empty list
                upstream_access_data: List[List[Row]] = [
                    upstream.get_access_data() if upstream else []
                    for upstream in ordered_upstream_tasks
                ]
                # Run the main access function
                graph_task.access_request(*upstream_access_data)
                log_task_complete(request_task)

        queue_downstream_tasks(
            session,
            request_task,
            privacy_request,
            CurrentStep.upload_access,
            privacy_request_proceed,
        )
        return


@celery_app.task(base=DatabaseTask, bind=True)
def run_erasure_node(
    self: DatabaseTask,
    privacy_request_id: str,
    privacy_request_task_id: str,
    privacy_request_proceed: bool = True,
) -> None:
    """Run an individual task in the erasure graph for DSR 3.0 and queue downstream nodes
    upon completion if applicable"""
    with self.get_new_session() as session:
        privacy_request, request_task, _ = run_prerequisite_task_checks(
            session, privacy_request_id, privacy_request_task_id
        )
        log_task_starting(request_task)

        if can_run_task_body(request_task):
            with TaskResources(
                privacy_request,
                privacy_request.policy,
                session.query(ConnectionConfig).all(),
                request_task,
                session,
            ) as resources:
                # Build GraphTask resource to facilitate execution
                graph_task: GraphTask = create_graph_task(
                    session, request_task, resources
                )
                # Get access data that was saved in the erasure format that was collected from the
                # access task for the same collection.  This data is used to build the masking request
                retrieved_data: List[Row] = request_task.get_data_for_erasures() or []

                # Run the main erasure function!
                graph_task.erasure_request(retrieved_data)

                log_task_complete(request_task)

        queue_downstream_tasks(
            session,
            request_task,
            privacy_request,
            CurrentStep.finalize_erasure,
            privacy_request_proceed,
        )
        return


@celery_app.task(base=DatabaseTask, bind=True)
def run_consent_node(
    self: DatabaseTask,
    privacy_request_id: str,
    privacy_request_task_id: str,
    privacy_request_proceed: bool = True,
) -> None:
    """Run an individual task in the consent graph for DSR 3.0 and queue downstream nodes
    upon completion if applicable"""
    with self.get_new_session() as session:
        privacy_request, request_task, upstream_results = run_prerequisite_task_checks(
            session, privacy_request_id, privacy_request_task_id
        )
        log_task_starting(request_task)

        if can_run_task_body(request_task):
            # Build GraphTask resource to facilitate execution
            with TaskResources(
                privacy_request,
                privacy_request.policy,
                session.query(ConnectionConfig).all(),
                request_task,
                session,
            ) as resources:
                graph_task: GraphTask = create_graph_task(
                    session, request_task, resources
                )
                if upstream_results:
                    # For consent, expected that there is only one upstream node, the root node,
                    # and it holds the identity data (stored in a list for consistency with other
                    # data stored in access_data)
                    access_data: List = upstream_results[0].get_access_data() or []

                graph_task.consent_request(access_data[0] if access_data else {})

                log_task_complete(request_task)

        queue_downstream_tasks(
            session,
            request_task,
            privacy_request,
            CurrentStep.finalize_consent,
            privacy_request_proceed,
        )
        return


def logger_method(request_task: RequestTask) -> Callable:
    """Log selected no-op items with debug method and others with info method"""
    return (
        logger.debug
        if request_task.status == ExecutionLogStatus.complete
        else logger.info
    )


def log_task_starting(request_task: RequestTask) -> None:
    """Convenience method for logging task start"""
    logger_method(request_task)(
        "Starting '{}' task {} with current status '{}'. Privacy Request: {}, Request Task {}",
        request_task.action_type,
        request_task.collection_address,
        request_task.status.value,
        request_task.privacy_request_id,
        request_task.id,
    )


def log_task_complete(request_task: RequestTask) -> None:
    """Convenience method for logging task completion"""
    logger.info(
        "{} task {} is {}. Privacy Request: {}, Request Task {}",
        request_task.action_type.value.capitalize(),
        request_task.collection_address,
        request_task.status.value,
        request_task.privacy_request_id,
        request_task.id,
    )


def _order_tasks_by_input_key(
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


mapping = {
    ActionType.access: run_access_node,
    ActionType.erasure: run_erasure_node,
    ActionType.consent: run_consent_node,
}


def queue_request_task(
    request_task: RequestTask, privacy_request_proceed: bool = True
) -> None:
    """Queues the RequestTask in Celery and caches the Celery Task ID"""
    celery_task_fn: Task = mapping[request_task.action_type]
    celery_task = celery_task_fn.delay(
        privacy_request_id=request_task.privacy_request_id,
        privacy_request_task_id=request_task.id,
        privacy_request_proceed=privacy_request_proceed,
    )
    cache_task_tracking_key(request_task.id, celery_task.task_id)


def log_task_queued(request_task: RequestTask, location: str) -> None:
    """Helper for logging that tasks are queued"""
    logger_method(request_task)(
        "Queuing {} task {} from {}. Privacy Request: {}, Request Task {}",
        request_task.action_type.value,
        request_task.collection_address,
        location,
        request_task.privacy_request_id,
        request_task.id,
    )
