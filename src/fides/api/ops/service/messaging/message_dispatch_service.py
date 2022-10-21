from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

import requests
from sqlalchemy.orm import Session

from fides.api.ops.common_exceptions import MessageDispatchException
from fides.api.ops.email_templates import get_email_template
from fides.api.ops.models.messaging import MessagingConfig
from fides.api.ops.models.privacy_request import CheckpointActionRequired
from fides.api.ops.schemas.messaging.messaging import (
    AccessRequestCompleteBodyParams,
    FidesopsMessage,
    MessageForActionType,
    MessagingActionType,
    MessagingMethod,
    MessagingServiceDetails,
    MessagingServiceSecrets,
    MessagingServiceType,
    RequestReceiptBodyParams,
    RequestReviewDenyBodyParams,
    SubjectIdentityVerificationBodyParams,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.tasks import DatabaseTask, celery_app
from fides.api.ops.util.logger import Pii
from fides.ctl.core.config import get_config

CONFIG = get_config()

logger = logging.getLogger(__name__)


@celery_app.task(base=DatabaseTask, bind=True)
def dispatch_message_task(
    self: DatabaseTask,
    message_meta: Dict[str, Any],
    messaging_method: Optional[MessagingMethod],
    to_identity: Identity,
) -> None:
    """
    A wrapper function to dispatch a message task into the Celery queues
    """
    schema = FidesopsMessage.parse_obj(message_meta)
    with self.session as db:
        dispatch_message(
            db,
            schema.action_type,
            to_identity,
            messaging_method,
            schema.body_params,
        )


def dispatch_message(
    db: Session,
    action_type: MessagingActionType,
    to_identity: Optional[Identity],
    messaging_method: Optional[MessagingMethod],
    message_body_params: Optional[
        Union[
            AccessRequestCompleteBodyParams,
            SubjectIdentityVerificationBodyParams,
            RequestReceiptBodyParams,
            RequestReviewDenyBodyParams,
            List[CheckpointActionRequired],
        ]
    ] = None,
) -> None:
    """
    Sends a message to `to_identity` with content supplied in `message_body_params`
    """
    if not to_identity:
        logger.error("Message failed to send. No identity supplied.")
        raise MessageDispatchException("No identity supplied.")

    logger.info("Retrieving message config")
    messaging_config: MessagingConfig = MessagingConfig.get_configuration(db=db)
    logger.info(
        "Building appropriate message template for action type: %s", action_type
    )
    message: Optional[MessageForActionType] = None  # fixme- huh??
    if messaging_method == MessagingMethod.EMAIL:
        message = _build_email(
            action_type=action_type,
            body_params=message_body_params,
        )
    elif messaging_method == MessagingMethod.SMS:
        message = _build_sms(
            action_type=action_type,
            body_params=message_body_params,
        )
    else:
        logger.error(
            "Notification service type is not valid: %s", CONFIG.notifications.notification_service_type
        )
        raise MessageDispatchException(
            f"Notification service type is not valid: {CONFIG.notifications.notification_service_type}"
        )
    messaging_service: MessagingServiceType = messaging_config.service_type  # type: ignore
    logger.info(
        "Retrieving appropriate dispatcher for email service: %s", messaging_service
    )
    dispatcher: Any = _get_dispatcher_from_config_type(
        message_service_type=messaging_service
    )
    logger.info(
        "Starting email dispatch for messaging service with action type: %s",
        action_type,
    )
    dispatcher(
        messaging_config=messaging_config,
        message=message,
        to=to_identity.email
        if messaging_method == MessagingMethod.EMAIL
        else to_identity.phone_number,
    )


def _build_sms(
    action_type: MessagingActionType,
    body_params: Any,  # fixme- create message body based on params
) -> MessageForActionType:
    if action_type == MessagingActionType.CONSENT_REQUEST:
        return MessageForActionType(
            subject="Your one-time code",
            body="body",
        )
    logger.error("Message action type %s is not implemented", action_type)
    raise MessageDispatchException(
        f"Message action type {action_type} is not implemented"
    )


def _build_email(  # pylint: disable=too-many-return-statements
    action_type: MessagingActionType,
    body_params: Any,
) -> MessageForActionType:
    if action_type == MessagingActionType.CONSENT_REQUEST:
        template = get_email_template(action_type)
        return MessageForActionType(
            subject="Your one-time code",
            body=template.render(
                {
                    "code": body_params.verification_code,
                    "minutes": body_params.get_verification_code_ttl_minutes(),
                }
            ),
        )
    if action_type == MessagingActionType.SUBJECT_IDENTITY_VERIFICATION:
        template = get_email_template(action_type)
        return MessageForActionType(
            subject="Your one-time code",
            body=template.render(
                {
                    "code": body_params.verification_code,
                    "minutes": body_params.get_verification_code_ttl_minutes(),
                }
            ),
        )
    if action_type == MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT:
        base_template = get_email_template(action_type)
        return MessageForActionType(
            subject="Data erasure request",
            body=base_template.render(
                {"dataset_collection_action_required": body_params}
            ),
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_RECEIPT:
        base_template = get_email_template(action_type)
        return MessageForActionType(
            subject="Your request has been received",
            body=base_template.render({"request_types": body_params.request_types}),
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS:
        base_template = get_email_template(action_type)
        return MessageForActionType(
            subject="Your data is ready to be downloaded",
            body=base_template.render(
                {
                    "download_links": body_params.download_links,
                }
            ),
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION:
        base_template = get_email_template(action_type)
        return MessageForActionType(
            subject="Your data has been deleted",
            body=base_template.render(),
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE:
        base_template = get_email_template(action_type)
        return MessageForActionType(
            subject="Your request has been approved",
            body=base_template.render(),
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY:
        base_template = get_email_template(action_type)
        return MessageForActionType(
            subject="Your request has been denied",
            body=base_template.render(
                {"rejection_reason": body_params.rejection_reason}
            ),
        )
    logger.error("Message action type %s is not implemented", action_type)
    raise MessageDispatchException(
        f"Message action type {action_type} is not implemented"
    )


def _get_dispatcher_from_config_type(message_service_type: MessagingServiceType) -> Any:
    """Determines which dispatcher to use based on message service type"""
    return {
        MessagingServiceType.MAILGUN.value: _mailgun_dispatcher,
    }[message_service_type.value]


def _mailgun_dispatcher(
    messaging_config: MessagingConfig,
    message: MessageForActionType,
    to_email: Optional[str],
) -> None:
    """Dispatches email using mailgun"""
    if not to_email:
        logger.error("Message failed to send. No email identity supplied.")
        raise MessageDispatchException("No email identity supplied.")
    base_url = (
        "https://api.mailgun.net"
        if messaging_config.details[MessagingServiceDetails.IS_EU_DOMAIN.value] is False
        else "https://api.eu.mailgun.net"
    )
    domain = messaging_config.details[MessagingServiceDetails.DOMAIN.value]
    data = {
        "from": f"<mailgun@{domain}>",
        "to": [to_email],
        "subject": message.subject,
        "html": message.body,
    }
    try:
        response: requests.Response = requests.post(
            f"{base_url}/{messaging_config.details[MessagingServiceDetails.API_VERSION.value]}/{domain}/messages",
            auth=(
                "api",
                messaging_config.secrets[MessagingServiceSecrets.MAILGUN_API_KEY.value],  # type: ignore
            ),
            data=data,
        )
        if not response.ok:
            logger.error(
                "Email failed to send with status code: %s", response.status_code
            )
            raise MessageDispatchException(
                f"Email failed to send with status code {response.status_code}"
            )
    except Exception as e:
        logger.error("Email failed to send: %s", Pii(str(e)))
        raise MessageDispatchException(f"Email failed to send due to: {Pii(e)}")
