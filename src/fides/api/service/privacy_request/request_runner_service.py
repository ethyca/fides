import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import requests
from loguru import logger
from pydantic import ValidationError
from sqlalchemy.orm import Query, Session

from fides.api import common_exceptions
from fides.api.common_exceptions import (
    ClientUnsuccessfulException,
    IdentityNotFoundException,
    ManualWebhookFieldsUnset,
    MessageDispatchException,
    NoCachedManualWebhookEntry,
    PrivacyRequestExit,
    PrivacyRequestPaused,
)
from fides.api.db.session import get_db_session
from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.connectionconfig import AccessLevel, ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.manual_webhook import AccessManualWebhook
from fides.api.models.policy import (
    CurrentStep,
    Policy,
    PolicyPostWebhook,
    PolicyPreWebhook,
    WebhookTypes,
)
from fides.api.models.privacy_request import (
    PrivacyRequest,
    PrivacyRequestStatus,
    ProvidedIdentityType,
    can_run_checkpoint,
)
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.messaging.messaging import (
    AccessRequestCompleteBodyParams,
    MessagingActionType,
)
from fides.api.schemas.policy import ActionType
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import FidesConnector, get_connector
from fides.api.service.connectors.consent_email_connector import (
    CONSENT_EMAIL_CONNECTOR_TYPES,
)
from fides.api.service.connectors.erasure_email_connector import (
    ERASURE_EMAIL_CONNECTOR_TYPES,
)
from fides.api.service.connectors.fides_connector import filter_fides_connector_datasets
from fides.api.service.messaging.message_dispatch_service import (
    dispatch_message,
    message_send_enabled,
)
from fides.api.service.storage.storage_uploader_service import upload
from fides.api.task.filter_results import filter_data_categories
from fides.api.task.graph_runners import access_runner, consent_runner, erasure_runner
from fides.api.task.graph_task import (
    build_consent_dataset_graph,
    filter_by_enabled_actions,
    get_cached_data_for_erasures,
)
from fides.api.tasks import DatabaseTask, celery_app
from fides.api.tasks.scheduled.scheduler import scheduler
from fides.api.util.cache import cache_task_tracking_key
from fides.api.util.collection_util import Row
from fides.api.util.logger import Pii, _log_exception, _log_warning
from fides.common.api.v1.urn_registry import (
    PRIVACY_REQUEST_TRANSFER_TO_PARENT,
    V1_URL_PREFIX,
)
from fides.config import CONFIG
from fides.config.config_proxy import ConfigProxy


class ManualWebhookResults(FidesSchema):
    """Represents manual webhook data retrieved from the cache and whether privacy request execution should continue"""

    manual_data: Dict[str, List[Dict[str, Optional[Any]]]]
    proceed: bool


