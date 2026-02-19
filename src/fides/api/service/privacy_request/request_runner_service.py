from datetime import datetime
from typing import Any, Optional

from loguru import logger
from sqlalchemy.orm import Session, selectinload

from fides.api import common_exceptions
from fides.api.common_exceptions import (
    IdentityNotFoundException,
    MaskingSecretsExpired,
    MessageDispatchException,
    PrivacyRequestExit,
    PrivacyRequestPaused,
    ValidationError,
)
from fides.api.graph.graph import DatasetGraph
from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import Policy, PolicyPostWebhook, PolicyPreWebhook
from fides.api.models.privacy_request import PrivacyRequest, can_run_checkpoint
from fides.api.schemas.messaging.messaging import MessagingActionType
from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.connectors.fides_connector import filter_fides_connector_datasets
from fides.api.service.messaging.message_dispatch_service import message_send_enabled
from fides.api.service.privacy_request.access_result_service import (
    upload_and_save_access_results,
)
from fides.api.service.privacy_request.completion_notification_service import (
    initiate_consent_request_completion_email,
    initiate_privacy_request_completion_email,
)
from fides.api.service.privacy_request.duplication_detection import check_for_duplicates
from fides.api.service.privacy_request.email_batch_service import needs_batch_email_send
from fides.api.service.privacy_request.manual_webhook_service import (
    ManualWebhookResults,
    get_manual_webhook_access_inputs,
    get_manual_webhook_erasure_inputs,
)
from fides.api.service.privacy_request.webhook_execution_service import (
    run_webhooks_and_report_status,
)
from fides.api.task.graph_runners import access_runner, consent_runner, erasure_runner
from fides.api.task.graph_task import (
    build_consent_dataset_graph,
    filter_by_enabled_actions,
    get_cached_data_for_erasures,
)
from fides.api.task.manual.manual_task_utils import create_manual_task_artificial_graphs
from fides.api.tasks import DatabaseTask, celery_app
from fides.api.util.cache import get_all_masking_secret_keys
from fides.api.util.logger import _log_exception, _log_warning
from fides.api.util.logger_context_utils import LoggerContextKeys, log_context
from fides.api.util.memory_watchdog import memory_limiter
from fides.config import CONFIG
from fides.config.config_proxy import ConfigProxy


