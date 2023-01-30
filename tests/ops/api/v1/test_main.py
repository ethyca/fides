"""Tests for the webserver and its various configurations."""
import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from fides.api.main import configure_security_env_overrides, create_fides_app
from fides.api.ops.util.oauth_util import (
    get_root_client,
    verify_oauth_client,
    verify_oauth_client_cli,
)


def test_read_autogenerated_docs(api_client: TestClient):
    """Test to ensure automatically generated docs build properly"""
    response = api_client.get(f"/openapi.json")
    assert response.status_code == 200


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


class TestSecurityEnvs:
    @pytest.mark.parametrize("endpoint", ["user", "system"])
    @pytest.mark.asyncio
    def test_demo_endpoints_unprotected(self, endpoint: str) -> None:
        """
        Test that all endpoints are unprotected in a 'demo'-tier
        security environment.
        """
        security_env = "demo"
        test_app = create_fides_app()
        test_app = configure_security_env_overrides(
            application=test_app, security_env=security_env
        )
        with TestClient(test_app) as test_client:
            response = test_client.get(f"/api/v1/{endpoint}")
            print(response.url)
            print(response.text)
            assert response.ok

    def test_dev_endpoints_protected(self) -> None:
        """
        Test that the non-cli-related endpoints are protected in
        a 'dev'-tier security environment.
        """
        security_env = "dev"
        endpoint = "data_category"
        test_app = create_fides_app()
        test_app = configure_security_env_overrides(
            application=test_app, security_env=security_env
        )
        with TestClient(test_app) as test_client:
            response = test_client.get(f"/api/v1/{endpoint}")
            print(response.url)
            print(response.text)
            assert response.ok

    def test_dev_endpoints_unprotected(self) -> None:
        """
        Test that the cli-related endpoints aren't protected in
        a 'dev'-tier security environment.
        """
        security_env = "dev"
        endpoint = "data_category"
        test_app = create_fides_app()
        test_app = configure_security_env_overrides(
            application=test_app, security_env=security_env
        )
        with TestClient(test_app) as test_client:
            response = test_client.get(f"/api/v1/{endpoint}")
            print(response.url)
            print(response.text)
            assert response.ok

    def test_prod_endpoints_protected(self) -> None:
        """
        Test that all endpoints are secured in a 'prod'-tier
        security environment.
        """
