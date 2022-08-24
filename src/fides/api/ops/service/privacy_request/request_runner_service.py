import logging
import random
from datetime import datetime, timedelta
from typing import ContextManager, Dict, List, Optional, Set

from celery import Task
from celery.utils.log import get_task_logger
from fideslib.db.session import get_db_session
from fideslib.models.audit_log import AuditLog, AuditLogAction
from pydantic import ValidationError
from redis.exceptions import DataError
from sqlalchemy.orm import Session

from fides.api.ops import common_exceptions
from fides.api.ops.common_exceptions import (
    ClientUnsuccessfulException,
    PrivacyRequestPaused,
)
from fides.api.ops.core.config import config
from fides.api.ops.graph.analytics_events import (
    failed_graph_analytics_event,
    fideslog_graph_failure,
)
from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.models.policy import (
    ActionType,
    PausedStep,
    Policy,
    PolicyPostWebhook,
    PolicyPreWebhook,
    WebhookTypes,
)
from fides.api.ops.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fides.api.ops.service.storage.storage_uploader_service import upload
from fides.api.ops.task.filter_results import filter_data_categories
from fides.api.ops.task.graph_task import (
    get_cached_data_for_erasures,
    run_access_request,
    run_erasure,
)
from fides.api.ops.tasks import celery_app
from fides.api.ops.tasks.scheduled.scheduler import scheduler
from fides.api.ops.util.cache import (
    FidesopsRedis,
    get_async_task_tracking_cache_key,
    get_cache,
)
from fidesops.ops.util.collection_util import Row
from fidesops.ops.util.logger import Pii, _log_exception, _log_warning

logger = get_task_logger(__name__)


def run_webhooks_and_report_status(
    db: Session,
    privacy_request: PrivacyRequest,
    webhook_cls: WebhookTypes,
    after_webhook_id: str = None,
) -> bool:
    """
    Runs a series of webhooks either pre- or post- privacy request execution, if any are configured.
    Updates privacy request status if execution is paused/errored.
    Returns True if execution should proceed.
    """
    webhooks = db.query(webhook_cls).filter_by(policy_id=privacy_request.policy.id)  # type: ignore

    if after_webhook_id:
        # Only run webhooks configured to run after this Pre-Execution webhook
        pre_webhook = PolicyPreWebhook.get(db=db, object_id=after_webhook_id)
        webhooks = webhooks.filter(
            webhook_cls.order > pre_webhook.order,
        )

    for webhook in webhooks.order_by(webhook_cls.order):
        try:
            privacy_request.trigger_policy_webhook(webhook)
        except PrivacyRequestPaused:
            logging.info(
                "Pausing execution of privacy request %s. Halt instruction received from webhook %s.",
                privacy_request.id,
                webhook.key,
            )
            privacy_request.pause_processing(db)
            initiate_paused_privacy_request_followup(privacy_request)
            return False
        except ClientUnsuccessfulException as exc:
            logging.error(
                "Privacy Request '%s' exited after response from webhook '%s': %s.",
                privacy_request.id,
                webhook.key,
                Pii(str(exc.args[0])),
            )
            privacy_request.error_processing(db)
            return False
        except ValidationError:
            logging.error(
                "Privacy Request '%s' errored due to response validation error from webhook '%s'.",
                privacy_request.id,
                webhook.key,
            )
            privacy_request.error_processing(db)
            return False

    return True


def upload_access_results(
    session: Session,
    policy: Policy,
    access_result: Dict[str, List[Row]],
    dataset_graph: DatasetGraph,
    privacy_request: PrivacyRequest,
) -> None:
    """Process the data uploads after the access portion of the privacy request has completed"""
    if not access_result:
        logging.info("No results returned for access request %s", privacy_request.id)

    for rule in policy.get_rules_for_action(action_type=ActionType.access):
        if not rule.storage_destination:
            raise common_exceptions.RuleValidationError(
                f"No storage destination configured on rule {rule.key}"
            )
        target_categories: Set[str] = {target.data_category for target in rule.targets}
        filtered_results = filter_data_categories(
            access_result,
            target_categories,
            dataset_graph.data_category_field_mapping,
        )
        logging.info(
            "Starting access request upload for rule %s for privacy request %s",
            rule.key,
            privacy_request.id,
        )
        try:
            upload(
                db=session,
                request_id=privacy_request.id,
                data=filtered_results,
                storage_key=rule.storage_destination.key,  # type: ignore
            )
        except common_exceptions.StorageUploadError as exc:
            logging.error(
                "Error uploading subject access data for rule %s on policy %s and privacy request %s : %s",
                rule.key,
                policy.key,
                privacy_request.id,
                Pii(str(exc)),
            )
            privacy_request.status = PrivacyRequestStatus.error


def queue_privacy_request(
    privacy_request_id: str,
    from_webhook_id: Optional[str] = None,
    from_step: Optional[str] = None,
) -> str:
    cache: FidesopsRedis = get_cache()
    task = run_privacy_request.delay(
        privacy_request_id=privacy_request_id,
        from_webhook_id=from_webhook_id,
        from_step=from_step,
    )
    try:
        cache.set(
            get_async_task_tracking_cache_key(privacy_request_id),
            task.task_id,
        )
    except DataError:
        logger.debug(
            "Error tracking task_id for request with id %s", privacy_request_id
        )

    return task.task_id


