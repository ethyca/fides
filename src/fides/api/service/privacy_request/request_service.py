from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from httpx import AsyncClient
from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import TextClause

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.models.privacy_request import (
    EXITED_EXECUTION_LOG_STATUSES,
    PrivacyRequest,
    RequestTask,
)
from fides.api.models.privacy_request.request_task import AsyncTaskType
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.drp_privacy_request import DrpPrivacyRequestCreate
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.schemas.redis_cache import Identity
from fides.api.tasks import DSR_QUEUE_NAME, DatabaseTask, celery_app
from fides.api.tasks.scheduled.scheduler import scheduler
from fides.api.util.cache import (
    FidesopsRedis,
    celery_tasks_in_flight,
    get_async_task_tracking_cache_key,
    get_cache,
    get_privacy_request_retry_count,
    increment_privacy_request_retry_count,
    reset_privacy_request_retry_count,
)
from fides.api.util.lock import redis_lock
from fides.config import CONFIG

PRIVACY_REQUEST_STATUS_CHANGE_POLL = "privacy_request_status_change_poll"
DSR_DATA_REMOVAL = "dsr_data_removal"
INTERRUPTED_TASK_REQUEUE_POLL = "interrupted_task_requeue_poll"
REQUEUE_INTERRUPTED_TASKS_LOCK = "requeue_interrupted_tasks_lock"
ASYNC_TASKS_STATUS_POLLING = "async_tasks_status_polling"
ASYNC_TASKS_STATUS_POLLING_LOCK = "async_tasks_status_polling_lock"
ASYNC_TASKS_STATUS_POLLING_LOCK_TIMEOUT = (
    300  # Starting timeout is shorter because the task goes directly to the workers.
)


def build_required_privacy_request_kwargs(
    requested_at: Optional[datetime],
    policy_id: str,
    verification_required: bool,
    authenticated: bool,
) -> Dict[str, Any]:
    """Build kwargs required for creating privacy request

    If identity verification is on, the request will have an initial status of
    "identity_unverified", otherwise, it will have an initial status of "pending".
    """
    status = (
        PrivacyRequestStatus.identity_unverified
        if verification_required and not authenticated
        else PrivacyRequestStatus.pending
    )
    return {
        "requested_at": requested_at,
        "policy_id": policy_id,
        "status": status,
    }


def cache_data(
    privacy_request: PrivacyRequest,
    identity: Identity,
    encryption_key: Optional[str],
    drp_request_body: Optional[DrpPrivacyRequestCreate],
    custom_privacy_request_fields: Optional[Dict[str, Any]] = None,
) -> None:
    """Cache privacy request data"""
    # Store identity and encryption key in the cache
    logger.info("Caching identity for privacy request {}", privacy_request.id)
    privacy_request.cache_identity(identity)
    privacy_request.cache_custom_privacy_request_fields(custom_privacy_request_fields)
    privacy_request.cache_encryption(encryption_key)  # handles None already

    if drp_request_body:
        privacy_request.cache_drp_request_body(drp_request_body)


def get_async_client() -> AsyncClient:
    """Return an async client used to make API requests"""
    return AsyncClient()


def initiate_poll_for_exited_privacy_request_tasks() -> None:
    """Initiates scheduler to check if a Privacy Request's status needs to be flipped when all
    Request Tasks have had a chance to run"""

    if CONFIG.test_mode:
        return

    assert (
        scheduler.running
    ), "Scheduler is not running! Cannot add Privacy Request Status Change job."

    logger.info("Initiating scheduler for Privacy Request Status Change")
    scheduler.add_job(
        func=poll_for_exited_privacy_request_tasks,
        trigger="interval",
        kwargs={},
        id=PRIVACY_REQUEST_STATUS_CHANGE_POLL,
        coalesce=True,
        replace_existing=True,
        seconds=CONFIG.execution.state_polling_interval,
    )


