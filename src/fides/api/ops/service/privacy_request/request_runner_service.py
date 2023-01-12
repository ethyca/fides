import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import requests
from loguru import logger
from pydantic import ValidationError
from redis.exceptions import DataError
from sqlalchemy.orm import Session

from fides.api.ops import common_exceptions
from fides.api.ops.api.v1.urn_registry import (
    PRIVACY_REQUEST_TRANSFER_TO_PARENT,
    V1_URL_PREFIX,
)
from fides.api.ops.common_exceptions import (
    ClientUnsuccessfulException,
    IdentityNotFoundException,
    ManualWebhookFieldsUnset,
    MessageDispatchException,
    NoCachedManualWebhookEntry,
    PrivacyRequestPaused,
)
from fides.api.ops.graph.analytics_events import (
    failed_graph_analytics_event,
    fideslog_graph_failure,
)
from fides.api.ops.graph.config import CollectionAddress
from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.models.manual_webhook import AccessManualWebhook
from fides.api.ops.models.policy import (
    ActionType,
    CurrentStep,
    Policy,
    PolicyPostWebhook,
    PolicyPreWebhook,
    WebhookTypes,
)
from fides.api.ops.models.privacy_request import (
    PrivacyRequest,
    PrivacyRequestStatus,
    ProvidedIdentityType,
    can_run_checkpoint,
)
from fides.api.ops.schemas.messaging.messaging import (
    AccessRequestCompleteBodyParams,
    MessagingActionType,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import FidesConnector
from fides.api.ops.service.connectors.email_connector import (
    email_connector_erasure_send,
)
from fides.api.ops.service.connectors.fides_connector import (
    filter_fides_connector_datasets,
)
from fides.api.ops.service.messaging.message_dispatch_service import dispatch_message
from fides.api.ops.service.storage.storage_uploader_service import upload
from fides.api.ops.task.filter_results import filter_data_categories
from fides.api.ops.task.graph_task import (
    get_cached_data_for_erasures,
    run_access_request,
    run_erasure,
)
from fides.api.ops.tasks import DatabaseTask, celery_app
from fides.api.ops.tasks.scheduled.scheduler import scheduler
from fides.api.ops.util.cache import (
    FidesopsRedis,
    get_async_task_tracking_cache_key,
    get_cache,
)
from fides.api.ops.util.collection_util import Row
from fides.api.ops.util.logger import Pii, _log_exception, _log_warning
from fides.api.ops.util.wrappers import sync
from fides.core.config import get_config
from fides.lib.db.session import get_db_session
from fides.lib.models.audit_log import AuditLog, AuditLogAction
from fides.lib.schemas.base_class import BaseSchema

CONFIG = get_config()


class ManualWebhookResults(BaseSchema):
    """Represents manual webhook data retrieved from the cache and whether privacy request execution should continue"""

    manual_data: Dict[str, List[Dict[str, Optional[Any]]]]
    proceed: bool


def get_access_manual_webhook_inputs(
    db: Session, privacy_request: PrivacyRequest, policy: Policy
) -> ManualWebhookResults:

    """Retrieves manually uploaded data for all AccessManualWebhooks and formats in a way
    to match automatically retrieved data (a list of rows). Also returns if execution should proceed.

    This data will be uploaded to the user as-is, without filtering.
    """
    manual_inputs: Dict[str, List[Dict[str, Optional[Any]]]] = {}

    if not policy.get_rules_for_action(action_type=ActionType.access):
        # Don't fetch manual inputs if this is an erasure-only request
        return ManualWebhookResults(manual_data=manual_inputs, proceed=True)

    try:
        for manual_webhook in AccessManualWebhook.get_enabled(db):
            manual_inputs[manual_webhook.connection_config.key] = [
                privacy_request.get_manual_webhook_input_strict(manual_webhook)
            ]
    except (
        NoCachedManualWebhookEntry,
        ValidationError,
        ManualWebhookFieldsUnset,
    ) as exc:
        logger.info(exc)
        privacy_request.status = PrivacyRequestStatus.requires_input
        privacy_request.save(db)
        return ManualWebhookResults(manual_data=manual_inputs, proceed=False)

    return ManualWebhookResults(manual_data=manual_inputs, proceed=True)


def run_webhooks_and_report_status(
    db: Session,
    privacy_request: PrivacyRequest,
    webhook_cls: WebhookTypes,
    after_webhook_id: Optional[str] = None,
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
        webhooks = webhooks.filter(  # type: ignore[call-arg]
            webhook_cls.order > pre_webhook.order,  # type: ignore[union-attr]
        )

    current_step = CurrentStep[f"{webhook_cls.prefix}_webhooks"]

    for webhook in webhooks.order_by(webhook_cls.order):  # type: ignore[union-attr]
        try:
            privacy_request.trigger_policy_webhook(webhook)
        except PrivacyRequestPaused:
            logger.info(
                "Pausing execution of privacy request {}. Halt instruction received from webhook {}.",
                privacy_request.id,
                webhook.key,
            )
            privacy_request.pause_processing(db)
            initiate_paused_privacy_request_followup(privacy_request)
            return False
        except ClientUnsuccessfulException as exc:
            logger.error(
                "Privacy Request '{}' exited after response from webhook '{}': {}.",
                privacy_request.id,
                webhook.key,
                Pii(str(exc.args[0])),
            )
            privacy_request.error_processing(db)
            privacy_request.cache_failed_checkpoint_details(current_step)
            return False
        except ValidationError:
            logger.error(
                "Privacy Request '{}' errored due to response validation error from webhook '{}'.",
                privacy_request.id,
                webhook.key,
            )
            privacy_request.error_processing(db)
            privacy_request.cache_failed_checkpoint_details(current_step)
            return False

    return True


def upload_access_results(  # pylint: disable=R0912
    session: Session,
    policy: Policy,
    access_result: Dict[str, List[Row]],
    dataset_graph: DatasetGraph,
    privacy_request: PrivacyRequest,
    manual_data: Dict[str, List[Dict[str, Optional[Any]]]],
    fides_connector_datasets: Set[str],
) -> List[str]:
    """Process the data uploads after the access portion of the privacy request has completed"""
    download_urls: List[str] = []
    if not access_result:
        logger.info("No results returned for access request {}", privacy_request.id)

    for rule in policy.get_rules_for_action(  # pylint: disable=R1702
        action_type=ActionType.access
    ):
        if not rule.storage_destination:
            raise common_exceptions.RuleValidationError(
                f"No storage destination configured on rule {rule.key}"
            )
        target_categories: Set[str] = {target.data_category for target in rule.targets}  # type: ignore[attr-defined]
        filtered_results: Dict[
            str, List[Dict[str, Optional[Any]]]
        ] = filter_data_categories(
            access_result,
            target_categories,
            dataset_graph.data_category_field_mapping,
            rule.key,
            fides_connector_datasets,
        )

        filtered_results.update(
            manual_data
        )  # Add manual data directly to each upload packet

        logger.info(
            "Starting access request upload for rule {} for privacy request {}",
            rule.key,
            privacy_request.id,
        )
        try:
            download_url: Optional[str] = upload(
                db=session,
                request_id=privacy_request.id,
                data=filtered_results,
                storage_key=rule.storage_destination.key,  # type: ignore
            )
            if download_url:
                download_urls.append(download_url)
        except common_exceptions.StorageUploadError as exc:
            logger.error(
                "Error uploading subject access data for rule {} on policy {} and privacy request {} : {}",
                rule.key,
                policy.key,
                privacy_request.id,
                Pii(str(exc)),
            )
            privacy_request.status = PrivacyRequestStatus.error

    return download_urls


def queue_privacy_request(
    privacy_request_id: str,
    from_webhook_id: Optional[str] = None,
    from_step: Optional[str] = None,
) -> str:
    cache: FidesopsRedis = get_cache()
    logger.info("queueing privacy request")
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
            "Error tracking task_id for request with id {}", privacy_request_id
        )

    return task.task_id


@celery_app.task(base=DatabaseTask, bind=True)
@sync
async def run_privacy_request(
    self: DatabaseTask,
    privacy_request_id: str,
    from_webhook_id: Optional[str] = None,
    from_step: Optional[str] = None,
) -> None:
    # pylint: disable=too-many-statements, too-many-return-statements, too-many-branches
    """
    Dispatch a privacy_request into the execution layer by:
        1. Generate a graph from all the currently configured datasets
        2. Take the provided identity data
        3. Start the access request / erasure request execution
        4. When finished, upload the results to the configured storage destination if applicable

    Celery does not like for the function to be async so the @sync decorator runs the
    coroutine for it.
    """
    resume_step: Optional[CurrentStep] = CurrentStep(from_step) if from_step else None  # type: ignore
    if from_step:
        logger.info("Resuming privacy request from checkpoint: '{}'", from_step)

    with self.session as session:
        privacy_request = PrivacyRequest.get(db=session, object_id=privacy_request_id)

        privacy_request.cache_failed_checkpoint_details()  # Reset failed step and collection to None

        if privacy_request.status == PrivacyRequestStatus.canceled:
            logger.info(
                "Terminating privacy request {}: request canceled.", privacy_request.id
            )
            return
        logger.info("Dispatching privacy request {}", privacy_request.id)
        privacy_request.start_processing(session)

        policy = privacy_request.policy
        manual_webhook_results: ManualWebhookResults = get_access_manual_webhook_inputs(
            session, privacy_request, policy
        )
        if not manual_webhook_results.proceed:
            return

        if can_run_checkpoint(
            request_checkpoint=CurrentStep.pre_webhooks, from_checkpoint=resume_step
        ):
            # Run pre-execution webhooks
            proceed = run_webhooks_and_report_status(
                session,
                privacy_request=privacy_request,
                webhook_cls=PolicyPreWebhook,  # type: ignore
                after_webhook_id=from_webhook_id,
            )
            if not proceed:
                return
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
            fides_connector_datasets: Set[str] = filter_fides_connector_datasets(
                connection_configs
            )
            access_result_urls: List[str] = []

            if can_run_checkpoint(
                request_checkpoint=CurrentStep.access, from_checkpoint=resume_step
            ):
                access_result: Dict[str, List[Row]] = await run_access_request(
                    privacy_request=privacy_request,
                    policy=policy,
                    graph=dataset_graph,
                    connection_configs=connection_configs,
                    identity=identity_data,
                    session=session,
                )
                access_result_urls = upload_access_results(
                    session,
                    policy,
                    access_result,
                    dataset_graph,
                    privacy_request,
                    manual_webhook_results.manual_data,
                    fides_connector_datasets,
                )

            if policy.get_rules_for_action(
                action_type=ActionType.erasure
            ) and can_run_checkpoint(
                request_checkpoint=CurrentStep.erasure, from_checkpoint=resume_step
            ):
                # We only need to run the erasure once until masking strategies are handled
                await run_erasure(
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
            _log_warning(exc, CONFIG.dev_mode)
            return

        except BaseException as exc:  # pylint: disable=broad-except
            privacy_request.error_processing(db=session)
            # Send analytics to Fideslog
            await fideslog_graph_failure(
                failed_graph_analytics_event(privacy_request, exc)
            )
            # If dev mode, log traceback
            _log_exception(exc, CONFIG.dev_mode)
            return

        # Send erasure requests via email to third parties where applicable
        if can_run_checkpoint(
            request_checkpoint=CurrentStep.erasure_email_post_send,
            from_checkpoint=resume_step,
        ):
            try:
                email_connector_erasure_send(
                    db=session, privacy_request=privacy_request
                )
            except MessageDispatchException as exc:
                privacy_request.cache_failed_checkpoint_details(
                    step=CurrentStep.erasure_email_post_send, collection=None
                )
                privacy_request.error_processing(db=session)
                await fideslog_graph_failure(
                    failed_graph_analytics_event(privacy_request, exc)
                )
                # If dev mode, log traceback
                _log_exception(exc, CONFIG.dev_mode)
                return

        # Run post-execution webhooks
        proceed = run_webhooks_and_report_status(
            db=session,
            privacy_request=privacy_request,
            webhook_cls=PolicyPostWebhook,  # type: ignore
        )
        if not proceed:
            return
        if CONFIG.notifications.send_request_completion_notification:
            try:
                initiate_privacy_request_completion_email(
                    session, policy, access_result_urls, identity_data
                )
            except (IdentityNotFoundException, MessageDispatchException) as e:
                privacy_request.error_processing(db=session)
                # If dev mode, log traceback
                await fideslog_graph_failure(
                    failed_graph_analytics_event(privacy_request, e)
                )
                _log_exception(e, CONFIG.dev_mode)
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
        logger.info("Privacy request {} run completed.", privacy_request.id)
        privacy_request.save(db=session)


def initiate_privacy_request_completion_email(
    session: Session,
    policy: Policy,
    access_result_urls: List[str],
    identity_data: Dict[str, Any],
) -> None:
    """
    :param session: SQLAlchemy Session
    :param policy: Policy
    :param access_result_urls: list of urls generated by access request upload
    :param identity_data: Dict of identity data
    """
    if not identity_data.get(ProvidedIdentityType.email.value):
        raise IdentityNotFoundException(
            "Identity email was not found, so request completion email could not be sent."
        )
    to_identity: Identity = Identity(
        email=identity_data.get(ProvidedIdentityType.email.value),
        phone_number=identity_data.get(ProvidedIdentityType.phone_number.value),
    )
    if policy.get_rules_for_action(action_type=ActionType.access):
        # synchronous for now since failure to send complete emails is fatal to request
        dispatch_message(
            db=session,
            action_type=MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS,
            to_identity=to_identity,
            service_type=CONFIG.notifications.notification_service_type,
            message_body_params=AccessRequestCompleteBodyParams(
                download_links=access_result_urls
            ),
        )
    if policy.get_rules_for_action(action_type=ActionType.erasure):
        dispatch_message(
            db=session,
            action_type=MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION,
            to_identity=to_identity,
            service_type=CONFIG.notifications.notification_service_type,
            message_body_params=None,
        )


def initiate_paused_privacy_request_followup(privacy_request: PrivacyRequest) -> None:
    """Initiates scheduler to expire privacy request when the redis cache expires"""
    scheduler.add_job(
        func=mark_paused_privacy_request_as_expired,
        kwargs={"privacy_request_id": privacy_request.id},
        id=privacy_request.id,
        replace_existing=True,
        trigger="date",
        run_date=(datetime.now() + timedelta(seconds=CONFIG.redis.default_ttl_seconds)),
    )


def mark_paused_privacy_request_as_expired(privacy_request_id: str) -> None:
    """Mark "paused" PrivacyRequest as "errored" after its associated identity data in the redis cache has expired."""
    SessionLocal = get_db_session(CONFIG)
    db = SessionLocal()
    privacy_request = PrivacyRequest.get(db=db, object_id=privacy_request_id)
    if not privacy_request:
        logger.info(
            "Attempted to mark as expired. No privacy request with id '{}' found.",
            privacy_request_id,
        )
        db.close()
        return
    if privacy_request.status == PrivacyRequestStatus.paused:
        logger.error(
            "Privacy request '{}' has expired. Please resubmit information.",
            privacy_request.id,
        )
        privacy_request.error_processing(db=db)
    db.close()


def generate_id_verification_code() -> str:
    """
    Generate one-time identity verification code
    """
    return str(random.choice(range(100000, 999999)))


def _retrieve_child_results(  # pylint: disable=R0911
    fides_connector: Tuple[str, ConnectionConfig],
    rule_key: str,
    access_result: Dict[str, List[Row]],
) -> Optional[List[Dict[str, Optional[List[Row]]]]]:
    """Get child access request results to add to upload."""
    try:
        connector = FidesConnector(fides_connector[1])
    except Exception as e:
        logger.error(
            "Error create client for child server {}: {}", fides_connector[0], e
        )
        return None

    results = []

    for key, rows in access_result.items():
        address = CollectionAddress.from_string(key)
        if address.dataset == fides_connector[0]:
            if not rows:
                logger.info("No rows found for result entry {}", key)
                continue
            privacy_request_id = rows[0]["id"]

        if not privacy_request_id:
            logger.error(
                "No privacy request found for connector key {}", fides_connector[0]
            )
            continue

        try:
            client = connector.create_client()
        except requests.exceptions.HTTPError as e:
            logger.error(
                "Error logger into to child server for privacy request {}: {}",
                privacy_request_id,
                e,
            )
            continue

        try:
            request = client.authenticated_request(
                method="get",
                path=f"{V1_URL_PREFIX}{PRIVACY_REQUEST_TRANSFER_TO_PARENT.format(privacy_request_id=privacy_request_id, rule_key=rule_key)}",
                headers={"Authorization": f"Bearer {client.token}"},
            )
            response = client.session.send(request)
        except requests.exceptions.HTTPError as e:
            logger.error(
                "Error retrieving data from child server for privacy request {}: {}",
                privacy_request_id,
                e,
            )
            continue

        if response.status_code != 200:
            logger.error(
                "Error retrieving data from child server for privacy request {}: {}",
                privacy_request_id,
                response.json(),
            )
            continue

        results.append(response.json())

    if not results:
        return None

    return results
