from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional, Union

import requests
from loguru import logger
from sqlalchemy.orm import Session
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from fides.api.ops.common_exceptions import MessageDispatchException
from fides.api.ops.email_templates import get_email_template
from fides.api.ops.models.messaging import (  # type: ignore[attr-defined]
    EMAIL_MESSAGING_SERVICES,
    MessagingConfig,
    get_messaging_method,
)
from fides.api.ops.models.privacy_request import (
    CheckpointActionRequired,
    PrivacyRequestError,
    PrivacyRequestNotifications,
)
from fides.api.ops.schemas.messaging.messaging import (
    AccessRequestCompleteBodyParams,
    EmailForActionType,
    ErrorNotificaitonBodyParams,
    FidesopsMessage,
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
from fides.api.ops.tasks import MESSAGING_QUEUE_NAME, DatabaseTask, celery_app
from fides.api.ops.util.logger import Pii
from fides.core.config import get_config

CONFIG = get_config()


EMAIL_JOIN_STRING = ", "


def check_and_dispatch_error_notifications(db: Session) -> None:
    privacy_request_notifications = PrivacyRequestNotifications.all(db=db)
    if not privacy_request_notifications:
        return None

    unsent_errors = PrivacyRequestError.filter(
        db=db, conditions=(PrivacyRequestError.message_sent.is_(False))
    ).all()
    if not unsent_errors:
        return None

    email_config = (
        CONFIG.notifications.notification_service_type in EMAIL_MESSAGING_SERVICES
    )

    if (
        email_config
        and len(unsent_errors) >= privacy_request_notifications[0].notify_after_failures
    ):
        for email in privacy_request_notifications[0].email.split(EMAIL_JOIN_STRING):
            dispatch_message_task.apply_async(
                queue=MESSAGING_QUEUE_NAME,
                kwargs={
                    "message_meta": FidesopsMessage(
                        action_type=MessagingActionType.PRIVACY_REQUEST_ERROR_NOTIFICATION,
                        body_params=ErrorNotificaitonBodyParams(
                            unsent_errors=len(unsent_errors)
                        ),
                    ).dict(),
                    "service_type": CONFIG.notifications.notification_service_type,
                    "to_identity": {"email": email},
                },
            )

        for error in unsent_errors:
            error.update(db=db, data={"message_sent": True})

    return None


@celery_app.task(base=DatabaseTask, bind=True)
def dispatch_message_task(
    self: DatabaseTask,
    message_meta: Dict[str, Any],
    service_type: Optional[str],
    to_identity: Dict[str, Any],
) -> None:
    """
    A wrapper function to dispatch a message task into the Celery queues
    """
    schema = FidesopsMessage.parse_obj(message_meta)
    with self.session as db:
        dispatch_message(
            db,
            schema.action_type,
            Identity.parse_obj(to_identity),
            service_type,
            schema.body_params,
        )


def dispatch_message(
    db: Session,
    action_type: MessagingActionType,
    to_identity: Optional[Identity],
    service_type: Optional[str],
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
    if not service_type:
        logger.error("Message failed to send. No notification service type configured.")
        raise MessageDispatchException("No notification service type configured.")

    logger.info("Retrieving message config")
    messaging_config: MessagingConfig = MessagingConfig.get_configuration(
        db=db, service_type=service_type
    )
    logger.info(
        "Building appropriate message template for action type: {}", action_type
    )
    messaging_method = get_messaging_method(service_type)
    message: Optional[Union[EmailForActionType, str]] = None
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
            "Notification service type is not valid: {}",
            CONFIG.notifications.notification_service_type,
        )
        raise MessageDispatchException(
            f"Notification service type is not valid: {CONFIG.notifications.notification_service_type}"
        )
    messaging_service: MessagingServiceType = messaging_config.service_type  # type: ignore
    logger.info(
        "Retrieving appropriate dispatcher for email service: {}", messaging_service
    )
    dispatcher: Optional[
        Callable[[MessagingConfig, Any, Optional[str]], None]
    ] = _get_dispatcher_from_config_type(message_service_type=messaging_service)
    if not dispatcher:
        logger.error(
            "Dispatcher has not been implemented for message service type: {}",
            messaging_service,
        )
        raise MessageDispatchException(
            f"Dispatcher has not been implemented for message service type: {messaging_service}"
        )
    logger.info(
        "Starting message dispatch for messaging service with action type: {}",
        action_type,
    )
    dispatcher(
        messaging_config,
        message,
        to_identity.email
        if messaging_method == MessagingMethod.EMAIL
        else to_identity.phone_number,
    )


def _build_sms(  # pylint: disable=too-many-return-statements
    action_type: MessagingActionType,
    body_params: Any,
) -> str:
    separator = ","
    if action_type == MessagingActionType.SUBJECT_IDENTITY_VERIFICATION:
        return (
            f"Your privacy request verification code is {body_params.verification_code}. "
            f"Please return to the Privacy Center and enter the code to continue. "
            f"This code will expire in {body_params.get_verification_code_ttl_minutes()} minutes"
        )
    if action_type == MessagingActionType.CONSENT_REQUEST:
        return (
            "Your consent request verification code is {{code}}. "
            "Please return to the consent request page and enter the code to continue. "
            "This code will expire in {{minutes}} minutes"
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_RECEIPT:
        if len(body_params.request_types) > 1:
            return f"The following requests have been received: {separator.join(body_params.request_types)}"
        return f"Your {body_params.request_types[0]} request has been received"
    if action_type == MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS:
        if len(body_params.download_links) > 1:
            return (
                "Your data access has been completed and can be downloaded at the following links. "
                "For security purposes, these secret links will expire in 24 hours: "
                f"{separator.join(body_params.download_links)}"
            )
        return (
            f"Your data access has been completed and can be downloaded at {body_params.download_links[0]}. "
            f"For security purposes, this secret link will expire in 24 hours."
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION:
        return "Your privacy request for deletion has been completed."
    if action_type == MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE:
        return "Your privacy request has been approved and is currently processing."
    if action_type == MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY:
        if body_params.rejection_reason:
            return f"Your privacy request has been denied for the following reason: {body_params.rejection_reason}"
        return "Your privacy request has been denied."
    logger.error("Message action type {} is not implemented", action_type)
    raise MessageDispatchException(
        f"Message action type {action_type} is not implemented"
    )


def _build_email(  # pylint: disable=too-many-return-statements
    action_type: MessagingActionType,
    body_params: Any,
) -> EmailForActionType:
    if action_type == MessagingActionType.CONSENT_REQUEST:
        template = get_email_template(action_type)
        return EmailForActionType(
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
        return EmailForActionType(
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
        return EmailForActionType(
            subject="Data erasure request",
            body=base_template.render(
                {"dataset_collection_action_required": body_params}
            ),
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_RECEIPT:
        base_template = get_email_template(action_type)
        return EmailForActionType(
            subject="Your request has been received",
            body=base_template.render({"request_types": body_params.request_types}),
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS:
        base_template = get_email_template(action_type)
        return EmailForActionType(
            subject="Your data is ready to be downloaded",
            body=base_template.render(
                {
                    "download_links": body_params.download_links,
                }
            ),
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION:
        base_template = get_email_template(action_type)
        return EmailForActionType(
            subject="Your data has been deleted",
            body=base_template.render(),
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_ERROR_NOTIFICATION:
        base_template = get_email_template(action_type)
        return EmailForActionType(
            subject="Privacy Request Error Alert",
            body=base_template.render(),
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE:
        base_template = get_email_template(action_type)
        return EmailForActionType(
            subject="Your request has been approved",
            body=base_template.render(),
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY:
        base_template = get_email_template(action_type)
        return EmailForActionType(
            subject="Your request has been denied",
            body=base_template.render(
                {"rejection_reason": body_params.rejection_reason}
            ),
        )
    logger.error("Message action type {} is not implemented", action_type)
    raise MessageDispatchException(
        f"Message action type {action_type} is not implemented"
    )


def _get_dispatcher_from_config_type(
    message_service_type: MessagingServiceType,
) -> Optional[Callable[[MessagingConfig, Any, Optional[str]], None]]:
    """Determines which dispatcher to use based on message service type"""
    if message_service_type == MessagingServiceType.MAILGUN:
        return _mailgun_dispatcher
    if message_service_type == MessagingServiceType.TWILIO_TEXT:
        return _twilio_sms_dispatcher
    return None


def _mailgun_dispatcher(
    messaging_config: MessagingConfig,
    message: EmailForActionType,
    to: Optional[str],
) -> None:
    """Dispatches email using mailgun"""
    if not to:
        logger.error("Message failed to send. No email identity supplied.")
        raise MessageDispatchException("No email identity supplied.")
    if not messaging_config.details or not messaging_config.secrets:
        logger.error(
            "Message failed to send. No mailgun config details or secrets supplied."
        )
        raise MessageDispatchException("No mailgun config details or secrets supplied.")
    base_url = (
        "https://api.mailgun.net"
        if messaging_config.details[MessagingServiceDetails.IS_EU_DOMAIN.value] is False
        else "https://api.eu.mailgun.net"
    )

    domain = messaging_config.details[MessagingServiceDetails.DOMAIN.value]

    try:
        # Check if a fides template exists
        template_test = requests.get(
            f"{base_url}/{messaging_config.details[MessagingServiceDetails.API_VERSION.value]}/{domain}/templates/fides",
            auth=(
                "api",
                messaging_config.secrets[MessagingServiceSecrets.MAILGUN_API_KEY.value],
            ),
        )

        data = {
            "from": f"<mailgun@{domain}>",
            "to": [to.strip()],
            "subject": message.subject,
        }

        if template_test.status_code == 200:
            data["template"] = "fides"
            data["h:X-Mailgun-Variables"] = json.dumps(
                {"fides_email_body": message.body}
            )
            response = requests.post(
                f"{base_url}/{messaging_config.details[MessagingServiceDetails.API_VERSION.value]}/{domain}/messages",
                auth=(
                    "api",
                    messaging_config.secrets[
                        MessagingServiceSecrets.MAILGUN_API_KEY.value
                    ],
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
        else:
            data["html"] = message.body
            response = requests.post(
                f"{base_url}/{messaging_config.details[MessagingServiceDetails.API_VERSION.value]}/{domain}/messages",
                auth=(
                    "api",
                    messaging_config.secrets[
                        MessagingServiceSecrets.MAILGUN_API_KEY.value
                    ],
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
        logger.error("Email failed to send: {}", Pii(str(e)))
        raise MessageDispatchException(f"Email failed to send due to: {Pii(e)}")


def _twilio_sms_dispatcher(
    messaging_config: MessagingConfig,
    message: str,
    to: Optional[str],
) -> None:
    """Dispatches SMS using Twilio"""
    if not to:
        logger.error("Message failed to send. No phone identity supplied.")
        raise MessageDispatchException("No phone identity supplied.")
    if messaging_config.secrets is None:
        logger.error("Message failed to send. No config secrets supplied.")
        raise MessageDispatchException("No config secrets supplied.")
    account_sid = messaging_config.secrets[
        MessagingServiceSecrets.TWILIO_ACCOUNT_SID.value
    ]
    auth_token = messaging_config.secrets[
        MessagingServiceSecrets.TWILIO_AUTH_TOKEN.value
    ]
    messaging_service_id = messaging_config.secrets[
        MessagingServiceSecrets.TWILIO_MESSAGING_SERVICE_SID.value
    ]
    sender_phone_number = messaging_config.secrets[
        MessagingServiceSecrets.TWILIO_SENDER_PHONE_NUMBER.value
    ]

    client = Client(account_sid, auth_token)
    try:
        if messaging_service_id:
            client.messages.create(
                to=to, messaging_service_sid=messaging_service_id, body=message
            )
        elif sender_phone_number:
            client.messages.create(to=to, from_=sender_phone_number, body=message)
        else:
            logger.error(
                "Message failed to send. Either sender phone number or messaging service sid must be provided."
            )
            raise MessageDispatchException(
                "Message failed to send. Either sender phone number or messaging service sid must be provided."
            )
    except TwilioRestException as e:
        logger.error("Twilio SMS failed to send: {}", Pii(str(e)))
        raise MessageDispatchException(f"Twilio SMS failed to send due to: {Pii(e)}")