@celery_app.task(base=DatabaseTask, bind=True)
def poll_for_exited_privacy_request_tasks(self: DatabaseTask) -> Set[str]:
    """
    Mark a privacy request as errored if all of its Request Tasks have run but some have errored.

    When a Request Task fails, it marks itself and *every Request Task that can be reached by the current
    Request Task* as failed. However, other Request Tasks independent of this path should still have an
    opportunity to run. We wait until everything has run before marking the Privacy Request as errored so it
    can be reprocessed.
    """
    with self.get_new_session() as db:
        logger.debug("Polling for privacy requests awaiting errored status change")

        # Privacy Requests that needed approval are in "Approved" status as they process.
        # Privacy Requests that didn't need approval are "In Processing".
        # Privacy Requests in these states should be examined to see if all of its Request Tasks have had a chance
        # to complete.
        # Use query_without_large_columns to prevent OOM errors when processing many privacy requests
        in_progress_privacy_requests = (
            PrivacyRequest.query_without_large_columns(db)
            .filter(
                PrivacyRequest.status.in_(
                    [
                        PrivacyRequestStatus.in_processing,
                        PrivacyRequestStatus.approved,
                        PrivacyRequestStatus.requires_input,
                    ]
                )
            )
            # Only look at Privacy Requests that haven't been deleted
            .filter(PrivacyRequest.deleted_at.is_(None))
            .order_by(PrivacyRequest.created_at)
        )

        # TODO: With this approach, we're making 3*n queries , where n is the number of in-progress privacy requests.
        # We could optimize this to just get all the RequestTasks for all in-progress privacy requests in one single
        # query and then process them in-memory. This could be more efficient.
        def privacy_request_has_errored_tasks(
            privacy_request: PrivacyRequest, task_type: ActionType
        ) -> bool:
            """Check if a privacy request has exited all its tasks of the given type,
            and at least one of the tasks has errored.
            We specifically only query for the RequestTask.status column to avoid
            querying for the entire RequestTask row.
            """
            tasks_statuses_query = db.query(RequestTask.status).filter(
                RequestTask.privacy_request_id == privacy_request.id,
                RequestTask.action_type == task_type,
            )

            statuses = set(status for status, in tasks_statuses_query.all())
            all_exited = all(
                status in EXITED_EXECUTION_LOG_STATUSES for status in statuses
            )
            if all_exited and ExecutionLogStatus.error in statuses:
                logger.info(
                    f"Marking {task_type.value} step of {privacy_request.id} as error"
                )
                return True

            return False

        marked_as_errored: Set[str] = set()
        for pr in in_progress_privacy_requests.all():
            if pr.consent_tasks.count():
                # Consent propagation tasks - these are not created until access and erasure steps are complete.
                if privacy_request_has_errored_tasks(pr, ActionType.consent):
                    pr.error_processing(db)
                    marked_as_errored.add(pr.id)

            if pr.erasure_tasks.count():
                # Erasure tasks are created at the same time as access tasks but if any are errored, this means
                # we made it to the erasure section
                if privacy_request_has_errored_tasks(pr, ActionType.erasure):
                    pr.error_processing(db)
                    marked_as_errored.add(pr.id)

            if pr.access_tasks.count():
                if privacy_request_has_errored_tasks(pr, ActionType.access):
                    pr.error_processing(db)
                    marked_as_errored.add(pr.id)

        return marked_as_errored


def initiate_scheduled_dsr_data_removal() -> None:
    """Initiates scheduler to cleanup obsolete access and erasure data"""

    if CONFIG.test_mode:
        return

    assert (
        scheduler.running
    ), "Scheduler is not running! Cannot add DSR data removal job."

    logger.info("Initiating scheduler for DSR Data Removal")
    scheduler.add_job(
        func=remove_saved_dsr_data,
        kwargs={},
        id=DSR_DATA_REMOVAL,
        coalesce=False,
        replace_existing=True,
        trigger="cron",
        minute="0",
        hour="2",
        day="*",
        timezone="US/Eastern",
    )


