"""Tests for the correspondence email template."""

from fides.api.email_templates.get_email_template import get_email_template
from fides.api.schemas.messaging.messaging import MessagingActionType


class TestCorrespondenceTemplate:
    def test_template_loads(self):
        template = get_email_template(MessagingActionType.CORRESPONDENCE)
        assert template is not None

    def test_template_renders_with_variables(self):
        template = get_email_template(MessagingActionType.CORRESPONDENCE)
        rendered = template.render(
            subject="Test Subject",
            body="<p>Hello, this is a test.</p>",
        )
        assert "Test Subject" in rendered
        assert "<p>Hello, this is a test.</p>" in rendered

    def test_template_renders_empty_body(self):
        template = get_email_template(MessagingActionType.CORRESPONDENCE)
        rendered = template.render(subject="Empty", body="")
        assert "Empty" in rendered
