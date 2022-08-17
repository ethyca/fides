import logging
from typing import Any, Optional, Union

import requests
from requests import Response
from sqlalchemy.orm import Session

from fidesops.ops.common_exceptions import EmailDispatchException
from fidesops.ops.models.email import EmailConfig
from fidesops.ops.schemas.email.email import (
    EmailActionType,
    EmailForActionType,
    EmailServiceDetails,
    EmailServiceSecrets,
    EmailServiceType,
    SubjectIdentityVerificationBodyParams,
)

logger = logging.getLogger(__name__)


def dispatch_email(
    db: Session,
    action_type: EmailActionType,
    to_email: str,
    email_body_params: Union[SubjectIdentityVerificationBodyParams],
) -> None:
    logger.info("Retrieving email config")
    email_config: Optional[EmailConfig] = db.query(EmailConfig).first()
    if not email_config:
        raise EmailDispatchException("No email config found.")
    if not email_config.secrets:
        logger.warning(
            f"Email secrets not found for config with key: {email_config.key}"
        )
        raise EmailDispatchException(
            f"Email secrets not found for config with key: {email_config.key}"
        )
    logger.info(f"Building appropriate email template for action type: {action_type}")
    email: EmailForActionType = _build_email(
        action_type=action_type, body_params=email_body_params
    )
    email_service: EmailServiceType = email_config.service_type  # type: ignore
    logger.info(f"Retrieving appropriate dispatcher for email service: {email_service}")
    dispatcher: Any = _get_dispatcher_from_config_type(email_service_type=email_service)
    logger.info(
        f"Starting email dispatch for email service with action type: {action_type}"
    )
    dispatcher(email_config=email_config, email=email, to_email=to_email)


def _build_email(
    action_type: EmailActionType,
    body_params: Union[SubjectIdentityVerificationBodyParams],
) -> EmailForActionType:
    if action_type == EmailActionType.SUBJECT_IDENTITY_VERIFICATION:
        return EmailForActionType(
            subject="Your one-time code",
            # for 1st iteration, below will be replaced with actual template files
            body=f"<html>Your one-time code is {body_params.access_code}. Hurry! It expires in 10 minutes.</html>",
        )
    logger.error(f"Email action type {action_type} is not implemented")
    raise EmailDispatchException(f"Email action type {action_type} is not implemented")


def _get_dispatcher_from_config_type(email_service_type: EmailServiceType) -> Any:
    """Determines which dispatcher to use based on email service type"""
    return {
        EmailServiceType.MAILGUN.value: _mailgun_dispatcher,
    }[email_service_type.value]


def _mailgun_dispatcher(
    email_config: EmailConfig, email: EmailForActionType, to_email: str
) -> None:
    """Dispatches email using mailgun"""
    base_url = (
        "https://api.mailgun.net"
        if email_config.details[EmailServiceDetails.IS_EU_DOMAIN.value] is False
        else "https://api.eu.mailgun.net"
    )
    domain = email_config.details[EmailServiceDetails.DOMAIN.value]
    data = {
        "from": f"<mailgun@{domain}>",
        "to": [to_email],
        "subject": email.subject,
        "html": email.body,
    }
    try:
        response: Response = requests.post(
            f"{base_url}/{email_config.details[EmailServiceDetails.API_VERSION.value]}/{domain}/messages",
            auth=(
                "api",
                email_config.secrets[EmailServiceSecrets.MAILGUN_API_KEY.value],  # type: ignore
            ),
            data=data,
        )
        if not response.ok:
            logger.error(
                f"Email failed to send with status code: {response.status_code}"
            )
            raise EmailDispatchException(
                f"Email failed to send with status code {response.status_code}"
            )
    except Exception as e:
        logger.error(e)
        raise EmailDispatchException(format("Email failed to send: %s", str(e)))