@celery_app.task(base=DatabaseTask, bind=True)
def remove_saved_dsr_data(self: DatabaseTask) -> None:
    """
    Remove saved customer data that is no longer needed to facilitate running the access or erasure request.
    """
    with self.get_new_session() as db:
        logger.info("Running DSR Data Removal Task to cleanup obsolete user data")

        # Remove old request tasks which potentially contain encrypted PII
        remove_dsr_data: TextClause = text(
            """
            DELETE FROM requesttask
            USING privacyrequest
            WHERE requesttask.privacy_request_id = privacyrequest.id
            AND requesttask.created_at < :ttl
            AND privacyrequest.status = 'complete';
            """
        )

        result = db.execute(
            remove_dsr_data,
            {
                "ttl": (
                    datetime.now()
                    - timedelta(seconds=CONFIG.execution.request_task_ttl)
                ),
            },
        )
        affected_rows = result.rowcount
        logger.info(
            f"Deleted {affected_rows} expired request tasks via DSR Data Removal Task."
        )

        # Remove columns from old privacyrequests that potentially contain encrypted PII
        # or URL's that contain encrypted PII.
        remove_data_from_privacy_request: TextClause = text(
            """
            UPDATE privacyrequest
            SET filtered_final_upload = null, access_result_urls = null
            WHERE privacyrequest.updated_at < :ttl
            AND privacyrequest.status = 'complete';
            """
        )

        db.execute(
            remove_data_from_privacy_request,
            {
                "ttl": (  # Using Redis Default TTL Seconds by default
                    datetime.now() - timedelta(seconds=CONFIG.redis.default_ttl_seconds)
                ),
            },
        )

        db.commit()


def initiate_interrupted_task_requeue_poll() -> None:
    """Initiates scheduler to check for and requeue interrupted tasks"""

    if CONFIG.test_mode:
        return

    assert (
        scheduler.running
    ), "Scheduler is not running! Cannot add interrupted task requeue job."

    logger.info("Initiating scheduler for interrupted task requeue")
    scheduler.add_job(
        func=requeue_interrupted_tasks,
        trigger="interval",
        kwargs={},
        id=INTERRUPTED_TASK_REQUEUE_POLL,
        coalesce=True,
        replace_existing=True,
        seconds=CONFIG.execution.interrupted_task_requeue_interval,
    )


def initiate_polling_task_requeue() -> None:
    """Initiates scheduler to check for and requeue pending polling async tasks"""
    if CONFIG.test_mode:
        return

    assert (
        scheduler.running
    ), "Scheduler is not running! Cannot add async tasks status polling job."

    logger.info("Initiating scheduler for async tasks status polling")
    scheduler.add_job(
        func=requeue_polling_tasks,
        trigger="interval",
        kwargs={},
        id=ASYNC_TASKS_STATUS_POLLING,
        coalesce=True,
        replace_existing=True,
        seconds=CONFIG.execution.async_polling_interval_hours * 3600,
    )


def get_cached_task_id(entity_id: str) -> Optional[str]:
    """Gets the cached task ID for a privacy request or request task by ID.

    Raises Exception if cache operations fail, allowing callers to handle cache failures appropriately.
    """
    cache: FidesopsRedis = get_cache()
    try:
        task_id = cache.get(get_async_task_tracking_cache_key(entity_id))
        return task_id
    except Exception as exc:
        logger.error(f"Failed to get cached task ID for entity {entity_id}: {exc}")
        raise


def _get_task_ids_from_dsr_queue(
    redis_client: FidesopsRedis, chunk_size: int = 100
) -> Set[str]:
    """
    Get all task IDs from a Redis queue in a memory-efficient way.

    Args:
        redis_client: Redis client
        chunk_size: Size of chunks to process

    Returns:
        Set of task IDs
    """
    queued_tasks_ids = set()
    queue_length = redis_client.llen(DSR_QUEUE_NAME)

    # Process the queue in chunks to avoid memory issues with large queues
    for offset in range(0, queue_length, chunk_size):
        # Get a chunk of tasks (at most chunk_size elements)
        tasks_chunk = redis_client.lrange(
            DSR_QUEUE_NAME, offset, offset + chunk_size - 1
        )

        # Extract task IDs from the chunk
        for task in tasks_chunk:
            try:
                queued_tasks_ids.add(json.loads(task)["headers"]["id"])
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse task from queue: {e}")
                continue

    return queued_tasks_ids


