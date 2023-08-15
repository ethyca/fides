from enum import Enum

from loguru import logger
from sqlalchemy.orm import Query, Session

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.policy import CurrentStep, Policy, Rule
from fides.api.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fides.api.schemas.policy import ActionType
from fides.api.service.connectors import get_connector
from fides.api.service.privacy_request.request_runner_service import (
    get_consent_email_connection_configs,
    get_erasure_email_connection_configs,
    queue_privacy_request,
)
from fides.api.tasks import DatabaseTask, celery_app
from fides.api.tasks.scheduled.scheduler import scheduler
from fides.config import get_config

CONFIG = get_config()
BATCH_EMAIL_SEND = "batch_email_send"


class EmailExitState(Enum):
    """A schema to describe where the email send process exited.
    For logging and testing"""

    no_applicable_privacy_requests = "no_applicable_privacy_requests"
    no_applicable_connectors = "no_applicable_connectors"
    missing_required_data = "missing_required_data"
    email_send_failed = "email_send_failed"
    complete = "complete"


@celery_app.task(base=DatabaseTask, bind=True)
def send_email_batch(self: DatabaseTask) -> EmailExitState:
    """Sends emails for each relevant connector with applicable user details batched together."""

    logger.info("Starting batched email send...")
    with self.get_new_session() as session:
        privacy_requests: Query = (
            session.query(PrivacyRequest)
            .filter(PrivacyRequest.status == PrivacyRequestStatus.awaiting_email_send)
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
                    )
                )

            # consent
            for connection_config in consent_configs:
                get_connector(connection_config).batch_email_send(  # type: ignore
                    filter_privacy_requests_by_action_type(
                        privacy_requests, ActionType.consent
                    )
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

    logger.info("Initiating scheduler for batch email send")
    scheduler.add_job(
        func=send_email_batch,
        kwargs={},
        id=BATCH_EMAIL_SEND,
        coalesce=False,
        replace_existing=True,
        trigger="cron",
        minute="0",
        hour="12",
        day_of_week="mon",
        timezone="US/Eastern",
    )
