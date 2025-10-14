from typing import Callable, List, Optional, Tuple

from celery.app.task import Task
from loguru import logger
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Query, Session
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from fides.api.common_exceptions import (
    PrivacyRequestCanceled,
    PrivacyRequestNotFound,
    RequestTaskNotFound,
    ResumeTaskException,
    UpstreamTasksNotReady,
)
from fides.api.graph.config import TERMINATOR_ADDRESS, CollectionAddress
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.privacy_request import ExecutionLog, PrivacyRequest, RequestTask
from fides.api.models.worker_task import (
    RESUMABLE_EXECUTION_LOG_STATUSES,
    ExecutionLogStatus,
)
from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.graph_task import (
    GraphTask,
    mark_current_and_downstream_nodes_as_failed,
)
from fides.api.task.manual.manual_task_address import ManualTaskAddress
from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask
from fides.api.task.task_resources import TaskResources
from fides.api.tasks import DSR_QUEUE_NAME, DatabaseTask, celery_app
from fides.api.util.cache import cache_task_tracking_key
from fides.api.util.collection_util import Row
from fides.api.util.logger_context_utils import LoggerContextKeys, log_context
from fides.api.util.memory_watchdog import memory_limiter

# DSR 3.0 task functions


def get_privacy_request_and_task(
    session: Session, privacy_request_id: str, privacy_request_task_id: str
) -> Tuple[PrivacyRequest, RequestTask]:
    """
    Retrieves and validates a privacy request and its associated task
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

    return privacy_request, request_task


def run_prerequisite_task_checks(
    session: Session, privacy_request_id: str, privacy_request_task_id: str
) -> Tuple[PrivacyRequest, RequestTask, Query]:
    """
    Upfront checks that run as soon as the RequestTask is executed by the worker.

    Returns resources for use in executing a task
    """

    privacy_request, request_task = get_privacy_request_and_task(
        session, privacy_request_id, privacy_request_task_id
    )

    assert request_task  # For mypy

    upstream_results: Query = request_task.upstream_tasks_objects(session)

    # Only bother running this if the current task body needs to run
    if request_task.status == ExecutionLogStatus.pending:
        # Only running the upstream check instead of RequestTask.can_queue_request_task since
        # the node is already queued.
        if not request_task.upstream_tasks_complete(session, should_log=False):
            raise UpstreamTasksNotReady(
                f"Cannot start {request_task.action_type} task {request_task.collection_address}. Waiting for upstream tasks to finish."
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
        collection_address = request_task.request_task_address

        # Check if this is a manual task address
        graph_task: GraphTask
        if ManualTaskAddress.is_manual_task_address(collection_address):
            graph_task = ManualTaskGraphTask(resources)
        else:
            graph_task = GraphTask(resources)

    except Exception as exc:
        logger.debug(
            "Cannot execute task - error loading task from database. Exception {}",
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
            "Terminator {} task reached.",
            request_task.action_type,
        )
        return False
    if request_task.is_root_task:
        # Shouldn't be possible but adding as a catch-all
        return False
    if request_task.status not in RESUMABLE_EXECUTION_LOG_STATUSES:
        logger_method(request_task)(
            "Skipping {} task {} with status {}.",
            request_task.action_type,
            request_task.collection_address,
            request_task.status.value,
        )
        return False

    return True


def log_retry_attempt(retry_state: RetryCallState) -> None:
    """Log queue_downstream_tasks retry attempts."""

    logger.warning(
        "queue_downstream_tasks attempt {} failed. Retrying in {} seconds...",
        retry_state.attempt_number,
        retry_state.next_action.sleep,  # type: ignore[union-attr]
    )


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1),
    retry=retry_if_exception_type(OperationalError),
    before_sleep=log_retry_attempt,
)
def queue_downstream_tasks_with_retries(
    database_task: DatabaseTask,
    privacy_request_id: str,
    privacy_request_task_id: str,
    current_step: CurrentStep,
    privacy_request_proceed: bool,
) -> None:
    with database_task.get_new_session() as session:
        privacy_request, request_task = get_privacy_request_and_task(
            session, privacy_request_id, privacy_request_task_id
        )
        with logger.contextualize(
            privacy_request_source=(
                privacy_request.source.value if privacy_request.source else None
            )
        ):
            log_task_complete(request_task)
            queue_downstream_tasks(
                session,
                request_task,
                privacy_request,
                current_step,
                privacy_request_proceed,
            )


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
        from fides.service.privacy_request.privacy_request_service import (  # pylint: disable=cyclic-import
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
@memory_limiter
@log_context(
    capture_args={
        "privacy_request_id": LoggerContextKeys.privacy_request_id,
        "privacy_request_task_id": LoggerContextKeys.task_id,
    }
)
def run_access_node(
    self: DatabaseTask,
    privacy_request_id: str,
    privacy_request_task_id: str,
    privacy_request_proceed: bool = True,
) -> None:
    """Run an individual task in the access graph for DSR 3.0 and queue downstream nodes
    upon completion if applicable"""

    try:
        with self.get_new_session() as session:
            (
                privacy_request,
                request_task,
                upstream_results,
            ) = run_prerequisite_task_checks(
                session, privacy_request_id, privacy_request_task_id
            )
            with logger.contextualize(
                privacy_request_source=(
                    privacy_request.source.value if privacy_request.source else None
                ),
                collection=request_task.collection_address,
            ):
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
                        upstream_access_data: List[List[Row]] = (
                            _build_upstream_access_data(
                                graph_task.execution_node.input_keys, upstream_results
                            )
                        )
                        # Run the main access function
                        graph_task.access_request(*upstream_access_data)

        queue_downstream_tasks_with_retries(
            self,
            privacy_request_id,
            privacy_request_task_id,
            CurrentStep.upload_access,
            privacy_request_proceed,
        )
    except Exception as e:
        logger.error(f"Error in run_access_node: {e}")
        raise


@celery_app.task(base=DatabaseTask, bind=True)
@memory_limiter
@log_context(
    capture_args={
        "privacy_request_id": LoggerContextKeys.privacy_request_id,
        "privacy_request_task_id": LoggerContextKeys.task_id,
    }
)
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
        with logger.contextualize(
            privacy_request_source=(
                privacy_request.source.value if privacy_request.source else None
            ),
            collection=request_task.collection_address,
        ):
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
                    erasure_graph_task: GraphTask = create_graph_task(
                        session, request_task, resources
                    )
                    # Get access data that was saved in the erasure format that was collected from the
                    # access task for the same collection.  This data is used to build the masking request
                    retrieved_data: List[Row] = (
                        request_task.get_data_for_erasures() or []
                    )

                    upstream_access_data: List[List[Row]] = []

                    try:
                        upstream_access_data = (
                            get_upstream_access_data_for_erasure_task(
                                request_task, session, resources
                            )
                        )
                    except Exception as e:
                        logger.error(
                            f"Unable to get upstream access data for erasure task {request_task.collection_address}: {e}"
                        )

                    # Run the main erasure function, passing along the upstream access data.
                    # The extra data is currently only needed for generating BigQuery delete statements.
                    erasure_graph_task.erasure_request(
                        retrieved_data, inputs=upstream_access_data
                    )

    queue_downstream_tasks_with_retries(
        self,
        privacy_request_id,
        privacy_request_task_id,
        CurrentStep.finalize_erasure,
        privacy_request_proceed,
    )


@celery_app.task(base=DatabaseTask, bind=True)
@memory_limiter
@log_context(
    capture_args={
        "privacy_request_id": LoggerContextKeys.privacy_request_id,
        "privacy_request_task_id": LoggerContextKeys.task_id,
    }
)
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
        with logger.contextualize(
            privacy_request_source=(
                privacy_request.source.value if privacy_request.source else None
            ),
            collection=request_task.collection_address,
        ):
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
                    access_data: List = []
                    if upstream_results:
                        # For consent, expected that there is only one upstream node, the root node,
                        # and it holds the identity data (stored in a list for consistency with other
                        # data stored in access_data)
                        access_data = upstream_results[0].get_access_data() or []

                    graph_task.consent_request(access_data[0] if access_data else {})

    queue_downstream_tasks_with_retries(
        self,
        privacy_request_id,
        privacy_request_task_id,
        CurrentStep.finalize_consent,
        privacy_request_proceed,
    )


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
        "Starting '{}' task {} with current status '{}'.",
        request_task.action_type,
        request_task.collection_address,
        request_task.status.value,
    )


def log_task_complete(request_task: RequestTask) -> None:
    """Convenience method for logging task completion"""
    logger.info(
        "{} task {} is {}.",
        request_task.action_type.capitalize(),
        request_task.collection_address,
        request_task.status.value,
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


def get_upstream_access_data_for_erasure_task(
    erasure_request_task: RequestTask,
    session: Session,
    resources: TaskResources,
) -> List[List[Row]]:
    """
    Retrieves upstream access data for a given erasure request task.

    This function finds the corresponding access task for the erasure task,
    creates a GraphTask to extract input keys, and builds the upstream access data
    needed for erasure operations (particularly for BigQuery delete statements).

    Args:
        erasure_request_task: The erasure task that needs upstream access data
        session: Database session for querying
        resources: Task resources for creating GraphTask

    Returns:
        List[List[Row]]: Upstream access data ordered by input keys

    Raises:
        Exception: If the corresponding access task cannot be found
    """
    # Get the corresponding access task for the current erasure task
    access_request_task = (
        session.query(RequestTask)
        .filter(
            RequestTask.privacy_request_id == erasure_request_task.privacy_request_id,
            RequestTask.collection_address == erasure_request_task.collection_address,
            RequestTask.action_type == ActionType.access,
        )
        .first()
    )

    if not access_request_task:
        raise Exception(
            f"Unable to find access request task for erasure task {erasure_request_task.collection_address}"
        )

    # Convert the request task to a GraphTask to get the input_keys
    access_graph_task: GraphTask = create_graph_task(
        session, access_request_task, resources
    )

    # Build and return the upstream access data
    return _build_upstream_access_data(
        access_graph_task.execution_node.input_keys,
        access_request_task.upstream_tasks_objects(session),
    )


def _build_upstream_access_data(
    input_keys: List[CollectionAddress],
    upstream_tasks: Query,
) -> List[List[Row]]:
    """
    Helper function to build the access data for the current node.
    The access data is passed in the same order as the input keys.
    If we don't have access data for an upstream node, return an empty list.
    """

    ordered_upstream: List[Optional[RequestTask]] = _order_tasks_by_input_key(
        input_keys, upstream_tasks
    )
    return [task.get_access_data() if task else [] for task in ordered_upstream]


mapping = {
    ActionType.access.value: run_access_node,
    ActionType.erasure.value: run_erasure_node,
    ActionType.consent.value: run_consent_node,
}


def queue_request_task(
    request_task: RequestTask, privacy_request_proceed: bool = True
) -> None:
    """Queues the RequestTask in Celery and caches the Celery Task ID"""
    celery_task_fn: Task = mapping[request_task.action_type]
    celery_task = celery_task_fn.apply_async(
        queue=DSR_QUEUE_NAME,
        kwargs={
            "privacy_request_id": request_task.privacy_request_id,
            "privacy_request_task_id": request_task.id,
            "privacy_request_proceed": privacy_request_proceed,
        },
    )
    cache_task_tracking_key(request_task.id, celery_task.task_id)


def log_task_queued(request_task: RequestTask, location: str) -> None:
    """Helper for logging that tasks are queued"""
    logger_method(request_task)(
        "Queuing {} task {} from {}.",
        request_task.action_type,
        request_task.collection_address,
        location,
    )