def _cancel_interrupted_tasks_and_error_privacy_request(
    db: Session, privacy_request: PrivacyRequest, error_message: Optional[str] = None
) -> None:
    """
    Cancel all tasks associated with an interrupted privacy request and set the privacy request to error state.

    This function:
    1. Logs the error message (either provided or default)
    2. Revokes the main privacy request task and all associated request tasks
    3. Sets the privacy request status to error
    4. Creates an error log entry

    Args:
        db: Database session
        privacy_request: The privacy request to cancel and error
        error_message: Optional error message to log. If not provided, uses default message.
    """
    if error_message:
        logger.error(error_message)
    else:
        logger.error(
            f"Canceling interrupted tasks and marking privacy request {privacy_request.id} as error"
        )

    # Cancel all associated Celery tasks
    privacy_request.cancel_celery_tasks()

    # Set privacy request to error state using the existing method
    try:
        privacy_request.error_processing(db)
        logger.info(
            f"Privacy request {privacy_request.id} marked as error due to task interruption"
        )
    except Exception as exc:
        logger.error(
            f"Failed to mark privacy request {privacy_request.id} as error: {exc}"
        )


def _handle_privacy_request_requeue(
    db: Session, privacy_request: PrivacyRequest
) -> None:
    """Handle retry logic for a privacy request - either requeue or cancel based on retry count."""
    try:
        # Check retry count and either requeue or cancel based on limit
        current_retry_count = get_privacy_request_retry_count(privacy_request.id)
        max_retries = CONFIG.execution.privacy_request_requeue_retry_count

        if current_retry_count < max_retries:
            # Increment retry count and attempt requeue
            new_retry_count = increment_privacy_request_retry_count(privacy_request.id)
            logger.info(
                f"Requeuing privacy request {privacy_request.id} "
                f"(attempt {new_retry_count}/{max_retries})"
            )

            from fides.service.privacy_request.privacy_request_service import (  # pylint: disable=cyclic-import
                _requeue_privacy_request,
            )

            try:
                _requeue_privacy_request(db, privacy_request)
            except PrivacyRequestError as exc:
                # If requeue fails, cancel tasks and set to error state
                _cancel_interrupted_tasks_and_error_privacy_request(
                    db, privacy_request, exc.message
                )
        else:
            # Exceeded retry limit, cancel tasks and set to error state
            _cancel_interrupted_tasks_and_error_privacy_request(
                db,
                privacy_request,
                f"Privacy request {privacy_request.id} exceeded max retry attempts "
                f"({max_retries}), canceling tasks and setting to error state",
            )
            # Reset retry count since we're giving up
            reset_privacy_request_retry_count(privacy_request.id)

    except Exception as cache_exc:
        # If cache operations fail (Redis down, network issues, etc.), fail safe by canceling
        _cancel_interrupted_tasks_and_error_privacy_request(
            db,
            privacy_request,
            f"Cache operation failed for privacy request {privacy_request.id}, "
            f"failing safe by canceling tasks: {cache_exc}",
        )


def _get_request_task_ids_in_progress(
    db: Session, privacy_request_id: str
) -> List[str]:
    """Get the IDs of request tasks that are currently in progress for a privacy request."""
    request_tasks_in_progress = (
        db.query(RequestTask.id)
        .filter(RequestTask.privacy_request_id == privacy_request_id)
        .filter(
            RequestTask.status.in_(
                [
                    ExecutionLogStatus.in_processing,
                    ExecutionLogStatus.pending,
                ]
            )
        )
        .all()
    )
    return [task[0] for task in request_tasks_in_progress]


