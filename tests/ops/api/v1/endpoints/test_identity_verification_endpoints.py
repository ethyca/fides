import pytest
from starlette.testclient import TestClient

from fides.api.models.application_config import ApplicationConfig
from fides.common.api.v1.urn_registry import ID_VERIFICATION_CONFIG, V1_URL_PREFIX
from fides.config import CONFIG


class TestGetIdentityVerificationConfig:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + ID_VERIFICATION_CONFIG

    @pytest.fixture(scope="function")
    def subject_identity_verification_not_required(self, db):
        original_value = CONFIG.execution.subject_identity_verification_required
        CONFIG.execution.subject_identity_verification_required = False
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        CONFIG.execution.subject_identity_verification_required = original_value
        ApplicationConfig.update_config_set(db, CONFIG)

    @pytest.mark.usefixtures("subject_identity_verification_required")
    def test_get_config_with_verification_required_no_email_config(
        self,
        url,
        api_client: TestClient,
    ):
        resp = api_client.get(url)
        assert resp.status_code == 200
        response_data = resp.json()
        assert response_data["identity_verification_required"] is True
        assert response_data["disable_consent_identity_verification"] is False
        assert response_data["valid_email_config_exists"] is False

    @pytest.mark.usefixtures(
        "messaging_config", "subject_identity_verification_required"
    )
    def test_get_config_with_verification_required_with_email_config(
        self,
        url,
        api_client: TestClient,
    ):
        resp = api_client.get(url)
        assert resp.status_code == 200
        response_data = resp.json()
        assert response_data["identity_verification_required"] is True
        assert response_data["disable_consent_identity_verification"] is False
        assert response_data["valid_email_config_exists"] is True

    @pytest.mark.usefixtures(
        "messaging_config", "subject_identity_verification_not_required"
    )
    def test_get_config_with_verification_not_required_with_email_config(
        self,
        url,
        api_client: TestClient,
    ):
        resp = api_client.get(url)
        assert resp.status_code == 200
        response_data = resp.json()
        assert response_data["identity_verification_required"] is False
        assert response_data["disable_consent_identity_verification"] is True
        assert response_data["valid_email_config_exists"] is True

    @pytest.mark.usefixtures("subject_identity_verification_not_required")
    def test_get_config_with_verification_not_required_with_no_email_config(
        self,
        url,
        api_client: TestClient,
    ):
        resp = api_client.get(url)
        assert resp.status_code == 200
        response_data = resp.json()
        assert response_data["identity_verification_required"] is False
        assert response_data["disable_consent_identity_verification"] is True
        assert response_data["valid_email_config_exists"] is False

    @pytest.mark.usefixtures(
        "subject_identity_verification_required",
        "disable_consent_identity_verification",
    )
    def test_disable_consent_identity_verification(
        self,
        url,
        api_client: TestClient,
    ):
        resp = api_client.get(url)
        assert resp.status_code == 200
        response_data = resp.json()
        assert response_data["identity_verification_required"] is True
        assert response_data["disable_consent_identity_verification"] is True
        assert response_data["valid_email_config_exists"] is False