class DatabaseTask(Task):  # pylint: disable=W0223
    _session = None

    @property
    def session(self) -> ContextManager[Session]:
        """Creates Session once per process"""
        if self._session is None:
            SessionLocal = get_db_session(config)
            self._session = SessionLocal()

        return self._session


@celery_app.task(base=DatabaseTask, bind=True)
def run_privacy_request(
    self: DatabaseTask,
    privacy_request_id: str,
    from_webhook_id: Optional[str] = None,
    from_step: Optional[str] = None,
) -> None:
    # pylint: disable=too-many-locals
    """
    Dispatch a privacy_request into the execution layer by:
        1. Generate a graph from all the currently configured datasets
        2. Take the provided identity data
        3. Start the access request / erasure request execution
        4. When finished, upload the results to the configured storage destination if applicable
    """
    if from_step is not None:
        # Re-cast `from_step` into an Enum to enforce the validation since unserializable objects
        # can't be passed into and between tasks
        from_step = PausedStep(from_step)  # type: ignore

    with self.session as session:

        privacy_request = PrivacyRequest.get(db=session, object_id=privacy_request_id)
        if privacy_request.status == PrivacyRequestStatus.canceled:
            logging.info(
                "Terminating privacy request %s: request canceled.", privacy_request.id
            )
            return
        logging.info("Dispatching privacy request %s", privacy_request.id)
        privacy_request.start_processing(session)

        if not from_step:  # Skip if we're resuming from the access or erasure step.
            # Run pre-execution webhooks
            proceed = run_webhooks_and_report_status(
                session,
                privacy_request=privacy_request,
                webhook_cls=PolicyPreWebhook,  # type: ignore
                after_webhook_id=from_webhook_id,
            )
            if not proceed:
                return

        policy = privacy_request.policy
        try:
            policy.rules[0]
        except IndexError:
            raise common_exceptions.MisconfiguredPolicyException(
                f"Policy with key {policy.key} must contain at least one Rule."
            )

        try:
            datasets = DatasetConfig.all(db=session)
            dataset_graphs = [dataset_config.get_graph() for dataset_config in datasets]
            dataset_graph = DatasetGraph(*dataset_graphs)
            identity_data = privacy_request.get_cached_identity_data()
            connection_configs = ConnectionConfig.all(db=session)

            if (
                from_step != PausedStep.erasure
            ):  # Skip if we're resuming from erasure step
                access_result: Dict[str, List[Row]] = run_access_request(
                    privacy_request=privacy_request,
                    policy=policy,
                    graph=dataset_graph,
                    connection_configs=connection_configs,
                    identity=identity_data,
                    session=session,
                )

                upload_access_results(
                    session,
                    policy,
                    access_result,
                    dataset_graph,
                    privacy_request,
                )

            if policy.get_rules_for_action(action_type=ActionType.erasure):
                # We only need to run the erasure once until masking strategies are handled
                run_erasure(
                    privacy_request=privacy_request,
                    policy=policy,
                    graph=dataset_graph,
                    connection_configs=connection_configs,
                    identity=identity_data,
                    access_request_data=get_cached_data_for_erasures(
                        privacy_request.id
                    ),
                    session=session,
                )

        except PrivacyRequestPaused as exc:
            privacy_request.pause_processing(session)
            _log_warning(exc, config.dev_mode)
            return

        except BaseException as exc:  # pylint: disable=broad-except
            privacy_request.error_processing(db=session)
            # If dev mode, log traceback
            fideslog_graph_failure(failed_graph_analytics_event(privacy_request, exc))
            _log_exception(exc, config.dev_mode)
            return

        # Run post-execution webhooks
        proceed = run_webhooks_and_report_status(
            db=session,
            privacy_request=privacy_request,
            webhook_cls=PolicyPostWebhook,  # type: ignore
        )
        if not proceed:
            return

        privacy_request.finished_processing_at = datetime.utcnow()
        AuditLog.create(
            db=session,
            data={
                "user_id": "system",
                "privacy_request_id": privacy_request.id,
                "action": AuditLogAction.finished,
                "message": "",
            },
        )
        privacy_request.status = PrivacyRequestStatus.complete
        privacy_request.save(db=session)
        logging.info("Privacy request %s run completed.", privacy_request.id)


def initiate_paused_privacy_request_followup(privacy_request: PrivacyRequest) -> None:
    """Initiates scheduler to expire privacy request when the redis cache expires"""
    scheduler.add_job(
        func=mark_paused_privacy_request_as_expired,
        kwargs={"privacy_request_id": privacy_request.id},
        id=privacy_request.id,
        replace_existing=True,
        trigger="date",
        run_date=(datetime.now() + timedelta(seconds=config.redis.default_ttl_seconds)),
    )


def mark_paused_privacy_request_as_expired(privacy_request_id: str) -> None:
    """Mark "paused" PrivacyRequest as "errored" after its associated identity data in the redis cache has expired."""
    SessionLocal = get_db_session(config)
    db = SessionLocal()
    privacy_request = PrivacyRequest.get(db=db, object_id=privacy_request_id)
    if not privacy_request:
        logger.info(
            "Attempted to mark as expired. No privacy request with id '%s' found.",
            privacy_request_id,
        )
        db.close()
        return
    if privacy_request.status == PrivacyRequestStatus.paused:
        logger.error(
            "Privacy request '%s' has expired. Please resubmit information.",
            privacy_request.id,
        )
        privacy_request.error_processing(db=db)
    db.close()


def generate_id_verification_code() -> str:
    """
    Generate one-time identity verification code
    """
    return str(random.choice(range(100000, 999999)))
