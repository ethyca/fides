import pytest
from jinja2 import Template

from fidesops.ops.common_exceptions import EmailTemplateUnhandledActionType
from fidesops.ops.email_templates import get_email_template
from fidesops.ops.schemas.email.email import EmailActionType


def test_get_email_template_returns_template():
    result = get_email_template(EmailActionType.SUBJECT_IDENTITY_VERIFICATION)
    assert type(result) == Template


def test_get_email_template_exception():
    fake_template = "templateThatDoesNotExist"
    with pytest.raises(EmailTemplateUnhandledActionType) as e:
        get_email_template(fake_template)
        assert e.value == f"No corresponding template linked to the {fake_template}"
