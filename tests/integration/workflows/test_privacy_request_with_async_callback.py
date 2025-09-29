from typing import Generator
from unittest.mock import patch

import pytest
import yaml
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK
from starlette.testclient import TestClient

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from tests.conftest import wait_for_privacy_request_status


@pytest.mark.async_dsr
class TestPrivacyRequestWithAsyncCallback:

    @pytest.fixture
    def async_callback_connector(self, db: Session) -> Generator:
        with open(
            "tests/integration/workflows/data/example_async_callback_config.yml",
            "r",
            encoding="utf-8",
        ) as saas_config_file:
            saas_config = yaml.safe_load(saas_config_file)["saas_config"]

        with open(
            "tests/integration/workflows/data/example_async_callback_dataset.yml",
            "r",
            encoding="utf-8",
        ) as dataset_file:
            dataset = yaml.safe_load(dataset_file)["dataset"][0]

        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "async_callback",
                "name": "Async Callback Example",
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

    @patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_privacy_request_with_async_callback(
        self,
        mock_send,
        db,
        policy,
        async_callback_connector,
        api_client: TestClient,
        root_auth_header,
    ):
        """
        Integration test for privacy request with async callback

        1) Submit a privacy request with async callback
        2) Submit a response via the callback endpoint
        3) Verify the privacy request is completed
        """

        # Configure mock response for the initial async request
        mock_send().json.return_value = {"id": "123"}

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

        # Get the callback tokens from the intercepted HTTP request
        request_params = mock_send.call_args[0][0]
        jwe_token = request_params.headers["reply-to-token"]
        reply_to_url = request_params.headers["reply-to"]

        # Use the intercepted token to call the callback endpoint
        # This simulates the external service calling back with results
        auth_header = {"Authorization": "Bearer " + jwe_token}
        callback_response = api_client.post(
            reply_to_url,
            headers=auth_header,
            json={
                "access_results": [
                    {"id": 1, "name": "John Doe"},
                ]
            },
        )
        assert callback_response.status_code == HTTP_200_OK

        # Wait for the privacy request to be complete
        wait_for_privacy_request_status(
            db=db,
            privacy_request_id=privacy_request_id,
            target_status=PrivacyRequestStatus.complete,
            timeout_seconds=30,
            poll_interval_seconds=2,
        )

        # Verify the results
        privacy_request = PrivacyRequest.get_by(
            db, field="id", value=privacy_request_id
        )
        access_results = privacy_request.get_raw_access_results()
        user_data = access_results["async_callback_example:user"]
        assert user_data == [{"id": 1, "name": "John Doe"}]
