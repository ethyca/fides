import logging
import pathlib

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

from fidesops.ops.common_exceptions import EmailTemplateUnhandledActionType
from fidesops.ops.email_templates.template_names import (
    CONSENT_REQUEST_VERIFICATION_TEMPLATE,
    EMAIL_ERASURE_REQUEST_FULFILLMENT,
    PRIVACY_REQUEST_COMPLETE_ACCESS_TEMPLATE,
    PRIVACY_REQUEST_COMPLETE_DELETION_TEMPLATE,
    PRIVACY_REQUEST_RECEIPT_TEMPLATE,
    PRIVACY_REQUEST_REVIEW_APPROVE_TEMPLATE,
    PRIVACY_REQUEST_REVIEW_DENY_TEMPLATE,
    SUBJECT_IDENTITY_VERIFICATION_TEMPLATE,
)
from fidesops.ops.schemas.email.email import EmailActionType

pathlib.Path(__file__).parent.resolve()
logger = logging.getLogger(__name__)

abs_path_to_current_file_dir = pathlib.Path(__file__).parent.resolve()
template_env = Environment(
    loader=FileSystemLoader(f"{abs_path_to_current_file_dir}/templates"),
    autoescape=select_autoescape(),
)


def get_email_template(  # pylint: disable=too-many-return-statements
    action_type: EmailActionType,
) -> Template:
    if action_type == EmailActionType.CONSENT_REQUEST:
        return template_env.get_template(CONSENT_REQUEST_VERIFICATION_TEMPLATE)
    if action_type == EmailActionType.SUBJECT_IDENTITY_VERIFICATION:
        return template_env.get_template(SUBJECT_IDENTITY_VERIFICATION_TEMPLATE)
    if action_type == EmailActionType.EMAIL_ERASURE_REQUEST_FULFILLMENT:
        return template_env.get_template(EMAIL_ERASURE_REQUEST_FULFILLMENT)
    if action_type == EmailActionType.PRIVACY_REQUEST_RECEIPT:
        return template_env.get_template(PRIVACY_REQUEST_RECEIPT_TEMPLATE)
    if action_type == EmailActionType.PRIVACY_REQUEST_COMPLETE_ACCESS:
        return template_env.get_template(PRIVACY_REQUEST_COMPLETE_ACCESS_TEMPLATE)
    if action_type == EmailActionType.PRIVACY_REQUEST_COMPLETE_DELETION:
        return template_env.get_template(PRIVACY_REQUEST_COMPLETE_DELETION_TEMPLATE)
    if action_type == EmailActionType.PRIVACY_REQUEST_REVIEW_DENY:
        return template_env.get_template(PRIVACY_REQUEST_REVIEW_DENY_TEMPLATE)
    if action_type == EmailActionType.PRIVACY_REQUEST_REVIEW_APPROVE:
        return template_env.get_template(PRIVACY_REQUEST_REVIEW_APPROVE_TEMPLATE)

    logger.error("No corresponding template linked to the %s", action_type)
    raise EmailTemplateUnhandledActionType(
        f"No corresponding template linked to the {action_type}"
    )
