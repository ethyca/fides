from typing import Any, Callable, Dict, List, Optional, Tuple

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
    PrivacyRequestPaused,
    RequestTaskNotFound,
    ResumeTaskException,
    UpstreamTasksNotReady,
)
from fides.api.graph.config import TERMINATOR_ADDRESS, CollectionAddress
from fides.api.models.attachment import AttachmentReferenceType
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_instance import ManualTaskInstance
from fides.api.models.privacy_request import ExecutionLog, PrivacyRequest, RequestTask
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    MANUAL_TASK_COLLECTIONS,
    ManualTaskExecutionTiming,
    ManualTaskParentEntityType,
)
from fides.api.schemas.manual_tasks.manual_task_status import StatusType
from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.graph_task import (
    GraphTask,
    mark_current_and_downstream_nodes_as_failed,
)
from fides.api.task.task_resources import TaskResources
from fides.api.tasks import DSR_QUEUE_NAME, DatabaseTask, celery_app
from fides.api.util.cache import cache_task_tracking_key
from fides.api.util.collection_util import Row
from fides.api.util.logger_context_utils import LoggerContextKeys, log_context
from fides.config import CONFIG

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
        graph_task: GraphTask = GraphTask(resources)

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
        logger.info("Root task encountered, skipping execution")
        return False

    # For manual task nodes, we want to check their status
    # Manual task nodes have collection names of "pre_execution" or "post_execution"
    if request_task.collection_name in MANUAL_TASK_COLLECTIONS.values():
        if request_task.status == ExecutionLogStatus.complete:
            logger.info(
                "Manual task node {} is already complete, skipping execution",
                request_task.collection_address,
            )
            return False
        logger.info(
            "Identified manual task node {} for processing",
            request_task.collection_address,
        )
        return True

    if request_task.status != ExecutionLogStatus.pending:
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
        logger.info(
            "Terminator task reached. Task status: {}, privacy_request_proceed: {}, next_step: {}",
            request_task.status,
            privacy_request_proceed,
            next_step.value,
        )
        from fides.service.privacy_request.privacy_request_service import (  # pylint: disable=cyclic-import
            queue_privacy_request,
        )

        if (
            privacy_request_proceed
        ):  # For Testing, this could be set to False, so we could just
            # run one of the graphs and not the entire privacy request
            logger.info("Queueing privacy request from step: {}", next_step.value)
            queue_privacy_request(
                privacy_request_id=privacy_request.id,
                from_step=next_step.value,
            )
        request_task.update_status(session, ExecutionLogStatus.complete)
    elif request_task.request_task_address == TERMINATOR_ADDRESS:
        logger.info(
            "Terminator task reached but status is already complete: {}",
            request_task.status,
        )
    else:
        logger.info(
            "Not a terminator task. request_task_address: {}, TERMINATOR_ADDRESS: {}, status: {}",
            request_task.request_task_address,
            TERMINATOR_ADDRESS,
            request_task.status,
        )


