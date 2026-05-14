"""Tests for the correspondence email template."""

import nh3

from fides.api.email_templates.get_email_template import (
    INBOUND_ALLOWED_ATTRIBUTES,
    INBOUND_ALLOWED_TAGS,
    INBOUND_URL_SCHEMES,
    get_email_template,
)
from fides.api.schemas.messaging.messaging import MessagingActionType


class TestCorrespondenceTemplate:
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

    def test_template_sanitizes_malicious_html(self):
        template = get_email_template(MessagingActionType.CORRESPONDENCE)
        rendered = template.render(
            subject="Safe Subject",
            body='<p>Hello</p><script>alert("xss")</script>',
        )
        assert "<p>Hello</p>" in rendered
        assert "<script>" not in rendered

    def test_template_allows_rich_formatting(self):
        """Outbound allowlist permits images and tables for operator content."""
        template = get_email_template(MessagingActionType.CORRESPONDENCE)
        rendered = template.render(
            subject="Test",
            body='<p>Text</p><img src="https://example.com/logo.png" alt="logo"><table><tr><td>cell</td></tr></table>',
        )
        assert "<p>Text</p>" in rendered
        assert "<img" in rendered
        assert "<table>" in rendered
        assert "<td>cell</td>" in rendered

    def test_template_strips_dangerous_tags(self):
        """Outbound allowlist still blocks script, iframe, form, etc."""
        template = get_email_template(MessagingActionType.CORRESPONDENCE)
        rendered = template.render(
            subject="Test",
            body='<p>Safe</p><iframe src="http://evil.com"></iframe><form action="/steal"><input></form>',
        )
        assert "<p>Safe</p>" in rendered
        assert "<iframe" not in rendered
        assert "<form" not in rendered
        assert "<input" not in rendered

    def test_template_blocks_javascript_uris(self):
        """Outbound blocks javascript: URIs but allows http/https."""
        template = get_email_template(MessagingActionType.CORRESPONDENCE)
        rendered = template.render(
            subject="Test",
            body='<a href="javascript:alert(1)">click</a><a href="https://safe.com">safe</a>',
        )
        assert "javascript:" not in rendered
        assert 'href="https://safe.com"' in rendered

    def test_subject_is_html_escaped(self):
        """subject uses Jinja2 autoescape, not sanitize_html."""
        template = get_email_template(MessagingActionType.CORRESPONDENCE)
        rendered = template.render(
            subject='<script>alert("xss")</script>',
            body="<p>Safe body</p>",
        )
        assert "<script>" not in rendered
        assert "&lt;script&gt;" in rendered


class TestInboundSanitization:
    """Tests for the inbound (data subject reply) allowlist."""

    def _clean(self, html: str) -> str:
        return nh3.clean(
            html,
            tags=INBOUND_ALLOWED_TAGS,
            attributes=INBOUND_ALLOWED_ATTRIBUTES,
            url_schemes=INBOUND_URL_SCHEMES,
        )

    def test_allows_basic_formatting(self):
        result = self._clean(
            "<p>Hello</p><strong>bold</strong><a href='https://example.com'>link</a>"
        )
        assert "<p>Hello</p>" in result
        assert "<strong>bold</strong>" in result
        assert "<a href" in result

    def test_strips_images(self):
        result = self._clean('<p>Hi</p><img src="http://tracker.com/pixel.gif">')
        assert "<p>Hi</p>" in result
        assert "<img" not in result

    def test_strips_tables(self):
        result = self._clean("<table><tr><td>data</td></tr></table>")
        assert "<table" not in result
        assert "data" in result

    def test_strips_scripts_and_forms(self):
        result = self._clean('<script>alert("xss")</script><form><input></form>')
        assert "<script" not in result
        assert "<form" not in result

    def test_blocks_javascript_and_http_uris(self):
        """Inbound allows https/mailto only — blocks javascript: and http:."""
        result = self._clean(
            '<a href="javascript:alert(1)">xss</a>'
            '<a href="http://insecure.com">http</a>'
            '<a href="https://safe.com">safe</a>'
            '<a href="mailto:user@example.com">email</a>'
        )
        assert "javascript:" not in result
        assert "http://insecure.com" not in result
        assert 'href="https://safe.com"' in result
        assert 'href="mailto:user@example.com"' in result
