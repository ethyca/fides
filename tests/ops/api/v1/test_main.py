"""Tests for the webserver and its various configurations."""
import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from fides.api.main import create_fides_app
from fides.api.ops.oauth.utils import (
    get_root_client,
    verify_oauth_client,
    verify_oauth_client_prod,
)


def test_read_autogenerated_docs(api_client: TestClient):
    """Test to ensure automatically generated docs build properly"""
    response = api_client.get("/openapi.json")
    assert response.status_code == 200


class TestConfigureSecurityEnvOverrides:
    def test_configure_security_env_overrides_dev(self) -> None:
        """
        This test verifies that when set to 'dev', only the
        cli-related endpoints default to the root user.
        """
        security_env = "dev"
        test_app = FastAPI(title="test")
        test_app = create_fides_app(security_env=security_env)
        assert (
            test_app.dependency_overrides[verify_oauth_client_prod] == get_root_client
        )

    def test_configure_security_env_overrides_prod(self) -> None:
        """
        This test verifies that when set to 'prod', there are no
        dependency overrides for the oauth clients.
        """
        security_env = "prod"
        test_app = FastAPI(title="test")
        test_app = create_fides_app(security_env=security_env)
        with pytest.raises(KeyError):
            test_app.dependency_overrides[verify_oauth_client]

        with pytest.raises(KeyError):
            test_app.dependency_overrides[verify_oauth_client_prod]