@celery_app.task(base=DatabaseTask, bind=True)
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
            privacy_request, request_task, upstream_results = (
                run_prerequisite_task_checks(
                    session, privacy_request_id, privacy_request_task_id
                )
            )
            with logger.contextualize(
                privacy_request_source=(
                    privacy_request.source.value if privacy_request.source else None
                )
            ):
                log_task_starting(request_task)
                logger.info(
                    "Task {} starting with status {}",
                    request_task.collection_address,
                    request_task.status,
                )

                if can_run_task_body(request_task):
                    # Check if this is a manual task node
                    if request_task.collection_name in [
                        "pre_execution",
                        "post_execution",
                    ]:
                        try:
                            logger.info(
                                "Running manual task node {} with status {}",
                                request_task.collection_address,
                                request_task.status,
                            )
                            task_completed = run_manual_task_node(session, request_task)
                            logger.info(
                                "Manual task node {} completed with result {} and status {}",
                                request_task.collection_address,
                                task_completed,
                                request_task.status,
                            )
                            # If task_completed is True, queue downstream tasks
                            if task_completed:
                                logger.info(
                                    "Queueing downstream tasks for completed manual task {}",
                                    request_task.collection_address,
                                )
                                queue_downstream_tasks_with_retries(
                                    self,
                                    privacy_request_id,
                                    privacy_request_task_id,
                                    CurrentStep.upload_access,
                                    privacy_request_proceed,
                                )
                            return
                        except PrivacyRequestPaused as exc:
                            # Request is paused waiting for manual input - no retry needed
                            logger.info(str(exc))
                            return
                        except UpstreamTasksNotReady as exc:
                            # Other upstream tasks not ready - retry
                            logger.info(
                                "Upstream tasks not ready, will retry in {} seconds: {}",
                                CONFIG.execution.task_retry_delay,
                                str(exc),
                            )
                            raise self.retry(
                                exc=exc,
                                countdown=CONFIG.execution.task_retry_delay,
                                max_retries=CONFIG.execution.task_retry_count,
                            )
                        except Exception as e:
                            logger.error(
                                "Error running manual task node {}: {}",
                                request_task.collection_address,
                                str(e),
                            )
                            raise

                    # Regular access task
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
                        ordered_upstream_tasks: List[Optional[RequestTask]] = (
                            _order_tasks_by_input_key(
                                graph_task.execution_node.input_keys, upstream_results
                            )
                        )
                        upstream_access_data: List[List[Row]] = [
                            upstream.get_access_data() if upstream else []
                            for upstream in ordered_upstream_tasks
                        ]
                        graph_task.access_request(*upstream_access_data)
                        # Mark task as complete since it executed without error
                        request_task.update_status(session, ExecutionLogStatus.complete)
                elif request_task.is_terminator_task:
                    # Special handling for terminator tasks - queue downstream even if not complete
                    logger.info(
                        "Terminator task {} reached, queueing downstream tasks",
                        request_task.collection_address,
                    )
                    queue_downstream_tasks_with_retries(
                        self,
                        privacy_request_id,
                        privacy_request_task_id,
                        CurrentStep.upload_access,
                        privacy_request_proceed,
                    )

                # Only queue downstream tasks if this task completed successfully
                if request_task.status == ExecutionLogStatus.complete:
                    logger.info(
                        "Task {} is complete, queueing downstream tasks",
                        request_task.collection_address,
                    )
                    queue_downstream_tasks_with_retries(
                        self,
                        privacy_request_id,
                        privacy_request_task_id,
                        CurrentStep.upload_access,
                        privacy_request_proceed,
                    )

    except Exception as e:
        logger.error(
            "Error in run_access_node for task {}: {}",
            (
                request_task.collection_address
                if "request_task" in locals()
                else "unknown"
            ),
            str(e),
        )
        raise


@celery_app.task(base=DatabaseTask, bind=True)
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
    try:
        with self.get_new_session() as session:
            privacy_request, request_task, _ = run_prerequisite_task_checks(
                session, privacy_request_id, privacy_request_task_id
            )
            with logger.contextualize(
                privacy_request_source=(
                    privacy_request.source.value if privacy_request.source else None
                )
            ):
                log_task_starting(request_task)

                if can_run_task_body(request_task):
                    # Check if this is a manual task node
                    if request_task.collection_name in [
                        "pre_execution",
                        "post_execution",
                    ]:
                        timing = ManualTaskExecutionTiming(request_task.collection_name)
                        try:
                            task_completed = run_manual_task_node(
                                session, request_task, timing
                            )
                            # If task_completed is True, queue downstream tasks
                            if task_completed:
                                queue_downstream_tasks_with_retries(
                                    self,
                                    privacy_request_id,
                                    privacy_request_task_id,
                                    CurrentStep.finalize_erasure,
                                    privacy_request_proceed,
                                )
                            return
                        except PrivacyRequestPaused as exc:
                            # Request is paused waiting for manual input - no retry needed
                            logger.info(str(exc))
                            return
                        except UpstreamTasksNotReady as exc:
                            # Other upstream tasks not ready - retry
                            logger.info(
                                "Upstream tasks not ready, will retry in {} seconds: {}",
                                CONFIG.execution.task_retry_delay,
                                str(exc),
                            )
                            raise self.retry(
                                exc=exc,
                                countdown=CONFIG.execution.task_retry_delay,
                                max_retries=CONFIG.execution.task_retry_count,
                            )

                    # Regular erasure task
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
                        retrieved_data: List[Row] = (
                            request_task.get_data_for_erasures() or []
                        )
                        graph_task.erasure_request(retrieved_data)
                        # Mark task as complete since it executed without error
                        request_task.update_status(session, ExecutionLogStatus.complete)

                # Only queue downstream tasks if this task completed successfully
                if request_task.status == ExecutionLogStatus.complete:
                    queue_downstream_tasks_with_retries(
                        self,
                        privacy_request_id,
                        privacy_request_task_id,
                        CurrentStep.finalize_erasure,
                        privacy_request_proceed,
                    )

    except Exception as e:
        logger.error(
            "Error in run_erasure_node for task {}: {}",
            (
                request_task.collection_address
                if "request_task" in locals()
                else "unknown"
            ),
            str(e),
        )
        raise


