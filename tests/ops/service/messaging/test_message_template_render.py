import pytest

from fides.api.service.messaging.message_dispatch_service import _render


@pytest.mark.unit
class TestMessageTemplateRender:

    def test_template_render(self):
        """
        Test that a template is rendered correctly with the given variables.
        """
        template_str = """
        Your privacy request has been denied.
        __DENIAL_REASON__
        """
        variables = {
            "denial_reason": "Accounts with an unpaid balance cannot be deleted."
        }

        expected_rendered_template = """
        Your privacy request has been denied.
        Accounts with an unpaid balance cannot be deleted.
        """

        rendered_template = _render(template_str, variables)
        assert rendered_template == expected_rendered_template

    def test_template_render_unsafe(self):
        """
        Test that a template with unsafe code is not rendered and raises a SecurityError.
        """
        template_str = """
        Your privacy request has been denied.
        *bb*
        {% for s in ().__class__.__base__.__subclasses__() %}{% if "warning" in s.__name__ %}{{s()._module.__builtins__['__import__']('os').popen("env").read() }}{% endif %}
        {% endfor %}
        __CONFIG__
        *aa*
        """

        expected_rendered_template = """
        Your privacy request has been denied.
        *bb*
        {% for s in ().__class__.__base__.__subclasses__() %}{% if "warning" in s.__name__ %}{{s()._module.__builtins__['__import__']('os').popen("env").read() }}{% endif %}
        {% endfor %}
        123
        *aa*
        """

        variables = {
            "config": "123",
        }

        rendered_template = _render(template_str, variables)
        assert rendered_template == expected_rendered_template

        template_str = "your privacy request has been denied. __CONFIG.security.app_encryption_key__"
        variables = {
            "config": "123",
        }

        rendered_template = _render(template_str, variables)
        assert rendered_template == template_str
