import pytest
from jinja2 import Template

from fides.api.email_templates import get_email_template
from fides.api.schemas.messaging.messaging import MessagingActionType


def test_manual_task_digest_template_retrieval() -> None:
    """Ensure the manual task digest template loads successfully as a Jinja Template object."""
    template = get_email_template(MessagingActionType.MANUAL_TASK_DIGEST)
    assert isinstance(template, Template)


@pytest.mark.parametrize(
    "vendor_contact_name,organization_name,portal_url,imminent_count,upcoming_count,company_logo_url",
    [
        (
            "Jane Doe",
            "Acme Corp",
            "https://privacy.example.com/external-tasks?access_token=abc123",
            3,
            7,
            None,
        ),
        (
            "John Smith",
            "Test Organization",
            "https://portal.test.com/external-tasks",
            0,
            5,
            "https://example.com/logo.png",
        ),
        (
            "Test User",
            "My Company",
            "http://localhost:3001/external-tasks",
            10,
            0,
            None,
        ),
    ],
)
def test_manual_task_digest_template_rendering(
    vendor_contact_name: str,
    organization_name: str,
    portal_url: str,
    imminent_count: int,
    upcoming_count: int,
    company_logo_url: str,
) -> None:
    """Test that the manual task digest template renders correctly with various inputs."""
    template = get_email_template(MessagingActionType.MANUAL_TASK_DIGEST)

    variables = {
        "vendor_contact_name": vendor_contact_name,
        "organization_name": organization_name,
        "portal_url": portal_url,
        "imminent_task_count": imminent_count,
        "upcoming_task_count": upcoming_count,
        "company_logo_url": company_logo_url,
    }

    rendered_html = template.render(variables)

    # Verify key content is present
    assert f"Hi {vendor_contact_name}," in rendered_html
    assert organization_name in rendered_html
    assert portal_url in rendered_html
    assert f"You have {imminent_count} request" in rendered_html
    assert f"You have {upcoming_count} request" in rendered_html

    # Check for proper pluralization
    if imminent_count == 1:
        assert "You have 1 request due" in rendered_html
    else:
        assert "You have {} requests due".format(imminent_count) in rendered_html

    if upcoming_count == 1:
        assert "You have 1 request due in the next period" in rendered_html
    else:
        assert "You have {} requests due in the next period".format(upcoming_count) in rendered_html

    # Check logo handling
    if company_logo_url:
        assert f'src="{company_logo_url}"' in rendered_html
        assert f'alt="{organization_name} Logo"' in rendered_html
    else:
        assert f'<div class="logo-placeholder">{organization_name}</div>' in rendered_html

    # Verify essential HTML structure
    assert "<!DOCTYPE html>" in rendered_html
    assert "<html lang=\"en\">" in rendered_html
    assert "Weekly DSR Summary" in rendered_html
    assert "Privacy Center" in rendered_html
    assert "View All Tasks Due Soon" in rendered_html
    assert "View All Upcoming Tasks" in rendered_html


def test_manual_task_digest_template_edge_cases() -> None:
    """Test template rendering with edge cases and special characters."""
    template = get_email_template(MessagingActionType.MANUAL_TASK_DIGEST)

    # Test with special characters and long names
    variables = {
        "vendor_contact_name": "María José García-López",
        "organization_name": "Acme Corp & Associates, LLC",
        "portal_url": "https://privacy.example.com/external-tasks?token=abc123&user=test",
        "imminent_task_count": 0,
        "upcoming_task_count": 0,
        "company_logo_url": None,
    }

    rendered_html = template.render(variables)

    # Verify special characters are handled correctly
    assert "María José García-López" in rendered_html
    assert "Acme Corp &amp; Associates, LLC" in rendered_html  # HTML escaped
    assert "privacy.example.com" in rendered_html
    assert "You have 0 requests due" in rendered_html


def test_manual_task_digest_template_responsive_design() -> None:
    """Test that the template includes responsive design elements."""
    template = get_email_template(MessagingActionType.MANUAL_TASK_DIGEST)

    variables = {
        "vendor_contact_name": "Test User",
        "organization_name": "Test Org",
        "portal_url": "https://example.com",
        "imminent_task_count": 1,
        "upcoming_task_count": 1,
        "company_logo_url": None,
    }

    rendered_html = template.render(variables)

    # Check for responsive design elements
    assert 'meta name="viewport"' in rendered_html
    assert "@media only screen and (max-width: 600px)" in rendered_html
    assert "@media (prefers-color-scheme: dark)" in rendered_html
    assert "email-container" in rendered_html
    assert "cta-button" in rendered_html
