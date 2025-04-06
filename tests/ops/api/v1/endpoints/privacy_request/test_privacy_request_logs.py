from typing import Generator

import pytest
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from starlette.testclient import TestClient

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import PrivacyRequestSource, PrivacyRequestStatus
from fides.common.api.scope_registry import (
    PRIVACY_REQUEST_READ_ACCESS_RESULTS,
    STORAGE_CREATE_OR_UPDATE,
)
from fides.common.api.v1.urn_registry import PRIVACY_REQUESTS, V1_URL_PREFIX


class TestGetTestPrivacyRequestLogs:
    @pytest.fixture(scope="function")
    def test_privacy_request(
        self, db: Session, policy: Policy
    ) -> Generator[PrivacyRequest, None, None]:
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "policy_id": policy.id,
                "source": PrivacyRequestSource.dataset_test,
                "status": PrivacyRequestStatus.in_processing,
            },
        )
        yield privacy_request
        privacy_request.delete(db)

    @pytest.fixture(scope="function")
    def url(self, test_privacy_request) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUESTS + f"/{test_privacy_request.id}/logs"

    def test_get_test_logs_unauthenticated(self, api_client: TestClient, url):
        response = api_client.get(url, headers={})
        assert response.status_code == HTTP_401_UNAUTHORIZED

    def test_get_test_logs_wrong_scope(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[STORAGE_CREATE_OR_UPDATE])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == HTTP_403_FORBIDDEN

    def test_get_test_logs_invalid_privacy_request_id(
        self, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ_ACCESS_RESULTS])
        response = api_client.get(
            V1_URL_PREFIX + PRIVACY_REQUESTS + "/invalid_privacy_request_id/logs",
            headers=auth_header,
        )
        assert response.status_code == HTTP_404_NOT_FOUND

    @pytest.mark.usefixtures("dsr_testing_tools_enabled")
    def test_get_test_logs_empty(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ_ACCESS_RESULTS])
        response = api_client.get(url, headers=auth_header)

        assert response.status_code == HTTP_200_OK
        logs = response.json()
        assert len(logs) == 0

    @pytest.mark.usefixtures("dsr_testing_tools_enabled")
    def test_get_test_logs_success(
        self,
        api_client: TestClient,
        generate_auth_header,
        test_privacy_request: PrivacyRequest,
        url,
    ):
        # Generate some test logs
        test_id = test_privacy_request.id
        with logger.contextualize(
            privacy_request_id=test_id,
            privacy_request_source=PrivacyRequestSource.dataset_test.value,
        ):
            logger.info("Test message 1")
            logger.error("Test error message")
            logger.warning("Test warning message")

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ_ACCESS_RESULTS])
        response = api_client.get(url, headers=auth_header)

        assert response.status_code == HTTP_200_OK
        logs = response.json()
        assert len(logs) == 3

        # Verify log contents and order (oldest first)
        assert logs[0]["level"] == "INFO"
        assert logs[0]["message"] == "Test message 1"
        assert "timestamp" in logs[0]
        assert "module_info" in logs[0]

        assert logs[1]["level"] == "ERROR"
        assert logs[1]["message"] == "Test error message"
        assert "timestamp" in logs[1]
        assert "module_info" in logs[1]

        assert logs[2]["level"] == "WARNING"
        assert logs[2]["message"] == "Test warning message"
        assert "timestamp" in logs[2]
        assert "module_info" in logs[2]

    @pytest.mark.usefixtures("dsr_testing_tools_enabled")
    def test_get_test_logs_only_includes_test_source(
        self,
        api_client: TestClient,
        generate_auth_header,
        test_privacy_request: PrivacyRequest,
        url,
    ):
        test_id = test_privacy_request.id

        # Log with dataset_test source
        with logger.contextualize(
            privacy_request_id=test_id,
            privacy_request_source=PrivacyRequestSource.dataset_test.value,
        ):
            logger.info("Test message")

        # Log with different source
        with logger.contextualize(
            privacy_request_id=test_id,
            privacy_request_source=PrivacyRequestSource.privacy_center.value,
        ):
            logger.info("Should not appear in results")

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ_ACCESS_RESULTS])
        response = api_client.get(url, headers=auth_header)

        assert response.status_code == HTTP_200_OK
        logs = response.json()
        assert len(logs) == 1
        assert logs[0]["message"] == "Test message"

    @pytest.mark.usefixtures("dsr_testing_tools_enabled")
    def test_logs_deleted_with_privacy_request(
        self,
        api_client: TestClient,
        generate_auth_header,
        test_privacy_request: PrivacyRequest,
        url,
        db: Session,
    ):
        # Generate some test logs
        test_id = test_privacy_request.id
        with logger.contextualize(
            privacy_request_id=test_id,
            privacy_request_source=PrivacyRequestSource.dataset_test.value,
        ):
            logger.info("Test message")

        # Verify logs exist
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ_ACCESS_RESULTS])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == HTTP_200_OK
        logs = response.json()
        assert len(logs) == 1
        assert logs[0]["message"] == "Test message"

        # Delete privacy request
        test_privacy_request.delete(db)

        # Verify logs are deleted
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == HTTP_404_NOT_FOUND

    @pytest.mark.usefixtures("dsr_testing_tools_disabled")
    def test_get_test_logs_dsr_testing_disabled(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ_ACCESS_RESULTS])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == HTTP_403_FORBIDDEN
        assert response.json()["detail"] == "DSR testing tools are not enabled."
