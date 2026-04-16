from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from loguru import logger
from requests.exceptions import RequestException, Timeout
from sqlalchemy.orm import Session
from twilio.base.exceptions import TwilioRestException

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
    ExternalUserWelcomeBodyParams,
    FidesopsMessage,
    ManualTaskDigestBodyParams,
    MessagingActionType,
    MessagingMethod,
    MessagingServiceType,
    PasswordResetBodyParams,
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
from fides.api.service.messaging.messaging_providers.aws_ses_service import (
    AwsSesService,
)
from fides.api.service.messaging.messaging_providers.base import (
    BaseEmailProviderService,
    BaseMessageProviderService,
    BaseSMSProviderService,
)
from fides.api.service.messaging.messaging_providers.mailchimp_transactional_service import (
    MailchimpTransactionalService,
)
from fides.api.service.messaging.messaging_providers.mailgun_service import (
    MailgunService,
)
from fides.api.service.messaging.messaging_providers.twilio_email_service import (
    TwilioEmailService,
)
from fides.api.service.messaging.messaging_providers.twilio_sms_service import (
    TwilioSmsService,
)
from fides.api.tasks import DatabaseTask, celery_app
from fides.config import CONFIG
from fides.config.config_proxy import ConfigProxy

EMAIL_JOIN_STRING = ", "


def _resolve_provider_map() -> dict[
    MessagingServiceType, type[BaseMessageProviderService]
]:
    """Build provider map at call time so test mocks of provider classes are respected."""
    return {
        MessagingServiceType.mailgun: MailgunService,
        MessagingServiceType.mailchimp_transactional: MailchimpTransactionalService,
        MessagingServiceType.twilio_text: TwilioSmsService,
        MessagingServiceType.twilio_email: TwilioEmailService,
        MessagingServiceType.aws_ses: AwsSesService,
    }


# Static reference for completeness invariant tests
PROVIDER_MAP: dict[MessagingServiceType, type[BaseMessageProviderService]] = (
    _resolve_provider_map()
)


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    autoretry_for=(
        Timeout,
        RequestException,
        TwilioRestException,
    ),
    retry_kwargs={"max_retries": 3},
    retry_backoff=2,
    retry_jitter=True,
)
def dispatch_message_task(
    self: DatabaseTask,
    message_meta: Dict[str, Any],
    service_type: Optional[str],
    to_identity: Dict[str, Any],
    property_id: Optional[str],
) -> None:
    """
    A wrapper function to dispatch a message task into the Celery queues.

    This task will automatically retry up to 3 times on transient network failures
    (timeouts, connection errors, temporary service unavailability) with exponential
    backoff (2s, 4s, 8s) and jitter to prevent thundering herd issues.

    Permanent errors (missing config, invalid identities, etc.) will fail immediately
    without retry to provide fast feedback and avoid wasting worker resources.
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
            PasswordResetBodyParams,
            ErrorNotificationBodyParams,
            ExternalUserWelcomeBodyParams,
            ManualTaskDigestBodyParams,
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
        "Retrieving appropriate provider for messaging service: {}", messaging_service
    )
    provider_cls = _resolve_provider_map().get(messaging_service)
    if not provider_cls:
        logger.error(
            "Dispatcher has not been implemented for message service type: {}",
            messaging_service,
        )
        raise MessageDispatchException(
            f"Dispatcher has not been implemented for message service type: {messaging_service}"
        )

    provider = provider_cls(messaging_config)

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

    if isinstance(provider, BaseEmailProviderService):
        if not isinstance(message, EmailForActionType):
            raise MessageDispatchException(
                "Expected EmailForActionType for email provider"
            )
        provider.send_email(to, message)
    elif isinstance(provider, BaseSMSProviderService):
        if not isinstance(message, str):
            raise MessageDispatchException("Expected str body for SMS provider")
        provider.send_sms(to, message)
    else:
        raise MessageDispatchException(
            f"Provider {type(provider).__name__} is not a recognized email or SMS provider"
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
    if action_type == MessagingActionType.PRIVACY_REQUEST_COMPLETE_CONSENT:
        return "Your consent request has been completed."
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


def _build_email(  # pylint: disable=too-many-return-statements, too-many-branches, too-many-statements
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
    if action_type == MessagingActionType.PRIVACY_REQUEST_COMPLETE_CONSENT:
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
    if action_type == MessagingActionType.PASSWORD_RESET:
        base_template = get_email_template(action_type)
        return EmailForActionType(
            subject="Fides Password Reset",
            body=base_template.render(
                {
                    "admin_ui_url": config_proxy.admin_ui.url,
                    "username": body_params.username,
                    "reset_token": body_params.reset_token,
                    "ttl_minutes": body_params.ttl_minutes,
                }
            ),
        )
    if action_type == MessagingActionType.EXTERNAL_USER_WELCOME:
        # Generate display name for personalization
        display_name = body_params.username
        if body_params.first_name:
            display_name = body_params.first_name
            if body_params.last_name:
                display_name = f"{body_params.first_name} {body_params.last_name}"

        portal_link = (
            f"{body_params.privacy_center_url}?access_token={body_params.access_token}"
        )

        variables = {
            "username": body_params.username,
            "display_name": display_name,
            "first_name": body_params.first_name,
            "last_name": body_params.last_name,
            "org_name": body_params.org_name,
            "portal_link": portal_link,
            "privacy_center_url": body_params.privacy_center_url,
            "access_token": body_params.access_token,
        }

        # Start with default subject
        subject = "Welcome to our Privacy Center"

        # If messaging template exists, extract customizable content
        if messaging_template:
            # Use custom subject if provided
            if "subject" in messaging_template.content:
                subject = _render(messaging_template.content["subject"], variables)

            # Use custom body content to replace the intro text in HTML template
            custom_body = messaging_template.content.get("body", "")
            if custom_body.strip():
                # Replace the default intro text with the custom body content
                rendered_custom_body = _render(custom_body, variables)
                variables["custom_intro"] = rendered_custom_body

        # Always use the HTML template
        base_template = get_email_template(action_type)
        return EmailForActionType(
            subject=subject,
            body=base_template.render(variables),
            template_variables=variables,
        )

    if action_type == MessagingActionType.MANUAL_TASK_DIGEST:
        variables = {
            "vendor_contact_name": body_params.vendor_contact_name,
            "organization_name": body_params.organization_name,
            "portal_url": body_params.portal_url,
            "imminent_task_count": body_params.imminent_task_count,
            "upcoming_task_count": body_params.upcoming_task_count,
            "total_task_count": body_params.total_task_count,
            "company_logo_url": body_params.company_logo_url,
        }

        # Start with default subject
        subject = f"Weekly DSR Summary from {body_params.organization_name}"

        # If messaging template exists, extract customizable content
        if messaging_template:
            # Use custom subject if provided
            if "subject" in messaging_template.content:
                subject = _render(messaging_template.content["subject"], variables)

            # Use custom body content to replace the intro text in HTML template
            custom_body = messaging_template.content.get("body", "")
            if custom_body.strip():
                # Replace the default intro text with the custom body content
                rendered_custom_body = _render(custom_body, variables)
                variables["intro_text"] = rendered_custom_body

        # Always use the HTML template
        base_template = get_email_template(action_type)
        return EmailForActionType(
            subject=subject,
            body=base_template.render(variables),
            template_variables=variables,
        )

    logger.error("Message action type {} is not implemented", action_type)
    raise MessageDispatchException(
        f"Message action type {action_type} is not implemented"
    )


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
