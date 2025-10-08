import pytest
from jinja2 import Template

from fides.api.email_templates import get_email_template
from fides.api.schemas.messaging.messaging import MessagingActionType
from tests.ops.test_helpers.email_test_utils import assert_url_hostname_present


def test_manual_task_digest_template_retrieval() -> None:
    """Ensure the manual task digest template loads successfully as a Jinja Template object."""
    template = get_email_template(MessagingActionType.MANUAL_TASK_DIGEST)
    assert isinstance(template, Template)


@pytest.mark.parametrize(
    "vendor_contact_name,organization_name,portal_url,imminent_count,upcoming_count,total_count,company_logo_url",
    [
        (
            "Jane Doe",
            "Acme Corp",
            "https://privacy.example.com/external-tasks?access_token=abc123",
            3,
            7,
            10,
            None,
        ),
        (
            "John Smith",
            "Test Organization",
            "https://portal.test.com/external-tasks",
            2,
            3,
            5,
            "https://example.com/logo.png",
        ),
        (
            "Test User",
            "My Company",
            "http://localhost:3001/external-tasks",
            0,
            0,
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
    total_count: int,
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
        "total_task_count": total_count,
        "company_logo_url": company_logo_url,
    }

    rendered_html = template.render(variables)

    # Verify key content is present
    assert f"Hi {vendor_contact_name}," in rendered_html
    assert organization_name in rendered_html
    assert portal_url in rendered_html
    assert f"You have {total_count} request" in rendered_html
    assert f"{imminent_count} within the next 7 days" in rendered_html
    assert f"{upcoming_count} due in the next period" in rendered_html

    # Check for proper pluralization
    if total_count == 1:
        assert "You have 1 request coming due" in rendered_html
    else:
        assert "You have {} requests coming due".format(total_count) in rendered_html

    # Check logo handling
    if company_logo_url:
        assert f'src="{company_logo_url}"' in rendered_html
        assert f'alt="{organization_name} Logo"' in rendered_html
    else:
        assert (
            f'<div class="logo-placeholder">{organization_name}</div>' in rendered_html
        )

    # Verify essential HTML structure
    assert "<!DOCTYPE html>" in rendered_html
    assert '<html lang="en">' in rendered_html
    assert "Weekly DSR Summary" in rendered_html
    assert "Privacy Center" in rendered_html
    assert "View All Tasks" in rendered_html


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
        "total_task_count": 0,
        "company_logo_url": None,
    }

    rendered_html = template.render(variables)

    # Verify special characters are handled correctly
    assert "María José García-López" in rendered_html
    assert "Acme Corp &amp; Associates, LLC" in rendered_html  # HTML escaped
    # Validate that URLs with the expected hostname are present in the rendered HTML
    assert_url_hostname_present(rendered_html, "privacy.example.com")
    assert "You have 0 requests due" in rendered_html


def test_manual_task_digest_template_responsive_design() -> None:
    """Test that the template includes responsive design elements."""
    template = get_email_template(MessagingActionType.MANUAL_TASK_DIGEST)

    variables = {
        "vendor_contact_name": "Test User",
        "organization_name": "Test Org",
        "portal_url": "https://example.com",
        "imminent_task_count": 0,
        "upcoming_task_count": 1,
        "total_task_count": 1,
        "company_logo_url": None,
    }

    rendered_html = template.render(variables)

    # Check for responsive design elements
    assert 'meta name="viewport"' in rendered_html
    assert "@media only screen and (max-width: 600px)" in rendered_html
    assert "@media (prefers-color-scheme: dark)" in rendered_html
    assert "email-container" in rendered_html
    assert "cta-button" in rendered_html
