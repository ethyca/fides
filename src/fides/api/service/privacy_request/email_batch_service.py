import uuid
from enum import Enum
from typing import Any

from loguru import logger
from sqlalchemy.orm import Query, Session

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.connectionconfig import AccessLevel, ConnectionConfig
from fides.api.models.policy import Policy, Rule
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.connectors import get_connector
from fides.api.service.connectors.consent_email_connector import (
    CONSENT_EMAIL_CONNECTOR_TYPES,
)
from fides.api.service.connectors.erasure_email_connector import (
    ERASURE_EMAIL_CONNECTOR_TYPES,
)
from fides.api.tasks import DatabaseTask, celery_app
from fides.api.tasks.scheduled.scheduler import create_cron_trigger, scheduler
from fides.api.util.lock import redis_lock
from fides.config import get_config
from fides.service.privacy_request.privacy_request_service import queue_privacy_request

CONFIG = get_config()
BATCH_EMAIL_SEND = "batch_email_send"
BATCH_EMAIL_SEND_LOCK = "batch_email_send_lock"
BATCH_EMAIL_SEND_LOCK_TIMEOUT = 600


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
    db: Session, user_identities: dict[str, Any], privacy_request: PrivacyRequest
) -> bool:
    """
    Delegates the "needs email" check to each configured email or
    generic email consent connector. Returns true if at least one
    connector needs to send an email.

    Only checks connectors relevant to the policy's action types.
    For example, consent-only policies will only check consent email connectors.

    If we don't need to send any emails, add skipped logs for any
    relevant erasure and consent email connectors.
    """
    can_skip_erasure_email: list[ConnectionConfig] = []
    can_skip_consent_email: list[ConnectionConfig] = []

    needs_email_send: bool = False

    # Get the action types for this policy
    policy_action_types = privacy_request.policy.get_all_action_types()
    has_erasure_rules = ActionType.erasure in policy_action_types
    has_consent_rules = ActionType.consent in policy_action_types

    # Only check erasure email connectors if the policy has erasure rules
    if has_erasure_rules:
        for connection_config in get_erasure_email_connection_configs(db):
            if get_connector(connection_config).needs_email(  # type: ignore
                user_identities, privacy_request
            ):
                needs_email_send = True
            else:
                can_skip_erasure_email.append(connection_config)

    # Only check consent email connectors if the policy has consent rules
    if has_consent_rules:
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
    can_skip_erasure_email: list[ConnectionConfig],
    can_skip_consent_email: list[ConnectionConfig],
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


class EmailExitState(Enum):
    """A schema to describe where the email send process exited.
    For logging and testing"""

    no_applicable_privacy_requests = "no_applicable_privacy_requests"
    no_applicable_connectors = "no_applicable_connectors"
    missing_required_data = "missing_required_data"
    email_send_failed = "email_send_failed"
    complete = "complete"
    email_send_already_running = "email_send_already_running"


@celery_app.task(base=DatabaseTask, bind=True)
def send_email_batch(self: DatabaseTask) -> EmailExitState:
    """Sends emails for each relevant connector with applicable user details batched together."""
    with redis_lock(
        lock_key=BATCH_EMAIL_SEND_LOCK, timeout=BATCH_EMAIL_SEND_LOCK_TIMEOUT
    ) as lock:
        if not lock:
            return EmailExitState.email_send_already_running

        batch_id = str(uuid.uuid4())
        logger.info("Starting batch email send {}...", batch_id)
        with self.get_new_session() as session:
            # Use query_without_large_columns to prevent OOM errors when processing many privacy requests
            privacy_requests: Query = (
                PrivacyRequest.query_without_large_columns(session)
                .filter(
                    PrivacyRequest.status == PrivacyRequestStatus.awaiting_email_send
                )
                .filter(PrivacyRequest.deleted_at.is_(None))
                .order_by(PrivacyRequest.created_at.asc())  # oldest first
            )
            if not privacy_requests.first():
                logger.info(
                    "Skipping batch email send with status: {}",
                    EmailExitState.no_applicable_privacy_requests.value,
                )
                return EmailExitState.no_applicable_privacy_requests

            consent_configs: Query = get_consent_email_connection_configs(session)
            erasure_configs: Query = get_erasure_email_connection_configs(session)
            combined_configs = consent_configs.union_all(erasure_configs)
            if not combined_configs.first():
                requeue_privacy_requests_after_email_send(privacy_requests, session)
                logger.info(
                    "Skipping batch email send with status: {}",
                    EmailExitState.no_applicable_connectors.value,
                )
                return EmailExitState.no_applicable_connectors

            try:
                # erasure
                for connection_config in erasure_configs:
                    get_connector(connection_config).batch_email_send(  # type: ignore
                        filter_privacy_requests_by_action_type(
                            privacy_requests, ActionType.erasure
                        ),
                        batch_id,
                    )

                # consent
                for connection_config in consent_configs:
                    get_connector(connection_config).batch_email_send(  # type: ignore
                        filter_privacy_requests_by_action_type(
                            privacy_requests, ActionType.consent
                        ),
                        batch_id,
                    )
            except MessageDispatchException as exc:
                logger.error(
                    "Batch email send for connector failed with exception: '{}'",
                    exc,
                )
                return EmailExitState.email_send_failed

        requeue_privacy_requests_after_email_send(privacy_requests, session)
        return EmailExitState.complete


def filter_privacy_requests_by_action_type(
    privacy_requests: Query, action_type: ActionType
) -> Query:
    """Applies a filter for the specific Rule.action_type to the passed in privacy_requests."""
    return (
        privacy_requests.join(Policy, PrivacyRequest.policy_id == Policy.id)
        .join(Rule, Policy.id == Rule.policy_id)
        .filter(Rule.action_type == action_type)
    )


def requeue_privacy_requests_after_email_send(
    privacy_requests: Query, db: Session
) -> None:
    """After batch consent email send, requeue privacy requests from the post webhooks step
    to wrap up processing and transition to a "complete" state.

    Also cache on the privacy request itself that it is paused at the post-webhooks state,
    in case something happens in re-queueing.
    """
    logger.info("Batched email send complete.")
    logger.info("Queuing privacy requests from 'post_webhooks' step.")
    for privacy_request in privacy_requests:
        privacy_request.cache_paused_collection_details(
            step=CurrentStep.post_webhooks,
            collection=None,
            action_needed=None,
        )
        privacy_request.status = PrivacyRequestStatus.paused
        privacy_request.save(db=db)

        queue_privacy_request(
            privacy_request_id=privacy_request.id,
            from_step=CurrentStep.post_webhooks.value,
        )


def initiate_scheduled_batch_email_send() -> None:
    """Initiates scheduler to add weekly batch email send"""

    if CONFIG.test_mode:
        return

    assert scheduler.running, "Scheduler is not running! Cannot add Batch Email job."

    cron_trigger = create_cron_trigger(
        cron_expression=CONFIG.execution.email_send_cron_expression,
        timezone=CONFIG.execution.email_send_timezone,
    )

    logger.info("Initiating scheduler for batch email send")
    scheduler.add_job(
        func=send_email_batch,
        kwargs={},
        id=BATCH_EMAIL_SEND,
        coalesce=False,
        replace_existing=True,
        trigger=cron_trigger,
    )
