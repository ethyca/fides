import pytest
from starlette.testclient import TestClient

from fides.api.ops.api.v1.urn_registry import ID_VERIFICATION_CONFIG, V1_URL_PREFIX
from fides.core.config import get_config


class TestGetIdentityVerificationConfig:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + ID_VERIFICATION_CONFIG

    @pytest.fixture(scope="function")
    def subject_identity_verification_required(self):
        """Override autouse fixture to enable identity verification for tests"""
        config = get_config()

        original_value = config.execution.subject_identity_verification_required
        config.execution.subject_identity_verification_required = True
        yield
        config.execution.subject_identity_verification_required = original_value

    def test_get_config_with_verification_required_no_email_config(
        self,
        url,
        db,
        api_client: TestClient,
        subject_identity_verification_required,
    ):
        resp = api_client.get(url)
        assert resp.status_code == 200
        response_data = resp.json()
        assert response_data["identity_verification_required"] is True
        assert response_data["valid_email_config_exists"] is False

    def test_get_config_with_verification_required_with_email_config(
        self,
        url,
        db,
        api_client: TestClient,
        messaging_config,
        subject_identity_verification_required,
    ):
        resp = api_client.get(url)
        assert resp.status_code == 200
        response_data = resp.json()
        assert response_data["identity_verification_required"] is True
        assert response_data["valid_email_config_exists"] is True

    def test_get_config_with_verification_not_required_with_email_config(
        self,
        url,
        db,
        api_client: TestClient,
        messaging_config,
    ):
        resp = api_client.get(url)
        assert resp.status_code == 200
        response_data = resp.json()
        assert response_data["identity_verification_required"] is False
        assert response_data["valid_email_config_exists"] is True

    def test_get_config_with_verification_not_required_with_no_email_config(
        self,
        url,
        db,
        api_client: TestClient,
    ):
        resp = api_client.get(url)
        assert resp.status_code == 200
        response_data = resp.json()
        assert response_data["identity_verification_required"] is False
        assert response_data["valid_email_config_exists"] is False