def get_manual_webhook_access_inputs(
    db: Session, privacy_request: PrivacyRequest, policy: Policy
) -> ManualWebhookResults:
    """Retrieves manually uploaded data for all AccessManualWebhooks and formats in a way
    to match automatically retrieved data (a list of rows). Also returns if execution should proceed.

    This data will be uploaded to the user as-is, without filtering.
    """
    manual_inputs: Dict[str, List[Dict[str, Optional[Any]]]] = {}

    if not policy.get_rules_for_action(action_type=ActionType.access):
        # Don't fetch manual inputs unless this policy has an access rule
        return ManualWebhookResults(manual_data=manual_inputs, proceed=True)

    try:
        for manual_webhook in AccessManualWebhook.get_enabled(db, ActionType.access):
            manual_inputs[manual_webhook.connection_config.key] = [
                privacy_request.get_manual_webhook_access_input_strict(manual_webhook)
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


def get_manual_webhook_erasure_inputs(
    db: Session, privacy_request: PrivacyRequest, policy: Policy
) -> ManualWebhookResults:
    manual_inputs: Dict[str, List[Dict[str, Optional[Any]]]] = {}

    if not policy.get_rules_for_action(action_type=ActionType.erasure):
        # Don't fetch manual inputs unless this policy has an access rule
        return ManualWebhookResults(manual_data=manual_inputs, proceed=True)
    try:
        for manual_webhook in AccessManualWebhook().get_enabled(db, ActionType.erasure):
            manual_inputs[manual_webhook.connection_config.key] = [
                privacy_request.get_manual_webhook_erasure_input_strict(manual_webhook)
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
            privacy_request.trigger_policy_webhook(
                webhook=webhook,
                policy_action=privacy_request.policy.get_action_type(),
            )
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

    rule_filtered_results: Dict[str, Dict[str, List[Row]]] = {}
    for rule in policy.get_rules_for_action(  # pylint: disable=R1702
        action_type=ActionType.access
    ):
        storage_destination = rule.get_storage_destination(session)

        target_categories: Set[str] = {target.data_category for target in rule.targets}  # type: ignore[attr-defined]
        filtered_results: Dict[str, List[Dict[str, Optional[Any]]]] = (
            filter_data_categories(
                access_result,
                target_categories,
                dataset_graph,
                rule.key,
                fides_connector_datasets,
            )
        )

        filtered_results.update(
            manual_data
        )  # Add manual data directly to each upload packet
        rule_filtered_results[rule.key] = filtered_results

        logger.info(
            "Starting access request upload for rule {} for privacy request {}",
            rule.key,
            privacy_request.id,
        )
        try:
            download_url: Optional[str] = upload(
                db=session,
                privacy_request=privacy_request,
                data=filtered_results,
                storage_key=storage_destination.key,  # type: ignore
                data_category_field_mapping=dataset_graph.data_category_field_mapping,
                data_use_map=privacy_request.get_cached_data_use_map(),
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
    # Save the results we uploaded to the user for later retrieval
    privacy_request.save_filtered_access_results(session, rule_filtered_results)
    # Saving access request URL's on the privacy request in case DSR 3.0
    # exits processing before the email is sent
    privacy_request.access_result_urls = {"access_result_urls": download_urls}
    privacy_request.save(session)
    return download_urls


def queue_privacy_request(
    privacy_request_id: str,
    from_webhook_id: Optional[str] = None,
    from_step: Optional[str] = None,
) -> str:
    logger.info(
        "Queueing privacy request {} from step {}", privacy_request_id, from_step
    )
    task = run_privacy_request.delay(
        privacy_request_id=privacy_request_id,
        from_webhook_id=from_webhook_id,
        from_step=from_step,
    )
    cache_task_tracking_key(privacy_request_id, task.task_id)

    return task.task_id


@celery_app.task(base=DatabaseTask, bind=True)
def run_privacy_request(
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

    with self.get_new_session() as session:
        privacy_request = PrivacyRequest.get(db=session, object_id=privacy_request_id)
        if not privacy_request:
            raise common_exceptions.PrivacyRequestNotFound(
                f"Privacy request with id {privacy_request_id} not found"
            )

        if privacy_request.status == PrivacyRequestStatus.canceled:
            logger.info(
                "Terminating privacy request {}: request canceled.", privacy_request.id
            )
            return
        logger.info("Dispatching privacy request {}", privacy_request.id)
        privacy_request.start_processing(session)

        policy = privacy_request.policy

        # check manual access results and pause if needed
        manual_webhook_access_results: ManualWebhookResults = (
            get_manual_webhook_access_inputs(session, privacy_request, policy)
        )
        if not manual_webhook_access_results.proceed:
            return

        # check manual erasure results and pause if needed
        manual_webhook_erasure_results: ManualWebhookResults = (
            get_manual_webhook_erasure_inputs(session, privacy_request, policy)
        )
        if not manual_webhook_erasure_results.proceed:
            return

        # Pre-Webhooks CHECKPOINT
        if can_run_checkpoint(
            request_checkpoint=CurrentStep.pre_webhooks, from_checkpoint=resume_step
        ):
            privacy_request.cache_failed_checkpoint_details(CurrentStep.pre_webhooks)
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
            policy.rules[0]  # type: ignore[attr-defined]
        except IndexError:
            raise common_exceptions.MisconfiguredPolicyException(
                f"Policy with key {policy.key} must contain at least one Rule."
            )

        try:
            datasets = DatasetConfig.all(db=session)
            dataset_graphs = [dataset_config.get_graph() for dataset_config in datasets]
            dataset_graph = DatasetGraph(*dataset_graphs)
            identity_data = {
                key: value["value"] if isinstance(value, dict) else value
                for key, value in privacy_request.get_cached_identity_data().items()
            }
            connection_configs = ConnectionConfig.all(db=session)
            fides_connector_datasets: Set[str] = filter_fides_connector_datasets(
                connection_configs
            )

            # Access CHECKPOINT
            if (
                policy.get_rules_for_action(action_type=ActionType.access)
                or policy.get_rules_for_action(action_type=ActionType.erasure)
            ) and can_run_checkpoint(
                request_checkpoint=CurrentStep.access, from_checkpoint=resume_step
            ):
                privacy_request.cache_failed_checkpoint_details(CurrentStep.access)
                access_runner(
                    privacy_request=privacy_request,
                    policy=policy,
                    graph=dataset_graph,
                    connection_configs=connection_configs,
                    identity=identity_data,
                    session=session,
                    privacy_request_proceed=True,  # Should always be True unless we're testing
                )

            # Upload Access Results CHECKPOINT
            access_result_urls: List[str] = []
            raw_access_results: Dict = privacy_request.get_raw_access_results()
            if (
                policy.get_rules_for_action(action_type=ActionType.access)
                or policy.get_rules_for_action(
                    action_type=ActionType.erasure
                )  # Intentional to support requeuing the Privacy Request after the Access step for DSR 3.0 for both access/erasure requests
            ) and can_run_checkpoint(
                request_checkpoint=CurrentStep.upload_access,
                from_checkpoint=resume_step,
            ):
                privacy_request.cache_failed_checkpoint_details(
                    CurrentStep.upload_access
                )
                filtered_access_results = filter_by_enabled_actions(
                    raw_access_results, connection_configs
                )
                access_result_urls = upload_access_results(
                    session,
                    policy,
                    filtered_access_results,
                    dataset_graph,
                    privacy_request,
                    manual_webhook_access_results.manual_data,
                    fides_connector_datasets,
                )

            # Erasure CHECKPOINT
            if policy.get_rules_for_action(
                action_type=ActionType.erasure
            ) and can_run_checkpoint(
                request_checkpoint=CurrentStep.erasure, from_checkpoint=resume_step
            ):
                privacy_request.cache_failed_checkpoint_details(CurrentStep.erasure)
                # We only need to run the erasure once until masking strategies are handled
                erasure_runner(
                    privacy_request=privacy_request,
                    policy=policy,
                    graph=dataset_graph,
                    connection_configs=connection_configs,
                    identity=identity_data,
                    access_request_data=get_cached_data_for_erasures(
                        privacy_request.id
                    ),
                    session=session,
                    privacy_request_proceed=True,  # Should always be True unless we're testing
                )

            # Finalize Erasure CHECKPOINT
            if can_run_checkpoint(
                request_checkpoint=CurrentStep.finalize_erasure,
                from_checkpoint=resume_step,
            ):
                # This checkpoint allows a Privacy Request to be re-queued
                # after the Erasure Step is complete for DSR 3.0
                privacy_request.cache_failed_checkpoint_details(
                    CurrentStep.finalize_erasure
                )

            if policy.get_rules_for_action(
                action_type=ActionType.consent
            ) and can_run_checkpoint(
                request_checkpoint=CurrentStep.consent,
                from_checkpoint=resume_step,
            ):
                privacy_request.cache_failed_checkpoint_details(CurrentStep.consent)
                consent_runner(
                    privacy_request=privacy_request,
                    policy=policy,
                    graph=build_consent_dataset_graph(datasets),
                    connection_configs=connection_configs,
                    identity=identity_data,
                    session=session,
                    privacy_request_proceed=True,  # Should always be True unless we're testing
                )

            # Finalize Consent CHECKPOINT
            if can_run_checkpoint(
                request_checkpoint=CurrentStep.finalize_consent,
                from_checkpoint=resume_step,
            ):
                # This checkpoint allows a Privacy Request to be re-queued
                # after the Consent Step is complete for DSR 3.0
                privacy_request.cache_failed_checkpoint_details(
                    CurrentStep.finalize_consent
                )

        except PrivacyRequestPaused as exc:
            privacy_request.pause_processing(session)
            _log_warning(exc, CONFIG.dev_mode)
            return

        except PrivacyRequestExit:
            # Privacy Request Exiting awaiting sub task processing (Request Tasks)
            # The access, consent, and erasure runners for DSR 3.0 throw this exception after its
            # Request Tasks have been built.  The Privacy Request will be requeued from
            # the appropriate checkpoint when all the Request Tasks have run.
            return

        except BaseException as exc:  # pylint: disable=broad-except
            privacy_request.error_processing(db=session)
            # If dev mode, log traceback
            _log_exception(exc, CONFIG.dev_mode)
            return

        # Check if privacy request needs erasure or consent emails sent
        # Email post-send CHECKPOINT
        if (
            (
                policy.get_rules_for_action(action_type=ActionType.erasure)
                or policy.get_rules_for_action(action_type=ActionType.consent)
            )
            and can_run_checkpoint(
                request_checkpoint=CurrentStep.email_post_send,
                from_checkpoint=resume_step,
            )
            and needs_batch_email_send(session, identity_data, privacy_request)
        ):
            privacy_request.cache_failed_checkpoint_details(CurrentStep.email_post_send)
            privacy_request.pause_processing_for_email_send(session)
            logger.info(
                "Privacy request '{}' exiting: awaiting email send.",
                privacy_request.id,
            )
            return

        # Post Webhooks CHECKPOINT
        if can_run_checkpoint(
            request_checkpoint=CurrentStep.post_webhooks,
            from_checkpoint=resume_step,
        ):
            privacy_request.cache_failed_checkpoint_details(CurrentStep.post_webhooks)
            proceed = run_webhooks_and_report_status(
                db=session,
                privacy_request=privacy_request,
                webhook_cls=PolicyPostWebhook,  # type: ignore
            )
            if not proceed:
                return

        legacy_request_completion_enabled = ConfigProxy(
            session
        ).notifications.send_request_completion_notification

        action_type = (
            MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS
            if policy.get_rules_for_action(action_type=ActionType.access)
            else MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION
        )

        if message_send_enabled(
            session,
            privacy_request.property_id,
            action_type,
            legacy_request_completion_enabled,
        ) and not policy.get_rules_for_action(action_type=ActionType.consent):
            try:
                if not access_result_urls:
                    # For DSR 3.0, if the request had both access and erasure rules, this needs to be fetched
                    # from the database because the Privacy Request would have exited
                    # processing and lost access to the access_result_urls in memory
                    access_result_urls = (privacy_request.access_result_urls or {}).get(
                        "access_result_urls", []
                    )
                initiate_privacy_request_completion_email(
                    session,
                    policy,
                    access_result_urls,
                    identity_data,
                    privacy_request.property_id,
                )
            except (IdentityNotFoundException, MessageDispatchException) as e:
                privacy_request.error_processing(db=session)
                # If dev mode, log traceback
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
    property_id: Optional[str],
) -> None:
    """
    :param session: SQLAlchemy Session
    :param policy: Policy
    :param access_result_urls: list of urls generated by access request upload
    :param identity_data: Dict of identity data
    :param property_id: Property id associated with the privacy request
    """
    config_proxy = ConfigProxy(session)
    if not (
        identity_data.get(ProvidedIdentityType.email.value)
        or identity_data.get(ProvidedIdentityType.phone_number.value)
    ):
        raise IdentityNotFoundException(
            "Identity email or phone number was not found, so request completion message could not be sent."
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
            service_type=config_proxy.notifications.notification_service_type,
            message_body_params=AccessRequestCompleteBodyParams(
                download_links=access_result_urls,
                subject_request_download_time_in_days=CONFIG.security.subject_request_download_link_ttl_seconds
                / 86400,
            ),
            property_id=property_id,
        )
    if policy.get_rules_for_action(action_type=ActionType.erasure):
        dispatch_message(
            db=session,
            action_type=MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION,
            to_identity=to_identity,
            service_type=config_proxy.notifications.notification_service_type,
            message_body_params=None,
            property_id=property_id,
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
    return str(secrets.choice(range(100000, 999999)))


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
        privacy_request_id = None
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


def get_consent_email_connection_configs(db: Session) -> Query:
    """Return enabled consent email connection configs."""
    return db.query(ConnectionConfig).filter(
        ConnectionConfig.connection_type.in_(CONSENT_EMAIL_CONNECTOR_TYPES),
        ConnectionConfig.disabled.is_(False),
        ConnectionConfig.access == AccessLevel.write,
    )


def get_erasure_email_connection_configs(db: Session) -> Query:
    """Return enabled erasure email connection configs."""
    return db.query(ConnectionConfig).filter(
        ConnectionConfig.connection_type.in_(ERASURE_EMAIL_CONNECTOR_TYPES),
        ConnectionConfig.disabled.is_(False),
        ConnectionConfig.access == AccessLevel.write,
    )


def needs_batch_email_send(
    db: Session, user_identities: Dict[str, Any], privacy_request: PrivacyRequest
) -> bool:
    """
    Delegates the "needs email" check to each configured email or
    generic email consent connector. Returns true if at least one
    connector needs to send an email.

    If we don't need to send any emails, add skipped logs for any
    relevant erasure and consent email connectors.
    """
    can_skip_erasure_email: List[ConnectionConfig] = []
    can_skip_consent_email: List[ConnectionConfig] = []

    needs_email_send: bool = False

    for connection_config in get_erasure_email_connection_configs(db):
        if get_connector(connection_config).needs_email(  # type: ignore
            user_identities, privacy_request
        ):
            needs_email_send = True
        else:
            can_skip_erasure_email.append(connection_config)

    for connection_config in get_consent_email_connection_configs(db):
        if get_connector(connection_config).needs_email(  # type: ignore
            user_identities, privacy_request
        ):
            needs_email_send = True
        else:
            can_skip_consent_email.append(connection_config)

    if not needs_email_send:
        _create_execution_logs_for_skipped_email_send(
            db, privacy_request, can_skip_erasure_email, can_skip_consent_email
        )

    return needs_email_send


def _create_execution_logs_for_skipped_email_send(
    db: Session,
    privacy_request: PrivacyRequest,
    can_skip_erasure_email: List[ConnectionConfig],
    can_skip_consent_email: List[ConnectionConfig],
) -> None:
    """Create skipped execution logs for relevant connectors
    if this privacy request does not need an email send at all.  For consent requests,
    cache that the system was skipped on any privacy preferences for consent reporting.

    Otherwise, any needed skipped execution logs will be added later
    in the weekly email send.
    """
    for connection_config in can_skip_erasure_email:
        connector = get_connector(connection_config)
        connector.add_skipped_log(db, privacy_request)  # type: ignore[attr-defined]

    for connection_config in can_skip_consent_email:
        connector = get_connector(connection_config)
        connector.add_skipped_log(db, privacy_request)  # type: ignore[attr-defined]
