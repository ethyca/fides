import logging
import pathlib

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

from fidesops.ops.common_exceptions import EmailTemplateUnhandledActionType
from fidesops.ops.email_templates.template_names import (
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


def get_email_template(action_type: EmailActionType) -> Template:
    if action_type == EmailActionType.SUBJECT_IDENTITY_VERIFICATION:
        return template_env.get_template(SUBJECT_IDENTITY_VERIFICATION_TEMPLATE)

    logger.error("No corresponding template linked to the %s", action_type)
    raise EmailTemplateUnhandledActionType(
        f"No corresponding template linked to the {action_type}"
    )
