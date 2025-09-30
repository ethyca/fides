from typing import Generator
from unittest.mock import patch

import pytest
import yaml
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK
from starlette.testclient import TestClient

from fides.api.models.attachment import AttachmentType
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.models.privacy_request.request_task import RequestTaskSubRequest
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.request_service import requeue_polling_tasks
from tests.conftest import wait_for_privacy_request_status
from tests.ops.test_helpers.saas_test_utils import MockAuthenticatedClient


@pytest.mark.async_dsr
class TestPrivacyRequestWithAsyncPolling:
    @pytest.fixture
    def async_polling_connector(self, db: Session) -> Generator:
        with open(
            "tests/integration/workflows/data/example_async_polling_config.yml",
            "r",
            encoding="utf-8",
        ) as saas_config_file:
            saas_config = yaml.safe_load(saas_config_file)["saas_config"]

        with open(
            "tests/integration/workflows/data/example_async_polling_dataset.yml",
            "r",
            encoding="utf-8",
        ) as dataset_file:
            dataset = yaml.safe_load(dataset_file)["dataset"][0]

        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "async_polling",
                "name": "Async Polling Example",
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.write,
                "secrets": {
                    "domain": "example.com",
                    "api_token": "123",
                },
                "saas_config": saas_config,
            },
        )

        ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)

        DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": dataset["fides_key"],
                "ctl_dataset_id": ctl_dataset.id,
            },
        )

        yield connection_config

    @pytest.fixture
    def mock_authenticated_client(self) -> MockAuthenticatedClient:
        """Fixture to mock an authenticated client for async polling operations"""
        client = MockAuthenticatedClient()

        # Initial request to start the async polling process
        client.add_response(
            "GET",
            "/api/access-package",
            {"request_id": "async_request_123", "status": "processing"},
            status_code=202,
        )

        # Status checks
        client.add_response(
            "GET",
            "/api/access-package/status",
            {"status": "completed"},
            status_code=200,
        )

        # Final result retrieval
        client.add_binary_response(
            "GET",
            "/api/access-package/result",
            b"file content here",
            headers={
                "content-type": "application/pdf",
                "content-disposition": "attachment; filename=report.pdf",
            },
        )

        client.add_response(
            "DELETE",
            "/api/anonymize-user/customer-1@example.com",
            {"correlation_id": "123"},
            status_code=200,
        )

        client.add_response(
            "GET",
            "/api/anonymize-user/123/status",
            {"status": "completed"},
            status_code=200,
        )

        return client

    @patch("fides.api.service.connectors.saas_connector.SaaSConnector.create_client")
    def test_access_privacy_request_with_async_polling(
        self,
        mock_create_client,
        db,
        policy,
        async_polling_connector,
        api_client: TestClient,
        mock_authenticated_client,
        root_auth_header,
    ):
        """
        Integration test for an access privacy request with async polling

        1) Submit a privacy request with async polling
        2) Wait for the privacy request to be in processing (awaiting polling)
        3) Requeue the polling task
        4) Mock the status response
        5) Wait for the privacy request to be complete
        6) Verify the DSR package includes the attachment
        """
        # Configure the mock to return our MockAuthenticatedClient instance
        mock_create_client.return_value = mock_authenticated_client

        response = api_client.post(
            "/api/v1/privacy-request",
            headers=root_auth_header,
            json=[
                {
                    "identity": {"email": "customer-1@example.com"},
                    "policy_key": policy.key,
                }
            ],
        )
        assert response.status_code == HTTP_200_OK
        privacy_request_id = response.json()["succeeded"][0]["id"]

        # Wait for the privacy request to be in processing (awaiting polling)
        wait_for_privacy_request_status(
            db=db,
            privacy_request_id=privacy_request_id,
            target_status=PrivacyRequestStatus.in_processing,
            timeout_seconds=30,
            poll_interval_seconds=2,
        )

        # Requeue the polling task
        requeue_polling_tasks.apply().get()

        # Wait for the privacy request to be complete
        wait_for_privacy_request_status(
            db=db,
            privacy_request_id=privacy_request_id,
            target_status=PrivacyRequestStatus.complete,
            timeout_seconds=30,
            poll_interval_seconds=2,
        )

        # Verify the privacy request has an attachment
        privacy_request = (
            db.query(PrivacyRequest)
            .filter(PrivacyRequest.id == privacy_request_id)
            .first()
        )
        attachments = privacy_request.attachments
        assert len(attachments) == 1

        attachment = attachments[0]
        assert attachment.file_name == "report.pdf"

        # We use the default storage config for local storage
        assert attachment.storage_key == "default_storage_config_local"
        assert attachment.attachment_type == AttachmentType.include_with_access_package

        # Verify the request task sub request is complete
        request_task_sub_requests = db.query(RequestTaskSubRequest).all()
        assert len(request_task_sub_requests) == 1
        assert request_task_sub_requests[0].status == ExecutionLogStatus.complete.value

    @patch("fides.api.service.connectors.saas_connector.SaaSConnector.create_client")
    def test_erasure_privacy_request_with_async_polling(
        self,
        mock_create_client,
        db,
        erasure_policy,
        async_polling_connector,
        api_client: TestClient,
        mock_authenticated_client,
        root_auth_header,
    ):
        """
        Integration test for an erasure privacy request with async polling

        1) Submit a privacy request with async polling
        2) Wait for the privacy request to be in processing (awaiting polling)
        3) Requeue the polling task
        4) Mock the status response
        5) Wait for the privacy request to be complete
        6) Verify the DSR package includes the attachment
        """
        # Configure the mock to return our MockAuthenticatedClient instance
        mock_create_client.return_value = mock_authenticated_client

        response = api_client.post(
            "/api/v1/privacy-request",
            headers=root_auth_header,
            json=[
                {
                    "identity": {"email": "customer-1@example.com"},
                    "policy_key": erasure_policy.key,
                }
            ],
        )
        assert response.status_code == HTTP_200_OK
        privacy_request_id = response.json()["succeeded"][0]["id"]

        # Wait for the privacy request to be in processing (awaiting polling)
        wait_for_privacy_request_status(
            db=db,
            privacy_request_id=privacy_request_id,
            target_status=PrivacyRequestStatus.in_processing,
            timeout_seconds=30,
            poll_interval_seconds=2,
        )

        # Requeue the polling task
        requeue_polling_tasks.apply().get()

        # Wait for the privacy request to be in processing (awaiting polling)
        wait_for_privacy_request_status(
            db=db,
            privacy_request_id=privacy_request_id,
            target_status=PrivacyRequestStatus.in_processing,
            timeout_seconds=30,
            poll_interval_seconds=2,
        )

        # Requeue the polling task
        requeue_polling_tasks.apply().get()

        # Wait for the privacy request to be complete
        wait_for_privacy_request_status(
            db=db,
            privacy_request_id=privacy_request_id,
            target_status=PrivacyRequestStatus.complete,
            timeout_seconds=30,
            poll_interval_seconds=2,
        )
