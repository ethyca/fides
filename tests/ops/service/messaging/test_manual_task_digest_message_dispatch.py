from unittest import mock
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session
from tests.fixtures.messaging_fixtures import mailgun_post_body
from tests.ops.test_helpers.email_test_utils import assert_url_hostname_present

from fides.api.models.messaging_template import MessagingTemplate
from fides.api.schemas.messaging.messaging import (
    ManualTaskDigestBodyParams,
    MessagingActionType,
    MessagingServiceType,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.service.messaging.message_dispatch_service import dispatch_message


@pytest.mark.unit
class TestManualTaskDigestMessageDispatch:
    """Test manual task digest message dispatch functionality."""

    def test_manual_task_digest_email_dispatch_mailgun_success(
        self,
        db: Session,
        messaging_config,
        mock_mailgun_http,
    ) -> None:
        """Test successful dispatch of manual task digest email via Mailgun."""
        dispatch_message(
            db=db,
            action_type=MessagingActionType.MANUAL_TASK_DIGEST,
            to_identity=Identity(**{"email": "vendor@example.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=ManualTaskDigestBodyParams(
                vendor_contact_name="Jane Doe",
                organization_name="Acme Corp",
                portal_url="https://privacy.example.com/external-tasks?access_token=abc123",
                imminent_task_count=3,
                upcoming_task_count=7,
                total_task_count=10,
                company_logo_url=None,
            ),
        )

        assert mock_mailgun_http.called
        body = mailgun_post_body(mock_mailgun_http.request_history)

        assert body["to"] == ["vendor@example.com"]

        # Check email content
        assert body["subject"] == ["Weekly DSR Summary from Acme Corp"]
        html = body["html"][0]
        assert "Hi Jane Doe," in html
        assert "Acme Corp" in html
        assert "You have 10 requests coming due" in html  # total tasks
        assert "3 within the next 7 days" in html  # imminent tasks
        assert "7 due in the next period" in html  # upcoming tasks
        # Validate that URLs with the expected hostname are present in the email
        assert_url_hostname_present(html, "privacy.example.com")

    def test_manual_task_digest_email_dispatch_with_logo(
        self,
        db: Session,
        messaging_config,
        mock_mailgun_http,
    ) -> None:
        """Test manual task digest email dispatch with company logo URL in template variables."""
        dispatch_message(
            db=db,
            action_type=MessagingActionType.MANUAL_TASK_DIGEST,
            to_identity=Identity(**{"email": "vendor@example.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=ManualTaskDigestBodyParams(
                vendor_contact_name="John Smith",
                organization_name="Test Organization",
                portal_url="https://portal.test.com/external-tasks",
                imminent_task_count=2,
                upcoming_task_count=3,
                total_task_count=5,
                company_logo_url="https://example.com/logo.png",
            ),
        )

        assert mock_mailgun_http.called
        body = mailgun_post_body(mock_mailgun_http.request_history)
        html = body["html"][0]

        # Check that the HTML template is used with logo functionality
        assert "Test Organization" in html
        assert "John Smith" in html
        assert "You have 5 requests coming due" in html  # total tasks
        assert "2 within the next 7 days" in html  # imminent tasks
        assert "3 due in the next period" in html  # upcoming tasks

        # Should contain HTML tags (since it's the HTML template)
        assert "<div" in html
        assert "<html" in html
        assert "email-container" in html

        # Check logo URL is present in the HTML
        assert "https://example.com/logo.png" in html

    def test_manual_task_digest_email_dispatch_zero_tasks(
        self,
        db: Session,
        messaging_config,
        mock_mailgun_http,
    ) -> None:
        """Test manual task digest email dispatch with zero tasks."""
        dispatch_message(
            db=db,
            action_type=MessagingActionType.MANUAL_TASK_DIGEST,
            to_identity=Identity(**{"email": "vendor@example.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=ManualTaskDigestBodyParams(
                vendor_contact_name="Test User",
                organization_name="My Company",
                portal_url="http://localhost:3001/external-tasks",
                imminent_task_count=0,
                upcoming_task_count=0,
                total_task_count=0,
                company_logo_url=None,
            ),
        )

        assert mock_mailgun_http.called
        body = mailgun_post_body(mock_mailgun_http.request_history)
        html = body["html"][0]

        # Check that zero counts are handled correctly (HTML template format)
        assert "You have 0 request" in html  # HTML template handles pluralization

        # Should contain HTML tags (since it's the HTML template)
        assert "<div" in html
        assert "<html" in html
        assert "email-container" in html

        # Check that zero counts appear in the HTML
        assert "0 within the next 7 days" in html
        assert "0 due in the next period" in html

    def test_manual_task_digest_body_params_validation(self) -> None:
        """Test that ManualTaskDigestBodyParams validates correctly."""
        # Test valid params
        valid_params = ManualTaskDigestBodyParams(
            vendor_contact_name="Jane Doe",
            organization_name="Acme Corp",
            portal_url="https://example.com/portal",
            imminent_task_count=5,
            upcoming_task_count=10,
            total_task_count=15,
            company_logo_url="https://example.com/logo.png",
        )

        assert valid_params.vendor_contact_name == "Jane Doe"
        assert valid_params.organization_name == "Acme Corp"
        assert valid_params.portal_url == "https://example.com/portal"
        assert valid_params.imminent_task_count == 5
        assert valid_params.upcoming_task_count == 10
        assert valid_params.total_task_count == 15
        assert valid_params.company_logo_url == "https://example.com/logo.png"

        # Test with optional logo URL as None
        params_no_logo = ManualTaskDigestBodyParams(
            vendor_contact_name="John Smith",
            organization_name="Test Org",
            portal_url="https://test.com",
            imminent_task_count=1,
            upcoming_task_count=2,
            total_task_count=3,
            company_logo_url=None,
        )

        assert params_no_logo.company_logo_url is None

    def test_manual_task_digest_email_dispatch_special_characters(
        self,
        db: Session,
        messaging_config,
        mock_mailgun_http,
    ) -> None:
        """Test manual task digest email dispatch with special characters in names."""
        dispatch_message(
            db=db,
            action_type=MessagingActionType.MANUAL_TASK_DIGEST,
            to_identity=Identity(**{"email": "vendor@example.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=ManualTaskDigestBodyParams(
                vendor_contact_name="María José García-López",
                organization_name="Acme Corp & Associates, LLC",
                portal_url="https://privacy.example.com/external-tasks?token=abc123&user=test",
                imminent_task_count=1,
                upcoming_task_count=1,
                total_task_count=2,
                company_logo_url=None,
            ),
        )

        assert mock_mailgun_http.called
        body = mailgun_post_body(mock_mailgun_http.request_history)
        html = body["html"][0]

        # Check that special characters are handled correctly
        assert "María José García-López" in html
        # HTML template should escape HTML entities
        assert "Acme Corp &amp; Associates, LLC" in html

        # Should contain HTML tags (since it's the HTML template)
        assert "<div" in html
        assert "<html" in html
        assert "email-container" in html
        # Validate that URLs with the expected hostname are present in the email
        assert_url_hostname_present(html, "privacy.example.com")

    def test_manual_task_digest_email_dispatch_with_custom_template(
        self,
        db: Session,
        messaging_config,
        mock_mailgun_http,
    ) -> None:
        """Test manual task digest email dispatch using custom template from UI."""
        custom_template = MessagingTemplate.create(
            db=db,
            data={
                "type": MessagingActionType.MANUAL_TASK_DIGEST.value,
                "label": "Custom manual task digest",
                "content": {
                    "subject": "Custom Digest: __ORGANIZATION_NAME__ Tasks",
                    "body": "Hello __VENDOR_CONTACT_NAME__, you have __IMMINENT_TASK_COUNT__ urgent tasks and __UPCOMING_TASK_COUNT__ upcoming tasks from __ORGANIZATION_NAME__. Please visit our portal to review these tasks.",
                },
                "is_enabled": True,
            },
        )

        dispatch_message(
            db=db,
            action_type=MessagingActionType.MANUAL_TASK_DIGEST,
            to_identity=Identity(**{"email": "vendor@example.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=ManualTaskDigestBodyParams(
                vendor_contact_name="John Smith",
                organization_name="Custom Corp",
                portal_url="https://privacy.example.com/tasks",
                imminent_task_count=2,
                upcoming_task_count=5,
                total_task_count=7,
                company_logo_url=None,
            ),
        )

        # Verify custom template was used
        assert mock_mailgun_http.called
        body = mailgun_post_body(mock_mailgun_http.request_history)
        html = body["html"][0]

        # Check that custom template content was used within HTML template
        assert body["subject"] == ["Custom Digest: Custom Corp Tasks"]
        assert "Hello John Smith" in html  # Custom intro text
        assert "you have 2 urgent tasks and 5 upcoming tasks" in html
        assert "Custom Corp" in html
        assert "Please visit our portal to review these tasks" in html  # Custom content

        # Should contain HTML tags (since it uses HTML template with custom content)
        assert "<div" in html
        assert "<html" in html
        assert "email-container" in html

        # Clean up
        custom_template.delete(db)

    def test_manual_task_digest_email_dispatch_uses_default_template(
        self,
        db: Session,
        messaging_config,
        mock_mailgun_http,
    ) -> None:
        """Test manual task digest uses default template when no custom template exists in DB."""
        existing_templates = (
            MessagingTemplate.query(db)
            .filter(
                MessagingTemplate.type == MessagingActionType.MANUAL_TASK_DIGEST.value
            )
            .all()
        )
        for template in existing_templates:
            template.delete(db)

        dispatch_message(
            db=db,
            action_type=MessagingActionType.MANUAL_TASK_DIGEST,
            to_identity=Identity(**{"email": "vendor@example.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=ManualTaskDigestBodyParams(
                vendor_contact_name="Jane Doe",
                organization_name="Fallback Corp",
                portal_url="https://privacy.example.com/tasks",
                imminent_task_count=1,
                upcoming_task_count=3,
                total_task_count=4,
                company_logo_url=None,
            ),
        )

        # Verify default template was used
        assert mock_mailgun_http.called
        body = mailgun_post_body(mock_mailgun_http.request_history)
        html = body["html"][0]

        # Check that HTML template with default content is used
        assert body["subject"] == ["Weekly DSR Summary from Fallback Corp"]
        assert "Hi Jane Doe," in html
        assert "This is your weekly summary" in html  # Default intro text from template
        assert "4 requests coming due" in html  # Total count
        assert "1 within the next 7 days" in html  # Imminent count
        assert "3 due in the next period" in html  # Upcoming count

        # Should contain HTML tags (since it's the HTML template)
        assert "<div" in html
        assert "<html" in html
        assert "email-container" in html

        # Validate that URLs with the expected hostname are present in the email
        assert_url_hostname_present(html, "privacy.example.com")

    @mock.patch(
        "fides.api.service.messaging.message_dispatch_service.get_basic_messaging_template_by_type_or_default"
    )
    def test_manual_task_digest_email_dispatch_fallback_to_html_template(
        self,
        mock_get_template: Mock,
        db: Session,
        messaging_config,
        mock_mailgun_http,
    ) -> None:
        """Test manual task digest falls back to HTML template when no template is available."""
        # Mock the template retrieval to return None (simulating no template available)
        mock_get_template.return_value = None

        dispatch_message(
            db=db,
            action_type=MessagingActionType.MANUAL_TASK_DIGEST,
            to_identity=Identity(**{"email": "vendor@example.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=ManualTaskDigestBodyParams(
                vendor_contact_name="Jane Doe",
                organization_name="Fallback Corp",
                portal_url="https://privacy.example.com/tasks",
                imminent_task_count=1,
                upcoming_task_count=3,
                total_task_count=4,
                company_logo_url=None,
            ),
        )

        # Verify HTML template was used as fallback
        assert mock_mailgun_http.called
        body = mailgun_post_body(mock_mailgun_http.request_history)
        html = body["html"][0]

        # Check that HTML template content was used
        assert body["subject"] == ["Weekly DSR Summary from Fallback Corp"]
        assert "Hi Jane Doe," in html

        # Should contain HTML tags (since it's the HTML template)
        assert "<div" in html
        assert "<html" in html
        assert "email-container" in html

        # Validate that URLs with the expected hostname are present in the email
        assert_url_hostname_present(html, "privacy.example.com")
