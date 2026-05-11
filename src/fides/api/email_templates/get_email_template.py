import pathlib

import nh3
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from loguru import logger
from markupsafe import Markup

from fides.api.common_exceptions import EmailTemplateUnhandledActionType
from fides.api.email_templates.template_names import (
    CONSENT_REQUEST_EMAIL_FULFILLMENT,
    CONSENT_REQUEST_VERIFICATION_TEMPLATE,
    CORRESPONDENCE,
    EMAIL_ERASURE_REQUEST_FULFILLMENT,
    EXTERNAL_USER_WELCOME,
    MANUAL_TASK_DIGEST,
    PASSWORD_RESET,
    PRIVACY_REQUEST_COMPLETE_ACCESS_TEMPLATE,
    PRIVACY_REQUEST_COMPLETE_DELETION_TEMPLATE,
    PRIVACY_REQUEST_ERROR_NOTIFICATION_TEMPLATE,
    PRIVACY_REQUEST_RECEIPT_TEMPLATE,
    PRIVACY_REQUEST_REVIEW_APPROVE_TEMPLATE,
    PRIVACY_REQUEST_REVIEW_DENY_TEMPLATE,
    SUBJECT_IDENTITY_VERIFICATION_TEMPLATE,
    TEST_MESSAGE_TEMPLATE,
    USER_INVITE,
)
from fides.api.schemas.messaging.messaging import MessagingActionType

pathlib.Path(__file__).parent.resolve()

abs_path_to_current_file_dir = pathlib.Path(__file__).parent.resolve()
template_env = Environment(
    loader=FileSystemLoader(f"{abs_path_to_current_file_dir}/templates"),
    autoescape=select_autoescape(),
)


def _sanitize_html(value: str) -> Markup:
    """Sanitize HTML, preserving safe formatting tags.

    Returns Markup so Jinja2 won't double-escape the result.
    """
    return Markup(nh3.clean(value))


template_env.filters["sanitize_html"] = _sanitize_html


def get_email_template(  # pylint: disable=too-many-return-statements, too-many-branches
    action_type: MessagingActionType,
) -> Template:
    if action_type == MessagingActionType.CONSENT_REQUEST:
        return template_env.get_template(CONSENT_REQUEST_VERIFICATION_TEMPLATE)
    if action_type == MessagingActionType.SUBJECT_IDENTITY_VERIFICATION:
        return template_env.get_template(SUBJECT_IDENTITY_VERIFICATION_TEMPLATE)
    if action_type == MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT:
        return template_env.get_template(EMAIL_ERASURE_REQUEST_FULFILLMENT)
    if action_type == MessagingActionType.CONSENT_REQUEST_EMAIL_FULFILLMENT:
        return template_env.get_template(CONSENT_REQUEST_EMAIL_FULFILLMENT)
    if action_type == MessagingActionType.PRIVACY_REQUEST_RECEIPT:
        return template_env.get_template(PRIVACY_REQUEST_RECEIPT_TEMPLATE)
    if action_type == MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS:
        return template_env.get_template(PRIVACY_REQUEST_COMPLETE_ACCESS_TEMPLATE)
    if action_type == MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION:
        return template_env.get_template(PRIVACY_REQUEST_COMPLETE_DELETION_TEMPLATE)
    if action_type == MessagingActionType.PRIVACY_REQUEST_ERROR_NOTIFICATION:
        return template_env.get_template(PRIVACY_REQUEST_ERROR_NOTIFICATION_TEMPLATE)
    if action_type == MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY:
        return template_env.get_template(PRIVACY_REQUEST_REVIEW_DENY_TEMPLATE)
    if action_type == MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE:
        return template_env.get_template(PRIVACY_REQUEST_REVIEW_APPROVE_TEMPLATE)
    if action_type == MessagingActionType.TEST_MESSAGE:
        return template_env.get_template(TEST_MESSAGE_TEMPLATE)
    if action_type == MessagingActionType.USER_INVITE:
        return template_env.get_template(USER_INVITE)
    if action_type == MessagingActionType.PASSWORD_RESET:
        return template_env.get_template(PASSWORD_RESET)
    if action_type == MessagingActionType.EXTERNAL_USER_WELCOME:
        return template_env.get_template(EXTERNAL_USER_WELCOME)
    if action_type == MessagingActionType.MANUAL_TASK_DIGEST:
        return template_env.get_template(MANUAL_TASK_DIGEST)
    if action_type == MessagingActionType.CORRESPONDENCE:
        return template_env.get_template(CORRESPONDENCE)

    logger.error("No corresponding template linked to the {}", action_type)
    raise EmailTemplateUnhandledActionType(
        f"No corresponding template linked to the {action_type}"
    )
