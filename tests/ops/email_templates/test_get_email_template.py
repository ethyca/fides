import pytest
from jinja2 import Template

from fides.api.ops.common_exceptions import EmailTemplateUnhandledActionType
from fides.api.ops.email_templates import get_email_template
from fides.api.ops.schemas.messaging.messaging import MessagingActionType


def test_get_email_template_returns_template():
    result = get_email_template(MessagingActionType.SUBJECT_IDENTITY_VERIFICATION)
    assert type(result) == Template


def test_get_email_template_exception():
    fake_template = "templateThatDoesNotExist"
    with pytest.raises(EmailTemplateUnhandledActionType) as e:
        get_email_template(fake_template)
        assert e.value == f"No corresponding template linked to the {fake_template}"