@celery_app.task(base=DatabaseTask, bind=True)
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
            )
        ):
            log_task_starting(request_task)

            if can_run_task_body(request_task):
                # Check if this is a manual task node
                if request_task.collection_name in MANUAL_TASK_COLLECTIONS.values():
                    timing = ManualTaskExecutionTiming(request_task.collection_name)
                    try:
                        run_manual_task_node(session, request_task, timing)
                    except PrivacyRequestPaused as exc:
                        # Request is paused waiting for manual input - no retry needed
                        logger.info(str(exc))
                        return
                    except UpstreamTasksNotReady as exc:
                        # Other upstream tasks not ready - retry
                        logger.info(
                            "Upstream tasks not ready, will retry in {} seconds: {}",
                            CONFIG.execution.task_retry_delay,
                            str(exc),
                        )
                        raise self.retry(
                            exc=exc,
                            countdown=CONFIG.execution.task_retry_delay,
                            max_retries=CONFIG.execution.task_retry_count,
                        )
                else:
                    # Regular consent task
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
                            access_data = upstream_results[0].get_access_data() or []

                        graph_task.consent_request(
                            access_data[0] if access_data else {}
                        )

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


mapping = {
    ActionType.access.value: run_access_node,
    ActionType.erasure.value: run_erasure_node,
    ActionType.consent.value: run_consent_node,
}


def queue_request_task(
    request_task: RequestTask, privacy_request_proceed: bool = True
) -> None:
    """Queues the RequestTask in Celery and caches the Celery Task ID"""
    # Don't queue if task is already complete
    if request_task.status == ExecutionLogStatus.complete:
        logger.info(
            "Task {} is already complete, skipping queueing",
            request_task.collection_address,
        )
        return

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


def run_manual_task_node(
    session: Session,
    request_task: RequestTask,
    timing: Optional[ManualTaskExecutionTiming] = None,
) -> bool:
    """Check if all manual tasks for the given timing and connection config are complete.

    Args:
        session: Database session
        request_task: The request task representing the manual task node
        timing: Optional timing override. If not provided, will be derived from request_task.collection_name

    Returns:
        bool: True if the task was completed (either already complete or completed now), False if waiting for input
    """
    logger.info(
        "Starting run_manual_task_node for task {} with status {}",
        request_task.collection_address,
        request_task.status,
    )

    if request_task.status == ExecutionLogStatus.complete:
        logger.info(
            "Manual task node {} is already complete, skipping processing",
            request_task.collection_address,
        )
        return True

    if timing is None:
        timing = ManualTaskExecutionTiming(request_task.collection_name)

    logger.info(
        "Processing manual task node {} with timing {}",
        request_task.collection_address,
        timing.value,
    )

    privacy_request = _get_privacy_request(session, request_task)
    connection_config = _get_connection_config(session, request_task)
    manual_task = _get_manual_task(session, connection_config)

    if not manual_task:
        return True

    configs = _get_configs_for_timing(manual_task, timing)
    if not configs:
        return True

    instances = _get_manual_task_instances(session, request_task, manual_task, timing)

    if not instances:
        return _handle_no_instances(
            session, request_task, privacy_request, connection_config, timing
        )

    return _process_manual_task_instances(session, request_task, instances, timing)


def _get_privacy_request(session: Session, request_task: RequestTask) -> PrivacyRequest:
    """Get the privacy request for the task."""
    privacy_request = PrivacyRequest.get(
        db=session, object_id=request_task.privacy_request_id
    )
    if not privacy_request:
        raise PrivacyRequestNotFound(
            f"Privacy request {request_task.privacy_request_id} not found"
        )
    return privacy_request


