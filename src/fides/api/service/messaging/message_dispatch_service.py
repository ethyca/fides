from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional, Union

import requests
from loguru import logger
from sqlalchemy.orm import Session
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from fides.api.common_exceptions import MessageDispatchException
from fides.api.email_templates.get_email_template import get_email_template
from fides.api.models.messaging import (  # type: ignore[attr-defined]
    EMAIL_MESSAGING_SERVICES,
    MessagingConfig,
    get_messaging_method,
)
from fides.api.models.messaging_template import MessagingTemplate
from fides.api.schemas.messaging.messaging import (
    CONFIGURABLE_MESSAGING_ACTION_TYPES,
    AccessRequestCompleteBodyParams,
    ConsentEmailFulfillmentBodyParams,
    EmailForActionType,
    ErasureRequestBodyParams,
    ErrorNotificationBodyParams,
    FidesopsMessage,
    MessagingActionType,
    MessagingMethod,
    MessagingServiceDetails,
    MessagingServiceSecrets,
    MessagingServiceType,
    RequestReceiptBodyParams,
    RequestReviewDenyBodyParams,
    SubjectIdentityVerificationBodyParams,
    UserInviteBodyParams,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.service.messaging.messaging_crud_service import (
    get_basic_messaging_template_by_type_or_default,
    get_enabled_messaging_template_by_type_and_property,
)
from fides.api.tasks import DatabaseTask, celery_app
from fides.api.util.logger import Pii
from fides.config import CONFIG
from fides.config.config_proxy import ConfigProxy
from fides.service.messaging.aws_ses_service import AWS_SES_Service
from fides.service.messaging.mailgun_service import MailgunService
from fides.service.messaging.twilio_email_service import TwilioEmailService

EMAIL_JOIN_STRING = ", "
EMAIL_TEMPLATE_NAME = "fides"


@celery_app.task(base=DatabaseTask, bind=True)
def dispatch_message_task(
    self: DatabaseTask,
    message_meta: Dict[str, Any],
    service_type: Optional[str],
    to_identity: Dict[str, Any],
    property_id: Optional[str],
) -> None:
    """
    A wrapper function to dispatch a message task into the Celery queues
    """
    schema = FidesopsMessage.model_validate(message_meta)
    with self.get_new_session() as db:
        dispatch_message(
            db=db,
            action_type=schema.action_type,
            to_identity=Identity.model_validate(to_identity),
            service_type=service_type,
            message_body_params=schema.body_params,
            property_id=property_id,
        )


def _property_specific_messaging_eligible(db: Session) -> bool:
    """
    Helper method to determine whether property specific messaging is eligible at all. To be eligible:
    1. The ENV must be configured
    2. The messaging type must be set as email. SMS is not yet supported for property-specific messaging.

    This method does not include a check for valid and enabled templates.
    """
    property_specific_messaging_enabled = ConfigProxy(
        db
    ).notifications.enable_property_specific_messaging
    if not property_specific_messaging_enabled:
        return False

    # Only email messaging method is supported when property-specific messaging is enabled.
    service_type = get_email_messaging_config_service_type(db=db)
    if not service_type or get_messaging_method(service_type) != MessagingMethod.EMAIL:
        logger.warning(
            "An email messaging config must be configured if property specific messaging is enabled."
        )
        return False
    return True


def get_property_specific_messaging_template(
    db: Session, property_id: Optional[str], action_type: MessagingActionType
) -> Optional[MessagingTemplate]:
    """
    Returns specific messaging template if one is enabled for a given action type and property.
    """
    is_property_specific_messaging_eligible = _property_specific_messaging_eligible(db)
    if not is_property_specific_messaging_eligible:
        return None

    template = get_enabled_messaging_template_by_type_and_property(
        db=db,
        template_type=action_type.value,
        property_id=property_id,
        use_default_property=True,
    )
    if not template:
        return None
    return template


def message_send_enabled(
    db: Session,
    property_id: Optional[str],
    action_type: MessagingActionType,
    basic_email_template_enabled: bool,
) -> bool:
    """
    Determines whether sending messages from Fides is enabled or disabled.

    Assumes action_type is one of CONFIGURABLE_MESSAGING_ACTION_TYPES.

    Property-specific messaging, if enabled, always takes precedence, and requires checking "enabled" templates for the
    given action type and property.
    """
    property_specific_messaging_enabled = ConfigProxy(
        db
    ).notifications.enable_property_specific_messaging

    if property_specific_messaging_enabled:
        # Only email messaging method is supported when property-specific messaging is enabled.
        service_type = get_email_messaging_config_service_type(db=db)
        if (
            not service_type
            or get_messaging_method(service_type) != MessagingMethod.EMAIL
        ):
            logger.warning(
                "An email messaging config must be configured if property specific messaging is enabled."
            )
            return False
        property_specific_messaging_template = get_property_specific_messaging_template(
            db=db, property_id=property_id, action_type=action_type
        )
        if property_specific_messaging_template:
            return True
    elif basic_email_template_enabled:
        return True
    logger.info("Message send is disabled for action type {}", action_type)
    return False


def dispatch_message(
    db: Session,
    action_type: MessagingActionType,
    *,
    to_identity: Optional[Identity],
    service_type: Optional[str],
    message_body_params: Optional[
        Union[
            AccessRequestCompleteBodyParams,
            ConsentEmailFulfillmentBodyParams,
            SubjectIdentityVerificationBodyParams,
            RequestReceiptBodyParams,
            RequestReviewDenyBodyParams,
            ErasureRequestBodyParams,
            UserInviteBodyParams,
            ErrorNotificationBodyParams,
        ]
    ] = None,
    subject_override: Optional[str] = None,
    property_id: Optional[str] = None,
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
    messaging_template: Optional[MessagingTemplate] = None

    # If property-specific messaging is enabled and message type is one of the configurable templates,
    # we switch over to this mode, regardless of other ENV vars
    if (
        ConfigProxy(db).notifications.enable_property_specific_messaging
        and action_type in CONFIGURABLE_MESSAGING_ACTION_TYPES
    ):
        property_specific_messaging_template = get_property_specific_messaging_template(
            db, property_id, action_type
        )
        if not property_specific_messaging_template:
            logger.warning(
                "Skipping sending property-specific email as no enabled template was found for action type: {}",
                action_type,
            )
            return
        messaging_template = property_specific_messaging_template
    else:
        logger.info(
            "Getting custom messaging template for action type: {}", action_type
        )
        messaging_template = get_basic_messaging_template_by_type_or_default(
            db=db, template_type=action_type.value
        )

    config_proxy = ConfigProxy(db=db)

    if messaging_method == MessagingMethod.EMAIL:
        message = _build_email(
            config_proxy=config_proxy,
            action_type=action_type,
            body_params=message_body_params,
            messaging_template=messaging_template,
        )
    elif messaging_method == MessagingMethod.SMS:
        message = _build_sms(
            action_type=action_type,
            body_params=message_body_params,
        )
    else:  # pragma: no cover
        # This is here as a fail safe, but it should be impossible to reach because
        # is controlled by a database enum field.
        logger.error("Notification service type is not valid: {}", service_type)
        raise MessageDispatchException(
            f"Notification service type is not valid: {service_type}"
        )
    messaging_service: MessagingServiceType = messaging_config.service_type  # type: ignore
    logger.info(
        "Retrieving appropriate dispatcher for email service: {}", messaging_service
    )
    dispatcher: Optional[Callable] = _get_dispatcher_from_config_type(
        message_service_type=messaging_service
    )
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

    if subject_override and isinstance(message, EmailForActionType):
        message.subject = subject_override

    to = (
        to_identity.email
        if messaging_method == MessagingMethod.EMAIL
        else to_identity.phone_number
    )

    if not to:
        error_message = f"No {'email' if messaging_method == MessagingMethod.EMAIL else 'phone'} identity supplied."
        logger.error(f"Message failed to send. {error_message}")
        raise MessageDispatchException(error_message)

    dispatcher(
        messaging_config,
        message,
        to,
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
            f"Your consent request verification code is {body_params.verification_code}. "
            "Please return to the consent request page and enter the code to continue. "
            f"This code will expire in {body_params.get_verification_code_ttl_minutes()} minutes"
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_RECEIPT:
        if len(body_params.request_types) > 1:
            return f"The following requests have been received: {separator.join(body_params.request_types)}"
        return f"Your {body_params.request_types[0]} request has been received"
    if action_type == MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS:
        # Converting the expiration time to days
        subject_request_download_time_in_days = (
            CONFIG.security.subject_request_download_link_ttl_seconds / 86400
        )
        if len(body_params.download_links) > 1:
            return (
                "Your data access has been completed and can be downloaded at the following links. "
                f"For security purposes, these secret links will expire in {subject_request_download_time_in_days} days: "
                f"{separator.join(body_params.download_links)}"
            )
        return (
            f"Your data access has been completed and can be downloaded at {body_params.download_links[0]}. "
            f"For security purposes, this secret link will expire in {subject_request_download_time_in_days} days."
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION:
        return "Your privacy request for deletion has been completed."
    if action_type == MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE:
        return "Your privacy request has been approved and is currently processing."
    if action_type == MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY:
        if body_params.rejection_reason:
            return f"Your privacy request has been denied for the following reason: {body_params.rejection_reason}"
        return "Your privacy request has been denied."
    if action_type == MessagingActionType.TEST_MESSAGE:
        return "Test message from Fides."
    logger.error("Message action type {} is not implemented", action_type)
    raise MessageDispatchException(
        f"Message action type {action_type} is not implemented"
    )


def _render(template_str: str, variables: Optional[Dict] = None) -> str:
    """Helper function to render a template string with the provided variables."""
    if variables is None:
        variables = {}

    for key, value in variables.items():
        template_str = template_str.replace(f"__{key.upper()}__", str(value))

    return template_str


def _build_email(  # pylint: disable=too-many-return-statements
    config_proxy: ConfigProxy,
    action_type: MessagingActionType,
    body_params: Any,
    messaging_template: Optional[MessagingTemplate] = None,
) -> EmailForActionType:
    """
    Builds an email for a specified messaging action type, using the provided parameters.

    The messaging_template parameter is used as the template for the email wording, and
    its rendered output is passed to the HTML templates. This is only applicable for action
    types that allow the user to specify a custom messaging template.

    Parameters:
        action_type (MessagingActionType): The type of messaging action for which the email is being built.
        body_params (Any): Parameters used to populate the email body, such as verification codes.
        messaging_template (Optional[MessagingTemplate]): An optional custom messaging template for the email wording.
            This parameter is used to define the subject and body of the email, and its rendered output is
            passed to the HTML templates. Only applicable for action types in CONFIGURABLE_MESSAGING_ACTION_TYPES.

    Returns:
        EmailForActionType: The constructed email object with the subject and body populated based on the action type.
    """
    if action_type == MessagingActionType.SUBJECT_IDENTITY_VERIFICATION:
        variables = {
            "code": body_params.verification_code,
            "minutes": body_params.get_verification_code_ttl_minutes(),
        }
        return EmailForActionType(
            subject=_render(messaging_template.content["subject"], variables),  # type: ignore
            body=_render(messaging_template.content["body"], variables),  # type: ignore
            template_variables=variables,
        )
    if action_type == MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT:
        base_template = get_email_template(action_type)
        return EmailForActionType(
            subject=f"Notification of user erasure requests from {body_params.controller}",
            body=base_template.render(
                {
                    "controller": body_params.controller,
                    "third_party_vendor_name": body_params.third_party_vendor_name,
                    "identities": body_params.identities,
                }
            ),
        )
    if action_type == MessagingActionType.CONSENT_REQUEST_EMAIL_FULFILLMENT:
        base_template = get_email_template(action_type)
        return EmailForActionType(
            subject="Notification of users' consent preference changes",
            body=base_template.render({"body": body_params}),
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_RECEIPT:
        variables = {"request_types": body_params.request_types}
        return EmailForActionType(
            subject=_render(messaging_template.content["subject"], variables),  # type: ignore
            body=_render(messaging_template.content["body"], variables),  # type: ignore
            template_variables=variables,
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS:
        variables = {
            "download_link": body_params.download_links[0],
            "days": body_params.subject_request_download_time_in_days,
        }
        return EmailForActionType(
            subject=_render(messaging_template.content["subject"], variables),  # type: ignore
            body=_render(messaging_template.content["body"], variables),  # type: ignore
            template_variables=variables,
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION:
        return EmailForActionType(
            subject=_render(messaging_template.content["subject"]),  # type: ignore
            body=_render(messaging_template.content["body"]),  # type: ignore
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_ERROR_NOTIFICATION:
        # This action type does not use the default templates that are configurable in the Admin-UI.
        # They are instead hard-coded in fides, which we retrieve using get_email_template(action_type)
        base_template = get_email_template(action_type)
        return EmailForActionType(
            subject="Privacy Request Error Alert",
            body=base_template.render(),
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE:
        return EmailForActionType(
            subject=_render(messaging_template.content["subject"]),  # type: ignore
            body=_render(messaging_template.content["body"]),  # type: ignore
        )
    if action_type == MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY:
        variables = {"denial_reason": body_params.rejection_reason}
        return EmailForActionType(
            subject=_render(messaging_template.content["subject"], variables),  # type: ignore
            body=_render(messaging_template.content["body"], variables),  # type: ignore
            template_variables=variables,
        )
    if action_type == MessagingActionType.TEST_MESSAGE:
        # This action type does not use the default templates that are configurable in the Admin-UI.
        # They are instead hard-coded in fides, which we retrieve using get_email_template(action_type)
        base_template = get_email_template(action_type)
        return EmailForActionType(
            subject="Test message from fides", body=base_template.render()
        )
    if action_type == MessagingActionType.USER_INVITE:
        base_template = get_email_template(action_type)
        return EmailForActionType(
            subject="Welcome to Fides",
            body=base_template.render(
                {
                    "admin_ui_url": config_proxy.admin_ui.url,
                    "username": body_params.username,
                    "invite_code": body_params.invite_code,
                }
            ),
        )
    logger.error("Message action type {} is not implemented", action_type)
    raise MessageDispatchException(
        f"Message action type {action_type} is not implemented"
    )


def _get_dispatcher_from_config_type(
    message_service_type: MessagingServiceType,
) -> Optional[Callable]:
    """Determines which dispatcher to use based on message service type"""
    handler = {
        MessagingServiceType.mailgun: _mailgun_dispatcher,
        MessagingServiceType.mailchimp_transactional: _mailchimp_transactional_dispatcher,
        MessagingServiceType.twilio_text: _twilio_sms_dispatcher,
        MessagingServiceType.twilio_email: _twilio_email_dispatcher,
        MessagingServiceType.aws_ses: _aws_ses_dispatcher,
    }
    return handler.get(message_service_type)  # type: ignore


def validate_config(
    messaging_config: MessagingConfig,
    config_name: str,
    validate_details: Optional[bool] = True,
) -> None:
    """
    Validates that the messaging config has the required details and secrets.
    """
    condition = (
        not messaging_config.details or not messaging_config.secrets
        if validate_details
        else not messaging_config.secrets
    )

    if condition:
        error_message = f"No {config_name} config {'details or secrets' if validate_details else 'secrets'} supplied."
        logger.error(f"Message failed to send. {error_message}")
        raise MessageDispatchException(error_message)


def _mailchimp_transactional_dispatcher(
    messaging_config: MessagingConfig,
    message: EmailForActionType,
    to: str,
) -> None:
    """Dispatches email using Mailchimp Transactional"""
    validate_config(messaging_config, "Mailchimp Transactional")

    from_email = messaging_config.details[MessagingServiceDetails.EMAIL_FROM.value]
    data = json.dumps(
        {
            "key": messaging_config.secrets[
                MessagingServiceSecrets.MAILCHIMP_TRANSACTIONAL_API_KEY.value
            ],
            "message": {
                "from_email": from_email,
                "subject": message.subject,
                "html": message.body,
                # On Mailchimp Transactional's free plan `to` must be an email of the same
                # domain as `from_email`
                "to": [{"email": to.strip(), "type": "to"}],
            },
        }
    )

    response = requests.post(
        "https://mandrillapp.com/api/1.0/messages/send",
        headers={"Content-Type": "application/json"},
        data=data,
    )
    if not response.ok:
        logger.error("Email failed to send with status code: %s", response.status_code)
        raise MessageDispatchException(
            f"Email failed to send with status code {response.status_code}"
        )

    send_data = response.json()[0]
    email_rejected = send_data.get("status", "rejected") == "rejected"
    if email_rejected:
        reason = send_data.get("reject_reason", "Fides Error")
        explanations = {
            "soft-bounce": "A temporary error occured with the target inbox. For example, this inbox could be full. See https://mailchimp.com/developer/transactional/docs/reputation-rejections/#bounces for more info.",
            "hard-bounce": "A permanent error occured with the target inbox. See https://mailchimp.com/developer/transactional/docs/reputation-rejections/#bounces for more info.",
            "recipient-domain-mismatch": f"You are not authorised to send email to this domain from {from_email}.",
            "unsigned": f"The sending domain for {from_email} has not been fully configured for Mailchimp Transactional. See https://mailchimp.com/developer/transactional/docs/authentication-delivery/#authentication/ for more info.",
        }
        explanation = explanations.get(reason, "")
        raise MessageDispatchException(
            f"Verification email unable to send due to reason: {reason}. {explanation}"
        )


def _mailgun_dispatcher(
    messaging_config: MessagingConfig,
    message: EmailForActionType,
    to: str,
) -> None:
    """Dispatches email using Mailgun"""
    validate_config(messaging_config, "Mailgun")

    mailgun_service = MailgunService(messaging_config)
    mailgun_service.send_message(message, to)


def _twilio_email_dispatcher(
    messaging_config: MessagingConfig,
    message: EmailForActionType,
    to: str,
) -> None:
    """Dispatches email using twilio sendgrid"""
    validate_config(messaging_config, "Twilio email")

    twilio_email_service = TwilioEmailService(messaging_config)
    twilio_email_service.send_message(message, to)


def _twilio_sms_dispatcher(
    messaging_config: MessagingConfig,
    message: str,
    to: str,
) -> None:
    """Dispatches SMS using Twilio"""
    validate_config(messaging_config, "Twilio SMS", validate_details=False)

    account_sid = messaging_config.secrets[
        MessagingServiceSecrets.TWILIO_ACCOUNT_SID.value
    ]
    auth_token = messaging_config.secrets[
        MessagingServiceSecrets.TWILIO_AUTH_TOKEN.value
    ]
    messaging_service_id = messaging_config.secrets.get(
        MessagingServiceSecrets.TWILIO_MESSAGING_SERVICE_SID.value
    )
    sender_phone_number = messaging_config.secrets.get(
        MessagingServiceSecrets.TWILIO_SENDER_PHONE_NUMBER.value
    )

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


def _aws_ses_dispatcher(
    messaging_config: MessagingConfig,
    message: EmailForActionType,
    to: str,
) -> None:
    validate_config(messaging_config, "AWS SES")

    aws_ses_serivce = AWS_SES_Service(messaging_config)
    aws_ses_serivce.send_message(message, to)


def get_email_messaging_config_service_type(db: Session) -> Optional[str]:
    """
    Email connectors require that an email messaging service has been configured.
    Prefers Twilio if both Twilio email AND Mailgun has been configured.
    """

    # if there's a specified messaging service type, and it's an email service, we use that
    if (
        configured_service_type := ConfigProxy(
            db
        ).notifications.notification_service_type
    ) is not None and configured_service_type in EMAIL_MESSAGING_SERVICES:
        return configured_service_type

    # if no specified messaging service type, fall back to hardcoded preference hierarchy
    messaging_configs: Optional[List[MessagingConfig]] = MessagingConfig.query(
        db=db
    ).all()
    if not messaging_configs:
        # let messaging dispatch service handle non-existent service
        return None

    twilio_email_config = next(
        (
            config
            for config in messaging_configs
            if config.service_type == MessagingServiceType.twilio_email
        ),
        None,
    )
    if twilio_email_config:
        # First choice: use Twilio
        return MessagingServiceType.twilio_email.value

    mailgun_config = next(
        (
            config
            for config in messaging_configs
            if config.service_type == MessagingServiceType.mailgun
        ),
        None,
    )
    if mailgun_config:
        # Second choice: use Mailgun
        return MessagingServiceType.mailgun.value

    mailchimp_transactional_config = next(
        (
            config
            for config in messaging_configs
            if config.service_type == MessagingServiceType.mailchimp_transactional
        ),
        None,
    )
    if mailchimp_transactional_config:
        # Third choice: use Mailchimp Transactional
        return MessagingServiceType.mailchimp_transactional.value

    return None