def _has_polling_tasks(db: Session, privacy_request_id: str) -> bool:
    """
    Check if a privacy request has any polling async tasks.

    Args:
        db: Database session
        privacy_request_id: The ID of the privacy request to check

    Returns:
        bool: True if the privacy request has polling tasks, False otherwise
    """
    return db.query(
        db.query(RequestTask)
        .filter(
            RequestTask.privacy_request_id == privacy_request_id,
            RequestTask.async_type == AsyncTaskType.polling,
        )
        .exists()
    ).scalar()


# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
@celery_app.task(base=DatabaseTask, bind=True)
def requeue_interrupted_tasks(self: DatabaseTask) -> None:
    """
    Requeue interrupted tasks for privacy requests that are in progress.

    This function checks for privacy requests that are currently pending or in progress and
    verifies if their associated tasks are still in the queue or running. If any
    task is found to be interrupted (i.e., not in the queue and not running), the
    privacy request is requeued to ensure its completion.

    The function performs the following steps:
    1. Retrieves all task IDs currently in the queue.
    2. Fetches all in-progress privacy requests from the database.
    3. Checks each privacy request to determine if its tasks are still active.
    4. Requeues the privacy request if any of its tasks are found to be interrupted.
    """
    redis_conn: FidesopsRedis = get_cache()

    with redis_lock(REQUEUE_INTERRUPTED_TASKS_LOCK, 600) as lock:
        if not lock:
            return
        with self.get_new_session() as db:
            logger.debug("Starting check for interrupted tasks to requeue")

            # Get all in-progress privacy requests that haven't been updated in the last 5 minutes
            # Use query_without_large_columns to prevent OOM errors when processing many privacy requests
            in_progress_requests = (
                PrivacyRequest.query_without_large_columns(db)
                .filter(
                    PrivacyRequest.status.in_(
                        [
                            PrivacyRequestStatus.in_processing,
                            PrivacyRequestStatus.approved,
                            PrivacyRequestStatus.requires_input,
                        ]
                    )
                )
                .filter(PrivacyRequest.deleted_at.is_(None))
                .order_by(PrivacyRequest.created_at)
            )

            if not in_progress_requests.count():
                logger.debug("No in-progress privacy requests to check")
                return

            logger.debug(
                f"Found {in_progress_requests.count()} privacy requests to check"
            )

            # Get task IDs from the queue in a memory-efficient way
            try:
                queued_tasks_ids = _get_task_ids_from_dsr_queue(redis_conn)
            except Exception as queue_exc:
                logger.warning(
                    f"Failed to get task IDs from queue, skipping queue state checks: {queue_exc}"
                )
                return

            # Check each privacy request
            for privacy_request in in_progress_requests:
                should_requeue = False
                logger.debug(f"Checking tasks for privacy request {privacy_request.id}")

                try:
                    task_id = get_cached_task_id(privacy_request.id)
                except Exception as cache_exc:
                    # If we can't get the task ID due to cache failure, fail safe by canceling
                    _cancel_interrupted_tasks_and_error_privacy_request(
                        db,
                        privacy_request,
                        f"Cache failure when getting task ID for privacy request {privacy_request.id}, "
                        f"failing safe by canceling tasks: {cache_exc}",
                    )
                    continue

                # If the task ID is not cached, we can't check if it's running
                # This means the request is stuck - cancel it
                if not task_id:
                    _cancel_interrupted_tasks_and_error_privacy_request(
                        db,
                        privacy_request,
                        f"No task ID found for privacy request {privacy_request.id}, "
                        f"request is stuck without a running task - canceling",
                    )
                    continue

                # Check if the main privacy request task is active
                if task_id not in queued_tasks_ids and not celery_tasks_in_flight(
                    [task_id]
                ):
                    request_tasks_count = (
                        db.query(RequestTask)
                        .filter(RequestTask.privacy_request_id == privacy_request.id)
                        .count()
                    )
                    if request_tasks_count == 0:
                        logger.warning(
                            f"The task for privacy request {privacy_request.id} was terminated before it could schedule any request tasks, requeueing privacy request"
                        )
                        should_requeue = True

                    request_task_ids_in_progress = _get_request_task_ids_in_progress(
                        db, privacy_request.id
                    )

                    # Check each individual request task
                    for request_task_id in request_task_ids_in_progress:
                        try:
                            subtask_id = get_cached_task_id(request_task_id)
                        except Exception as cache_exc:
                            # If we can't get the subtask ID due to cache failure, fail safe by canceling
                            _cancel_interrupted_tasks_and_error_privacy_request(
                                db,
                                privacy_request,
                                f"Cache failure when getting subtask ID for request task {request_task_id} "
                                f"(privacy request {privacy_request.id}), failing safe by canceling tasks: {cache_exc}",
                            )
                            should_requeue = False
                            break

                        # If the task ID is not cached, we can't check if it's running
                        # This means the subtask is stuck - but we need to handle this differently
                        # based on the privacy request status
                        if not subtask_id:
                            if (
                                privacy_request.status
                                == PrivacyRequestStatus.requires_input
                            ):
                                # For requires_input status, don't automatically error the request
                                # as it's intentionally waiting for user input
                                logger.warning(
                                    f"No task ID found for request task {request_task_id} "
                                    f"(privacy request {privacy_request.id}) in requires_input status - "
                                    f"keeping request in current status as it may be waiting for manual input"
                                )
                                should_requeue = False
                                break

                            # Check if the Privacy request has polling tasks
                            if _has_polling_tasks(db, privacy_request.id):
                                # If the polling request task has no cached task ID, it's stuck
                                logger.warning(
                                    f"No task ID found for request task {request_task_id} "
                                    f"(privacy request {privacy_request.id}) Contains polling tasks - "
                                    f"keeping request in current status as it may be waiting for polling task to complete"
                                )
                                should_requeue = False
                                break

                            # For other statuses, cancel the entire privacy request
                            _cancel_interrupted_tasks_and_error_privacy_request(
                                db,
                                privacy_request,
                                f"No task ID found for request task {request_task_id} "
                                f"(privacy request {privacy_request.id}), subtask is stuck - canceling privacy request",
                            )
                            should_requeue = False
                            break

                        if (
                            subtask_id not in queued_tasks_ids
                            and not celery_tasks_in_flight([subtask_id])
                        ):
                            logger.warning(
                                f"Request task {request_task_id} is not in the queue or running, requeueing privacy request"
                            )
                            should_requeue = True
                            break

                # Requeue the privacy request if needed
                if should_requeue:
                    _handle_privacy_request_requeue(db, privacy_request)


@celery_app.task(base=DatabaseTask, bind=True)
def requeue_polling_tasks(self: DatabaseTask) -> None:
    """
    Poll the status of async tasks that are awaiting processing.
    """
    with redis_lock(
        ASYNC_TASKS_STATUS_POLLING_LOCK,
        ASYNC_TASKS_STATUS_POLLING_LOCK_TIMEOUT,
    ) as lock:
        if not lock:
            logger.debug("Async tasks status polling lock not acquired, skipping")
            return
        with self.get_new_session() as db:
            logger.debug("Polling for async tasks status")

            # Get all tasks that are polling and are from polling async tasks
            async_tasks = (
                db.query(RequestTask)
                .filter(RequestTask.status == ExecutionLogStatus.polling)
                .filter(RequestTask.async_type == AsyncTaskType.polling)
                .all()
            )
            logger.info(f"Found {len(async_tasks)} async polling tasks")

            if async_tasks:
                # Avoiding cyclic imports
                from fides.api.task.execute_request_tasks import queue_request_task

                for async_task in async_tasks:
                    logger.info(
                        f"Requeuing polling task {async_task.id} for processing"
                    )
                    queue_request_task(async_task, privacy_request_proceed=True)
