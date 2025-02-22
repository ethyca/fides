from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Query
from sqlalchemy.sql.elements import TextClause

from fides.api.common_exceptions import PrivacyRequestNotFound
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import (
    EXITED_EXECUTION_LOG_STATUSES,
    ExecutionLogStatus,
    PrivacyRequest,
    PrivacyRequestStatus,
)
from fides.api.schemas.drp_privacy_request import DrpPrivacyRequestCreate
from fides.api.schemas.masking.masking_secrets import MaskingSecretCache
from fides.api.schemas.policy import ActionType
from fides.api.schemas.redis_cache import Identity
from fides.api.service.masking.strategy.masking_strategy import MaskingStrategy
from fides.api.task.queue_task import queue_request_task
from fides.api.tasks import DatabaseTask, celery_app
from fides.api.tasks.scheduled.scheduler import scheduler
from fides.api.util.cache import (
    FidesopsRedis,
    celery_tasks_in_flight,
    get_async_task_tracking_cache_key,
    get_cache,
)
from fides.config import CONFIG

PRIVACY_REQUEST_STATUS_CHANGE_POLL = "privacy_request_status_change_poll"
DSR_DATA_REMOVAL = "dsr_data_removal"
INTERRUPTED_TASK_REQUEUE_POLL = "interrupted_task_requeue_poll"


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
    policy: Policy,
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

    # Store masking secrets in the cache
    logger.info("Caching masking secrets for privacy request {}", privacy_request.id)
    erasure_rules = policy.get_rules_for_action(action_type=ActionType.erasure)
    unique_masking_strategies_by_name: Set[str] = set()
    for rule in erasure_rules:
        strategy_name: str = rule.masking_strategy["strategy"]  # type: ignore
        configuration = rule.masking_strategy["configuration"]  # type: ignore
        if strategy_name in unique_masking_strategies_by_name:
            continue
        unique_masking_strategies_by_name.add(strategy_name)
        masking_strategy = MaskingStrategy.get_strategy(strategy_name, configuration)
        if masking_strategy.secrets_required():
            masking_secrets: List[MaskingSecretCache] = (
                masking_strategy.generate_secrets_for_cache()
            )
            for masking_secret in masking_secrets:
                privacy_request.cache_masking_secret(masking_secret)
    if drp_request_body:
        privacy_request.cache_drp_request_body(drp_request_body)


def get_async_client() -> AsyncClient:
    """Return an async client used to make API requests"""
    return AsyncClient()


async def poll_server_for_completion(
    privacy_request_id: str,
    server_url: str,
    token: str,
    *,
    poll_interval_seconds: int = 30,
    timeout_seconds: int = 1800,  # 30 minutes
    client: AsyncClient | None = None,
) -> PrivacyRequestResponse:
    """Poll a server for privacy request completion.

    Requests will report complete with if they have a status of canceled, complete,
    denied, or error. By default the polling will time out if not completed in 30
    minutes, time can be overridden by setting the timeout_seconds.
    """
    url = (
        f"{server_url}{V1_URL_PREFIX}{PRIVACY_REQUESTS}?request_id={privacy_request_id}"
    )
    start_time = datetime.now()
    elapsed_time = 0.0
    while elapsed_time < timeout_seconds:
        if client:
            response = await client.get(
                url, headers={"Authorization": f"Bearer {token}"}
            )
        else:
            async_client = get_async_client()
            response = await async_client.get(
                url, headers={"Authorization": f"Bearer {token}"}
            )
        response.raise_for_status()

        # Privacy requests are returned paginated. Since this is searching for a specific
        # privacy request there should only be one value present in items.
        items = response.json()["items"]
        if not items:
            raise PrivacyRequestNotFound(
                f"No privacy request found with id '{privacy_request_id}'"
            )
        status = PrivacyRequestResponse(**items[0])
        if status.status and status.status in (
            PrivacyRequestStatus.complete,
            PrivacyRequestStatus.canceled,
            PrivacyRequestStatus.error,
            PrivacyRequestStatus.denied,
        ):
            return status

        await sleep(poll_interval_seconds)
        time_delta = datetime.now() - start_time
        elapsed_time = time_delta.seconds
    raise TimeoutError(
        f"Timeout of {timeout_seconds} seconds has been exceeded while waiting for privacy request {privacy_request_id}"
    )


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
        in_progress_privacy_requests = (
            db.query(PrivacyRequest)
            .filter(
                PrivacyRequest.status.in_(
                    [PrivacyRequestStatus.in_processing, PrivacyRequestStatus.approved]
                )
            )
            # Only look at Privacy Requests that haven't been deleted
            .filter(PrivacyRequest.deleted_at.is_(None))
            .order_by(PrivacyRequest.created_at)
        )

        def some_errored(tasks: Query) -> bool:
            """All statuses have exited and at least one is errored"""
            statuses: List[ExecutionLogStatus] = [tsk.status for tsk in tasks]
            all_exited = all(
                status in EXITED_EXECUTION_LOG_STATUSES for status in statuses
            )
            return all_exited and ExecutionLogStatus.error in statuses

        marked_as_errored: Set[str] = set()
        for pr in in_progress_privacy_requests.all():
            if pr.consent_tasks.count():
                # Consent propagation tasks - these are not created until access and erasure steps are complete.
                if some_errored(pr.consent_tasks):
                    logger.info(f"Marking consent step of {pr.id} as error")
                    pr.error_processing(db)
                    marked_as_errored.add(pr.id)

            if pr.erasure_tasks.count():
                # Erasure tasks are created at the same time as access tasks but if any are errored, this means
                # we made it to the erasure section
                if some_errored(pr.erasure_tasks):
                    logger.info(f"Marking erasure step of {pr.id} as error")
                    pr.error_processing(db)
                    marked_as_errored.add(pr.id)

            if pr.access_tasks.count():
                if some_errored(pr.access_tasks):
                    logger.info(f"Marking access step of {pr.id} as error")
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
        coalesce=True,  # Only run one instance at a time
        replace_existing=True,
        seconds=CONFIG.execution.state_polling_interval,  # Reuse same interval as status change polling
    )


