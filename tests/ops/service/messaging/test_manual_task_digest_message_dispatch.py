from unittest import mock
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from fides.api.schemas.messaging.messaging import (
    ManualTaskDigestBodyParams,
    MessagingActionType,
    MessagingServiceType,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.service.messaging.message_dispatch_service import dispatch_message
from tests.ops.test_helpers.email_test_utils import assert_url_hostname_present


@pytest.mark.unit
class TestManualTaskDigestMessageDispatch:
    """Test manual task digest message dispatch functionality."""

    @mock.patch(
        "fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    def test_manual_task_digest_email_dispatch_mailgun_success(
        self,
        mock_mailgun_dispatcher: Mock,
        db: Session,
        messaging_config,
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
                company_logo_url=None,
            ),
        )

        # Verify mailgun dispatcher was called with correct parameters
        mock_mailgun_dispatcher.assert_called_once()
        call_args = mock_mailgun_dispatcher.call_args

        messaging_config_arg = call_args[0][0]
        email_for_action_type = call_args[0][1]
        recipient_email = call_args[0][2]

        assert messaging_config_arg == messaging_config
        assert recipient_email == "vendor@example.com"

        # Check email content
        assert email_for_action_type.subject == "Weekly DSR Summary from Acme Corp"
        assert "Hi Jane Doe," in email_for_action_type.body
        assert "Acme Corp" in email_for_action_type.body
        assert "You have 3 request" in email_for_action_type.body  # imminent tasks
        assert "You have 7 request" in email_for_action_type.body  # upcoming tasks
        # Validate that URLs with the expected hostname are present in the email
        assert_url_hostname_present(email_for_action_type.body, "privacy.example.com")

        # Check template variables
        template_vars = email_for_action_type.template_variables
        assert template_vars["vendor_contact_name"] == "Jane Doe"
        assert template_vars["organization_name"] == "Acme Corp"
        assert template_vars["imminent_task_count"] == 3
        assert template_vars["upcoming_task_count"] == 7

    @mock.patch(
        "fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    def test_manual_task_digest_email_dispatch_with_logo(
        self,
        mock_mailgun_dispatcher: Mock,
        db: Session,
        messaging_config,
    ) -> None:
        """Test manual task digest email dispatch with company logo."""
        dispatch_message(
            db=db,
            action_type=MessagingActionType.MANUAL_TASK_DIGEST,
            to_identity=Identity(**{"email": "vendor@example.com"}),
            service_type=MessagingServiceType.mailgun.value,
            message_body_params=ManualTaskDigestBodyParams(
                vendor_contact_name="John Smith",
                organization_name="Test Organization",
                portal_url="https://portal.test.com/external-tasks",
                imminent_task_count=0,
                upcoming_task_count=5,
                company_logo_url="https://example.com/logo.png",
            ),
        )

        mock_mailgun_dispatcher.assert_called_once()
        email_for_action_type = mock_mailgun_dispatcher.call_args[0][1]

        # Check that logo URL is included in the rendered template
        assert 'src="https://example.com/logo.png"' in email_for_action_type.body
        assert 'alt="Test Organization Logo"' in email_for_action_type.body

        # Check template variables include logo URL
        template_vars = email_for_action_type.template_variables
        assert template_vars["company_logo_url"] == "https://example.com/logo.png"

    @mock.patch(
        "fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    def test_manual_task_digest_email_dispatch_zero_tasks(
        self,
        mock_mailgun_dispatcher: Mock,
        db: Session,
        messaging_config,
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
                company_logo_url=None,
            ),
        )

        mock_mailgun_dispatcher.assert_called_once()
        email_for_action_type = mock_mailgun_dispatcher.call_args[0][1]

        # Check that zero counts are handled correctly
        assert "You have 0 requests due" in email_for_action_type.body

        # Check template variables
        template_vars = email_for_action_type.template_variables
        assert template_vars["imminent_task_count"] == 0
        assert template_vars["upcoming_task_count"] == 0

    def test_manual_task_digest_body_params_validation(self) -> None:
        """Test that ManualTaskDigestBodyParams validates correctly."""
        # Test valid params
        valid_params = ManualTaskDigestBodyParams(
            vendor_contact_name="Jane Doe",
            organization_name="Acme Corp",
            portal_url="https://example.com/portal",
            imminent_task_count=5,
            upcoming_task_count=10,
            company_logo_url="https://example.com/logo.png",
        )

        assert valid_params.vendor_contact_name == "Jane Doe"
        assert valid_params.organization_name == "Acme Corp"
        assert valid_params.portal_url == "https://example.com/portal"
        assert valid_params.imminent_task_count == 5
        assert valid_params.upcoming_task_count == 10
        assert valid_params.company_logo_url == "https://example.com/logo.png"

        # Test with optional logo URL as None
        params_no_logo = ManualTaskDigestBodyParams(
            vendor_contact_name="John Smith",
            organization_name="Test Org",
            portal_url="https://test.com",
            imminent_task_count=0,
            upcoming_task_count=3,
            company_logo_url=None,
        )

        assert params_no_logo.company_logo_url is None

    @mock.patch(
        "fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    def test_manual_task_digest_email_dispatch_special_characters(
        self,
        mock_mailgun_dispatcher: Mock,
        db: Session,
        messaging_config,
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
                company_logo_url=None,
            ),
        )

        mock_mailgun_dispatcher.assert_called_once()
        email_for_action_type = mock_mailgun_dispatcher.call_args[0][1]

        # Check that special characters are handled correctly
        assert "María José García-López" in email_for_action_type.body
        # HTML should be escaped in the template
        assert "Acme Corp &amp; Associates, LLC" in email_for_action_type.body
        # Validate that URLs with the expected hostname are present in the email
        assert_url_hostname_present(email_for_action_type.body, "privacy.example.com")

        # Check template variables
        template_vars = email_for_action_type.template_variables
        assert template_vars["vendor_contact_name"] == "María José García-López"
        assert template_vars["organization_name"] == "Acme Corp & Associates, LLC"

    @mock.patch(
        "fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    def test_manual_task_digest_email_dispatch_with_custom_template(
        self,
        mock_mailgun_dispatcher: Mock,
        db: Session,
        messaging_config,
    ) -> None:
        """Test manual task digest email dispatch using custom template from UI."""
        from fides.api.models.messaging_template import MessagingTemplate

        # Create a custom template
        custom_template = MessagingTemplate.create(
            db=db,
            data={
                "type": MessagingActionType.MANUAL_TASK_DIGEST.value,
                "content": {
                    "subject": "Custom Digest: __ORGANIZATION_NAME__ Tasks",
                    "body": "Hello __VENDOR_CONTACT_NAME__, you have __IMMINENT_TASK_COUNT__ urgent tasks and __UPCOMING_TASK_COUNT__ upcoming tasks from __ORGANIZATION_NAME__. Visit: __PORTAL_URL__",
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
                company_logo_url=None,
            ),
        )

        # Verify custom template was used
        mock_mailgun_dispatcher.assert_called_once()
        call_args = mock_mailgun_dispatcher.call_args
        email_for_action_type = call_args[0][1]

        # Check that custom template content was used (not HTML template)
        assert email_for_action_type.subject == "Custom Digest: Custom Corp Tasks"
        assert "Hello John Smith" in email_for_action_type.body
        assert (
            "you have 2 urgent tasks and 5 upcoming tasks" in email_for_action_type.body
        )
        assert "Custom Corp" in email_for_action_type.body
        assert "https://privacy.example.com/tasks" in email_for_action_type.body

        # Should not contain HTML tags (since it's a custom text template)
        assert "<div" not in email_for_action_type.body
        assert "<html" not in email_for_action_type.body

        # Clean up
        custom_template.delete(db)

    @mock.patch(
        "fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    def test_manual_task_digest_email_dispatch_uses_default_template(
        self,
        mock_mailgun_dispatcher: Mock,
        db: Session,
        messaging_config,
    ) -> None:
        """Test manual task digest uses default template when no custom template exists in DB."""
        # Ensure no custom template exists in database
        from fides.api.models.messaging_template import MessagingTemplate

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
                company_logo_url=None,
            ),
        )

        # Verify default template was used
        mock_mailgun_dispatcher.assert_called_once()
        call_args = mock_mailgun_dispatcher.call_args
        email_for_action_type = call_args[0][1]

        # Check that default template content was used (text-based, not HTML)
        assert email_for_action_type.subject == "Weekly DSR Summary from Fallback Corp"
        assert "Hi Jane Doe," in email_for_action_type.body
        assert "This is your weekly summary" in email_for_action_type.body
        assert "1 request(s) due in the next week" in email_for_action_type.body
        assert "3 request(s) due in the next period" in email_for_action_type.body

        # Should NOT contain HTML tags (since it's the default text template)
        assert "<div" not in email_for_action_type.body
        assert "<html" not in email_for_action_type.body
        assert "email-container" not in email_for_action_type.body

        # Validate that URLs with the expected hostname are present in the email
        assert_url_hostname_present(email_for_action_type.body, "privacy.example.com")

    @mock.patch(
        "fides.api.service.messaging.message_dispatch_service._mailgun_dispatcher"
    )
    @mock.patch(
        "fides.api.service.messaging.message_dispatch_service.get_basic_messaging_template_by_type_or_default"
    )
    def test_manual_task_digest_email_dispatch_fallback_to_html_template(
        self,
        mock_get_template: Mock,
        mock_mailgun_dispatcher: Mock,
        db: Session,
        messaging_config,
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
                company_logo_url=None,
            ),
        )

        # Verify HTML template was used as fallback
        mock_mailgun_dispatcher.assert_called_once()
        call_args = mock_mailgun_dispatcher.call_args
        email_for_action_type = call_args[0][1]

        # Check that HTML template content was used
        assert email_for_action_type.subject == "Weekly DSR Summary from Fallback Corp"
        assert "Hi Jane Doe," in email_for_action_type.body

        # Should contain HTML tags (since it's the HTML template)
        assert "<div" in email_for_action_type.body
        assert "<html" in email_for_action_type.body
        assert "email-container" in email_for_action_type.body

        # Validate that URLs with the expected hostname are present in the email
        assert_url_hostname_present(email_for_action_type.body, "privacy.example.com")