def _get_connection_config(
    session: Session, request_task: RequestTask
) -> Optional[ConnectionConfig]:
    """Get the connection config for the manual task node."""
    connection_config = ConnectionConfig.filter(
        db=session,
        conditions=(ConnectionConfig.key == request_task.dataset_name),
    ).first()

    if not connection_config:
        logger.warning(
            "Connection config with key {} not found for manual task node {}. Marking node as complete.",
            request_task.dataset_name,
            request_task.collection_address,
        )
        request_task.update_status(session, ExecutionLogStatus.complete)
        return None

    return connection_config


def _get_manual_task(
    session: Session, connection_config: ConnectionConfig
) -> Optional[ManualTask]:
    """Get the manual task associated with the connection config."""
    manual_task = ManualTask.filter(
        db=session,
        conditions=(
            (ManualTask.parent_entity_id == connection_config.id)
            & (
                ManualTask.parent_entity_type
                == ManualTaskParentEntityType.connection_config
            )
        ),
    ).first()

    if not manual_task:
        logger.info(
            "No manual task found for connection config {}. Marking node as complete.",
            connection_config.key,
        )
        return None

    return manual_task


def _get_configs_for_timing(
    manual_task: ManualTask, timing: ManualTaskExecutionTiming
) -> List[Any]:
    """Get configs for the given timing."""
    configs = [
        config for config in manual_task.configs if config.execution_timing == timing
    ]

    logger.info(
        "Found {} configs with timing {} for task {}",
        len(configs),
        timing.value,
        manual_task.id,
    )

    if not configs:
        logger.info(
            "No manual task configs found for timing {}. Marking node as complete.",
            timing.value,
        )
        return []

    return configs


def _get_manual_task_instances(
    session: Session,
    request_task: RequestTask,
    manual_task: ManualTask,
    timing: ManualTaskExecutionTiming,
) -> List[ManualTaskInstance]:
    """Get instances for the specific manual task and timing."""
    instances = ManualTaskInstance.filter(
        db=session,
        conditions=(
            (ManualTaskInstance.entity_id == request_task.privacy_request_id)
            & (ManualTaskInstance.entity_type == "privacy_request")
            & (ManualTaskInstance.task_id == manual_task.id)
            & (ManualTaskInstance.config.has(execution_timing=timing))
        ),
    ).all()

    logger.info(
        "Found {} instances for task {} with timing {}",
        len(instances),
        request_task.collection_address,
        timing.value,
    )

    return instances


def _handle_no_instances(
    session: Session,
    request_task: RequestTask,
    privacy_request: PrivacyRequest,
    connection_config: ConnectionConfig,
    timing: ManualTaskExecutionTiming,
) -> bool:
    """Handle the case where no manual task instances exist yet."""
    logger.info(
        "No manual task instances found yet for privacy request {} with timing {}. Setting status to requires_input.",
        request_task.privacy_request_id,
        timing.value,
    )
    request_task.update_status(session, ExecutionLogStatus.pending)
    privacy_request.status = PrivacyRequestStatus.requires_input
    privacy_request.save(session)

    _create_pending_execution_log(session, request_task, connection_config, timing)

    raise PrivacyRequestPaused(
        f"Privacy request paused waiting for manual tasks with timing {timing.value}"
    )


def _create_pending_execution_log(
    session: Session,
    request_task: RequestTask,
    connection_config: ConnectionConfig,
    timing: ManualTaskExecutionTiming,
) -> None:
    """Create an execution log for pending manual tasks."""
    ExecutionLog.create(
        db=session,
        data={
            "connection_key": connection_config.key,
            "dataset_name": request_task.dataset_name,
            "collection_name": request_task.collection_name,
            "fields_affected": [],
            "action_type": request_task.action_type,
            "status": ExecutionLogStatus.pending,
            "privacy_request_id": request_task.privacy_request_id,
            "message": f"Waiting for manual tasks with timing {timing.value} to be created",
        },
    )


def _process_manual_task_instances(
    session: Session,
    request_task: RequestTask,
    instances: List[ManualTaskInstance],
    timing: ManualTaskExecutionTiming,
) -> bool:
    """Process manual task instances and determine if they're complete."""
    all_complete = all(
        instance.status == StatusType.completed for instance in instances
    )
    incomplete_count = sum(
        1 for instance in instances if instance.status != StatusType.completed
    )

    logger.info(
        "Task {} has {} complete instances and {} incomplete instances",
        request_task.collection_address,
        len(instances) - incomplete_count,
        incomplete_count,
    )

    if all_complete:
        return _handle_completed_instances(session, request_task, instances, timing)
    else:
        return _handle_incomplete_instances(
            session, request_task, instances, incomplete_count, timing
        )


