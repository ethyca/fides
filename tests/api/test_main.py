"""Tests for the webserver and its various configurations."""
import pytest
from fastapi import FastAPI

from fides.api.main import configure_security_env_overrides
from fides.api.ops.util.oauth_util import (
    get_root_client,
    verify_oauth_client,
    verify_oauth_client_cli,
)

# Test that each security env sets the correct application override


class TestConfigureSecurityEnvOverrides:
    def test_configure_security_env_overrides_dev(self) -> None:
        """
        This test verifies that when set to 'dev', only the
        cli-related endpoints default to the root user.
        """
        security_env = "dev"
        test_app = FastAPI(title="test")
        test_app = configure_security_env_overrides(
            application=test_app, security_env=security_env
        )
        assert test_app.dependency_overrides[verify_oauth_client_cli] == get_root_client

    def test_configure_security_env_overrides_demo(self) -> None:
        """
        This test verifies that when set to 'demo', both oauth client
        checks get overwritten.
        """
        security_env = "demo"
        test_app = FastAPI(title="test")
        test_app = configure_security_env_overrides(
            application=test_app, security_env=security_env
        )
        assert test_app.dependency_overrides[verify_oauth_client] == get_root_client
        assert test_app.dependency_overrides[verify_oauth_client_cli] == get_root_client

    def test_configure_security_env_overrides_prod(self) -> None:
        """
        This test verifies that when set to 'prod', there are no
        dependency overrides for the oauth clients.
        """
        security_env = "prod"
        test_app = FastAPI(title="test")
        test_app = configure_security_env_overrides(
            application=test_app, security_env=security_env
        )
        with pytest.raises(KeyError):
            test_app.dependency_overrides[verify_oauth_client]

        with pytest.raises(KeyError):
            test_app.dependency_overrides[verify_oauth_client_cli]