@celery_app.task(base=DatabaseTask, bind=True)
def requeue_interrupted_tasks(self: DatabaseTask) -> Dict[str, List[str]]:
    """
    Identifies and requeues tasks that were interrupted before completion.

    Looks for tasks that are:
    1. Marked as 'in_processing'
    2. Have a cached task_id
    3. Task is not actually running in Celery
    """
    with self.get_new_session() as db:
        logger.info("Starting check for interrupted tasks to requeue")

        # Get all in-progress privacy requests
        in_progress_requests = (
            db.query(PrivacyRequest)
            .filter(
                PrivacyRequest.status.in_(
                    [PrivacyRequestStatus.in_processing, PrivacyRequestStatus.approved]
                )
            )
            .filter(PrivacyRequest.deleted_at.is_(None))
            .order_by(PrivacyRequest.created_at)
        )

        results = {"requeued_tasks": [], "active_tasks": [], "state_cleaned": []}
        logger.info("Found {} privacy requests to check", in_progress_requests.count())

        for pr in in_progress_requests:
            logger.debug("Checking tasks for privacy request {}", pr.id)
            for task in pr.request_tasks:
                task_id = task.get_cached_task_id()
                logger.debug(
                    "Checking task {} (status: {}, cached_task_id: {})",
                    task.id,
                    task.status,
                    task_id,
                )

                if task.status == ExecutionLogStatus.in_processing and task_id:
                    # Check if task is still running
                    is_running = celery_tasks_in_flight([task_id])
                    logger.debug(
                        "Task {} is{} still running in Celery",
                        task.id,
                        "" if is_running else " not",
                    )

                    if not is_running:
                        # Clean up stale state
                        cache: FidesopsRedis = get_cache()
                        cache.delete(get_async_task_tracking_cache_key(task.id))
                        results["state_cleaned"].append(task.id)
                        logger.info("Cleaned stale state for task {}", task.id)

                        # Only requeue if upstream tasks are complete
                        if task.can_queue_request_task(db):
                            queue_request_task(task)
                            results["requeued_tasks"].append(task.id)
                            logger.info(
                                "Requeued interrupted task {} for privacy request {}",
                                task.id,
                                pr.id,
                            )
                        else:
                            logger.info(
                                "Task {} has incomplete upstream dependencies - not requeuing",
                                task.id,
                            )
                    else:
                        results["active_tasks"].append(task.id)

        logger.info(
            "Requeue check complete. Results: {} tasks requeued, {} tasks still active, {} states cleaned",
            len(results["requeued_tasks"]),
            len(results["active_tasks"]),
            len(results["state_cleaned"]),
        )
        return results
