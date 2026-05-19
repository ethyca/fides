import pytest
from jinja2 import Template

from fides.api.email_templates import get_email_template
from fides.api.schemas.messaging.messaging import MessagingActionType


def test_external_user_welcome_template_retrieval() -> None:
    """Ensure the template loads successfully as a Jinja Template object."""
    template = get_email_template(MessagingActionType.EXTERNAL_USER_WELCOME)
    assert isinstance(template, Template)


@pytest.mark.parametrize(
    "display_name,org_name,portal_link",
    [
        (
            "Jane Doe",
            "Acme Corp",
            "https://privacy.example.com?access_token=abc123",
        )
    ],
)
def test_external_user_welcome_template_render(
    display_name: str, org_name: str, portal_link: str
) -> None:
    """Render the template and verify variables are interpolated correctly."""
    template = get_email_template(MessagingActionType.EXTERNAL_USER_WELCOME)

    rendered = template.render(
        {
            "display_name": display_name,
            "org_name": org_name,
            "portal_link": portal_link,
        }
    )

    assert display_name in rendered
    assert org_name in rendered
    assert portal_link in rendered