@celery_app.task(base=DatabaseTask, bind=True)
@memory_limiter
@log_context(capture_args={"privacy_request_id": LoggerContextKeys.privacy_request_id})
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
        with logger.contextualize(
            privacy_request_id=privacy_request_id,
        ):
            logger.info("Resuming privacy request from checkpoint: '{}'", from_step)

    with self.get_new_session() as session:
        privacy_request = (
            PrivacyRequest.query_without_large_columns(session)
            .filter(PrivacyRequest.id == privacy_request_id)
            .first()
        )
        if not privacy_request:
            raise common_exceptions.PrivacyRequestNotFound(
                f"Privacy request with id {privacy_request_id} not found"
            )

        with logger.contextualize(
            privacy_request_source=(
                privacy_request.source.value if privacy_request.source else None
            ),
            privacy_request_id=privacy_request.id,
        ):
            if privacy_request.status == PrivacyRequestStatus.canceled:
                logger.info("Terminating privacy request: request canceled.")
                return

            if privacy_request.deleted_at is not None:
                logger.info("Terminating privacy request: request deleted.")
                return

            check_for_duplicates(db=session, privacy_request=privacy_request)
            if privacy_request.status == PrivacyRequestStatus.duplicate:
                return

            logger.info("Dispatching privacy request")
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
                privacy_request.cache_failed_checkpoint_details(
                    CurrentStep.pre_webhooks
                )
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
                error_message = (
                    f"Policy with key {policy.key} must contain at least one Rule."
                )
                privacy_request.add_error_execution_log(
                    session,
                    connection_key=None,
                    dataset_name="Policy validation",
                    collection_name=None,
                    message=error_message,
                    action_type=ActionType.access,  # Default since policy has no rules
                )
                privacy_request.error_processing(db=session)
                raise common_exceptions.MisconfiguredPolicyException(error_message)

            try:
                # Eager load connection_config and ctl_dataset to avoid N+1 queries
                datasets = (
                    session.query(DatasetConfig)
                    .options(
                        selectinload(DatasetConfig.connection_config),
                        selectinload(DatasetConfig.ctl_dataset),
                    )
                    .all()
                )
                dataset_graphs = [
                    dataset_config.get_graph()
                    for dataset_config in datasets
                    if not dataset_config.connection_config.disabled
                ]

                # Add manual task artificial graphs to dataset graphs
                # Only include manual tasks with access or erasure configs
                manual_task_graphs = create_manual_task_artificial_graphs(
                    session, config_types=[ActionType.access, ActionType.erasure]
                )
                dataset_graphs.extend(manual_task_graphs)

                dataset_graph = DatasetGraph(*dataset_graphs)

                # Add success log for dataset configuration
                privacy_request.add_success_execution_log(
                    session,
                    connection_key=None,
                    dataset_name="Dataset reference validation",
                    collection_name=None,
                    message=f"Dataset reference validation successful for privacy request: {privacy_request.id}",
                    action_type=privacy_request.policy.get_action_type(),  # type: ignore
                )

                identity_data = {
                    key: value["value"] if isinstance(value, dict) else value
                    for key, value in privacy_request.get_cached_identity_data().items()
                }
                # Eager load datasets relationship to avoid N+1 queries in filter_fides_connector_datasets
                connection_configs = (
                    session.query(ConnectionConfig)
                    .options(selectinload(ConnectionConfig.datasets))
                    .all()
                )
                fides_connector_datasets: set[str] = filter_fides_connector_datasets(
                    connection_configs
                )

                # If the privacy request requires manual finalization and has not yet been finalized, we exit here
                if (
                    privacy_request.status
                    == PrivacyRequestStatus.requires_manual_finalization
                    and privacy_request.finalized_at is None
                ):
                    return

                # Access CHECKPOINT
                if (
                    policy.get_rules_for_action(action_type=ActionType.access)
                    or policy.get_rules_for_action(action_type=ActionType.erasure)
                ) and can_run_checkpoint(
                    request_checkpoint=CurrentStep.access,
                    from_checkpoint=resume_step,
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
                access_result_urls: list[str] = []
                raw_access_results: dict = privacy_request.get_raw_access_results()
                if (
                    (
                        policy.get_rules_for_action(action_type=ActionType.access)
                        or policy.get_rules_for_action(
                            action_type=ActionType.erasure
                        )  # Intentional to support requeuing the Privacy Request after the Access step for DSR 3.0 for both access/erasure requests
                    )
                    and can_run_checkpoint(
                        request_checkpoint=CurrentStep.upload_access,
                        from_checkpoint=resume_step,
                    )
                ):
                    privacy_request.cache_failed_checkpoint_details(
                        CurrentStep.upload_access
                    )
                    filtered_access_results = filter_by_enabled_actions(
                        raw_access_results, connection_configs
                    )
                    access_result_urls = upload_and_save_access_results(
                        session,
                        policy,
                        filtered_access_results,
                        dataset_graph,
                        privacy_request,
                        manual_webhook_access_results,
                        fides_connector_datasets,
                    )

                # Erasure CHECKPOINT
                if policy.get_rules_for_action(
                    action_type=ActionType.erasure
                ) and can_run_checkpoint(
                    request_checkpoint=CurrentStep.erasure,
                    from_checkpoint=resume_step,
                ):
                    privacy_request.cache_failed_checkpoint_details(CurrentStep.erasure)
                    _verify_masking_secrets(policy, privacy_request, resume_step)

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
                        graph=build_consent_dataset_graph(datasets, session),
                        connection_configs=connection_configs,
                        identity=identity_data,
                        session=session,
                        privacy_request_proceed=True,  # Should always be True unless we're testing
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
                logger.info(
                    "Privacy Request exited awaiting sub task processing (Request Tasks)"
                )
                return

            except ValidationError as exc:
                # Handle validation errors from dataset graph creation
                logger.error(f"Error validating dataset references: {str(exc)}")
                privacy_request.add_error_execution_log(
                    session,
                    connection_key=None,
                    dataset_name="Dataset reference validation",
                    collection_name=None,
                    message=str(exc),
                    action_type=privacy_request.policy.get_action_type(),  # type: ignore[arg-type]
                )
                privacy_request.error_processing(db=session)
                return

            except BaseException as exc:  # pylint: disable=broad-except
                # Log the error to the activity timeline before marking as errored
                privacy_request.add_error_execution_log(
                    session,
                    connection_key=None,
                    dataset_name="Privacy request processing",
                    collection_name=None,
                    message=str(exc),
                    action_type=privacy_request.policy.get_action_type(),  # type: ignore
                )
                privacy_request.error_processing(db=session)
                # If dev mode, log traceback
                _log_exception(exc, CONFIG.dev_mode)
                return

            # Post-processing steps: email send, webhooks, finalization
            # Wrap in try/except to catch any unhandled exceptions
            try:
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
                    privacy_request.cache_failed_checkpoint_details(
                        CurrentStep.email_post_send
                    )
                    privacy_request.pause_processing_for_email_send(session)
                    logger.info("Privacy request exiting: awaiting email send.")
                    return

                # Post Webhooks CHECKPOINT
                if can_run_checkpoint(
                    request_checkpoint=CurrentStep.post_webhooks,
                    from_checkpoint=resume_step,
                ):
                    privacy_request.cache_failed_checkpoint_details(
                        CurrentStep.post_webhooks
                    )
                    proceed = run_webhooks_and_report_status(
                        db=session,
                        privacy_request=privacy_request,
                        webhook_cls=PolicyPostWebhook,  # type: ignore
                    )
                    if not proceed:
                        return

                # pylint: disable=too-many-nested-blocks
                # Request finalization CHECKPOINT
                if can_run_checkpoint(
                    request_checkpoint=CurrentStep.finalization,
                    from_checkpoint=resume_step,
                ):
                    privacy_request.cache_failed_checkpoint_details(
                        CurrentStep.finalization,
                    )
                    if privacy_request.status != PrivacyRequestStatus.error:
                        erasure_rules = policy.get_rules_for_action(
                            action_type=ActionType.erasure
                        )
                        config_proxy = ConfigProxy(session)
                        requires_finalization = (
                            privacy_request.finalized_at is None
                            and (
                                erasure_rules
                                and config_proxy.execution.erasure_request_finalization_required
                            )
                        )
                        if requires_finalization:
                            logger.info(
                                "Marking privacy request '{}' as requires manual finalization.",
                                privacy_request.id,
                            )
                            privacy_request.status = (
                                PrivacyRequestStatus.requires_manual_finalization
                            )
                            privacy_request.save(db=session)
                            return

                        # Finally, mark the request as complete
                        if privacy_request.finalized_at:
                            logger.info(
                                "Marking privacy request '{}' as finalized.",
                                privacy_request.id,
                            )
                            privacy_request.add_success_execution_log(
                                session,
                                connection_key=None,
                                dataset_name="Request finalized",
                                collection_name=None,
                                message=f"Request finalized for privacy request: {privacy_request.id}",
                                action_type=privacy_request.policy.get_action_type(),  # type: ignore
                            )

                        logger.info(
                            "Marking privacy request '{}' as complete.",
                            privacy_request.id,
                        )
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
                        privacy_request.finished_processing_at = datetime.utcnow()
                        privacy_request.save(db=session)

                        # Send a final email to the user confirming request completion
                        if privacy_request.status == PrivacyRequestStatus.complete:
                            legacy_request_completion_enabled = ConfigProxy(
                                session
                            ).notifications.send_request_completion_notification

                            action_types = policy.get_all_action_types()

                            # Access/erasure completion emails take priority over consent
                            if (
                                ActionType.access in action_types
                                or ActionType.erasure in action_types
                            ):
                                action_type = (
                                    MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS
                                    if ActionType.access in action_types
                                    else MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION
                                )

                                message_send_result = message_send_enabled(
                                    session,
                                    privacy_request.property_id,
                                    action_type,
                                    legacy_request_completion_enabled,
                                )

                                if message_send_result:
                                    if not access_result_urls:
                                        # For DSR 3.0, if the request had both access and erasure rules, this needs to be fetched
                                        # from the database because the Privacy Request would have exited
                                        # processing and lost access to the access_result_urls in memory
                                        access_result_urls = (
                                            privacy_request.access_result_urls or {}
                                        ).get("access_result_urls", [])

                                    try:
                                        initiate_privacy_request_completion_email(
                                            session,
                                            policy,
                                            access_result_urls,
                                            identity_data,
                                            privacy_request.property_id,
                                            privacy_request.id,
                                        )
                                        # Add success log for completion email
                                        privacy_request.add_success_execution_log(
                                            session,
                                            connection_key=None,
                                            dataset_name="Privacy request completion email",
                                            collection_name=None,
                                            message="Privacy request completion email sent successfully.",
                                            action_type=privacy_request.policy.get_action_type(),  # type: ignore
                                        )
                                    except (
                                        IdentityNotFoundException,
                                        MessageDispatchException,
                                    ) as e:
                                        # Add error log for completion email failure
                                        privacy_request.add_error_execution_log(
                                            session,
                                            connection_key=None,
                                            dataset_name="Privacy request completion email",
                                            collection_name=None,
                                            message=f"Privacy request completion email failed: {str(e)}",
                                            action_type=privacy_request.policy.get_action_type(),  # type: ignore
                                        )
                                        privacy_request.error_processing(db=session)
                                        # If dev mode, log traceback
                                        _log_exception(e, CONFIG.dev_mode)
                                        return

                            # Send consent completion email only for consent-only requests
                            elif ActionType.consent in action_types:
                                consent_message_enabled = message_send_enabled(
                                    session,
                                    privacy_request.property_id,
                                    MessagingActionType.PRIVACY_REQUEST_COMPLETE_CONSENT,
                                    legacy_request_completion_enabled,
                                )
                                if consent_message_enabled:
                                    try:
                                        email_sent = (
                                            initiate_consent_request_completion_email(
                                                session,
                                                identity_data,
                                                privacy_request.property_id,
                                            )
                                        )
                                        if email_sent:
                                            privacy_request.add_success_execution_log(
                                                session,
                                                connection_key=None,
                                                dataset_name="Consent request completion email",
                                                collection_name=None,
                                                message="Consent request completion email sent successfully.",
                                                action_type=ActionType.consent,
                                            )
                                    except MessageDispatchException as e:
                                        privacy_request.add_error_execution_log(
                                            session,
                                            connection_key=None,
                                            dataset_name="Consent request completion email",
                                            collection_name=None,
                                            message=f"Consent request completion email failed: {str(e)}",
                                            action_type=ActionType.consent,
                                        )
                                        privacy_request.error_processing(db=session)
                                        _log_exception(e, CONFIG.dev_mode)
                                        return

            except BaseException as exc:  # pylint: disable=broad-except
                # Catch any unhandled exceptions in post-processing steps
                privacy_request.add_error_execution_log(
                    session,
                    connection_key=None,
                    dataset_name="Privacy request finalization",
                    collection_name=None,
                    message=f"Error during post-processing: {str(exc)}",
                    action_type=privacy_request.policy.get_action_type(),  # type: ignore
                )
                privacy_request.error_processing(db=session)
                _log_exception(exc, CONFIG.dev_mode)
                return


def _verify_masking_secrets(
    policy: Policy, privacy_request: PrivacyRequest, resume_step: Optional[CurrentStep]
) -> None:
    """
    Checks that the required masking secrets are still cached for the given request.
    Raises an exception if masking secrets are needed for the given policy but they don't exist.
    """

    if resume_step is None:
        return

    # if masking can be performed without any masking secrets, we skip the cache check
    if (
        policy.generate_masking_secrets()
        and not get_all_masking_secret_keys(privacy_request.id)
        and not privacy_request.masking_secrets
    ):
        raise MaskingSecretsExpired(
            f"The masking secrets for privacy request ID '{privacy_request.id}' have expired. Please submit a new erasure request."
        )


# Re-exports for backward compatibility -- consumers should import from the new modules directly.
from fides.api.service.privacy_request.access_result_service import (
    save_access_results as save_access_results,  # noqa: E402
)
from fides.api.service.privacy_request.completion_notification_service import (  # noqa: E402
    initiate_paused_privacy_request_followup as initiate_paused_privacy_request_followup,
)
from fides.api.service.privacy_request.email_batch_service import (  # noqa: E402
    get_consent_email_connection_configs as get_consent_email_connection_configs,
)
from fides.api.service.privacy_request.email_batch_service import (
    get_erasure_email_connection_configs as get_erasure_email_connection_configs,
)