def _handle_completed_instances(
    session: Session,
    request_task: RequestTask,
    instances: List[ManualTaskInstance],
    timing: ManualTaskExecutionTiming,
) -> bool:
    """Handle the case where all manual task instances are complete."""
    logger.info(
        "All manual tasks complete for timing {}. Marking node as complete.",
        timing.value,
    )

    submission_data = _build_submission_data(request_task, instances)
    _save_task_data(request_task, submission_data)
    request_task.update_status(session, ExecutionLogStatus.complete)

    _create_complete_execution_log(session, request_task, timing)
    session.commit()

    return True


def _handle_incomplete_instances(
    session: Session,
    request_task: RequestTask,
    instances: List[ManualTaskInstance],
    incomplete_count: int,
    timing: ManualTaskExecutionTiming,
) -> bool:
    """Handle the case where some manual task instances are incomplete."""
    logger.info(
        "{} manual tasks still pending for timing {}. Setting status to requires_input.",
        incomplete_count,
        timing.value,
    )
    request_task.update_status(session, ExecutionLogStatus.pending)

    privacy_request = PrivacyRequest.get(
        db=session, object_id=request_task.privacy_request_id
    )
    privacy_request.status = PrivacyRequestStatus.requires_input
    privacy_request.save(session)

    _create_pending_execution_log(session, request_task, None, timing)

    raise PrivacyRequestPaused(
        f"Privacy request paused waiting for {incomplete_count} manual tasks with timing {timing.value} to complete"
    )


def _build_submission_data(
    request_task: RequestTask, instances: List[ManualTaskInstance]
) -> Dict[str, List[Dict[str, Any]]]:
    """Build submission data from manual task instances."""
    submission_data_by_config = {}
    collection_key = request_task.collection_address

    if collection_key not in submission_data_by_config:
        submission_data_by_config[collection_key] = []

    for instance in instances:
        task_data = _build_task_data(instance)
        submission_data_by_config[collection_key].append(task_data)

    return submission_data_by_config


def _build_task_data(instance: ManualTaskInstance) -> Dict[str, Any]:
    """Build task data from a manual task instance."""
    task_data = {"data": []}

    # Add submission data
    for submission in instance.submissions:
        submission_data_entry = {
            "field_id": submission.field_id,
            "data": submission.data,
        }
        task_data["data"].append(submission_data_entry)

    # Add attachment data if any
    attachments = []
    for submission in instance.submissions:
        for attachment in submission.attachments:
            attachments.append(
                {
                    "file_name": attachment.file_name,
                    "storage_key": attachment.storage_key,
                }
            )
    if attachments:
        task_data["attachments"] = attachments

    return task_data


def _save_task_data(
    request_task: RequestTask, submission_data: Dict[str, List[Dict[str, Any]]]
) -> None:
    """Save submission data to the request task."""
    if request_task.action_type == ActionType.access:
        # For access tasks:
        # 1. Save raw data to access_data and data_for_erasures
        request_task.access_data = submission_data
        request_task.data_for_erasures = (
            submission_data  # Same data for both since no filtering needed
        )
    else:
        # For erasure tasks, save raw data
        request_task.data_for_erasures = submission_data


def _create_complete_execution_log(
    session: Session,
    request_task: RequestTask,
    timing: ManualTaskExecutionTiming,
) -> None:
    """Create an execution log for completed manual tasks."""
    ExecutionLog.create(
        db=session,
        data={
            "connection_key": None,  # Will be set by the task execution
            "dataset_name": request_task.dataset_name,
            "collection_name": request_task.collection_name,
            "fields_affected": [],
            "action_type": request_task.action_type,
            "status": ExecutionLogStatus.complete,
            "privacy_request_id": request_task.privacy_request_id,
            "message": f"All manual tasks with timing {timing.value} completed successfully",
        },
    )


manual_task_config = ConnectionConfig(
    key="manual_task_connector",
    name="Manual Task Connector",
    connection_type=ConnectionType.saas,
    access="write",
)
