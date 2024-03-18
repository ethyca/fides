import json
from unittest import mock

import pytest
from requests import Response
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import Policy
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.schemas.privacy_request import CustomPrivacyRequestField
from fides.api.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from tests.ops.service.privacy_request.test_request_runner_service import (
    get_privacy_request_results,
)


@pytest.mark.integration_saas
class TestCustomPrivacyRequestFields:
    @pytest.fixture(scope="function")
    def custom_privacy_request_fields_config(self, db: Session) -> ConnectionConfig:
        fides_key = "custom_privacy_request_fields_instance"
        config = load_config_with_replacement(
            "tests/fixtures/saas/test_data/saas_custom_privacy_request_fields_config.yml",
            "<instance_fides_key>",
            fides_key,
        )

        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": fides_key,
                "name": fides_key,
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.write,
                "secrets": {"api_key": "test"},
                "saas_config": config,
            },
        )
        return connection_config

    @pytest.fixture(scope="function")
    def custom_privacy_request_fields_dataset(
        self,
        db: Session,
        custom_privacy_request_fields_config: ConnectionConfig,
    ) -> DatasetConfig:
        fides_key = "custom_privacy_request_fields_instance"
        connection_config = custom_privacy_request_fields_config
        dataset = load_dataset_with_replacement(
            "tests/fixtures/saas/test_data/saas_custom_privacy_request_fields_dataset.yml",
            "<instance_fides_key>",
            fides_key,
        )[0]
        connection_config.name = fides_key
        connection_config.key = fides_key
        connection_config.save(db=db)

        ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)

        dataset = DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": fides_key,
                "ctl_dataset_id": ctl_dataset.id,
            },
        )
        return dataset

    @pytest.mark.usefixtures(
        "custom_privacy_request_fields_config",
        "custom_privacy_request_fields_dataset",
        "allow_custom_privacy_request_field_collection_enabled",
        "allow_custom_privacy_request_fields_in_request_execution_enabled",
    )
    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_custom_privacy_request_fields_access(
        self, mock_send, db: Session, policy: Policy, run_privacy_request_task
    ) -> None:
        data = {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": policy.key,
            "identity": {"email": "customer@example.com"},
            "custom_privacy_request_fields": {
                "first_name": CustomPrivacyRequestField(
                    label="First name", value="John"
                ),
                "last_name": CustomPrivacyRequestField(label="Last name", value="Doe"),
                "subscriber_ids": CustomPrivacyRequestField(
                    label="Subscriber IDs", value=["123", "456"]
                ),
                "account_ids": CustomPrivacyRequestField(
                    label="Account IDs", value=[123, 456]
                ),
            },
        }

        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = json.dumps([{"id": 1}]).encode()
        mock_send.return_value = mock_response

        get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            data,
        )

        request_params = mock_send.call_args[0][0]
        assert request_params.query_params == {"first_name": "John"}
        assert json.loads(request_params.body) == {
            "last_name": "Doe",
            "order_id": None,
            "subscriber_ids": ["123", "456"],
            "account_ids": [123, 456],
        }

    @pytest.mark.usefixtures(
        "custom_privacy_request_fields_config",
        "custom_privacy_request_fields_dataset",
        "allow_custom_privacy_request_field_collection_enabled",
        "allow_custom_privacy_request_fields_in_request_execution_enabled",
    )
    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_custom_privacy_request_fields_erasure(
        self, mock_send, db: Session, erasure_policy: Policy, run_privacy_request_task
    ) -> None:
        data = {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": erasure_policy.key,
            "identity": {"email": "customer@example.com"},
            "custom_privacy_request_fields": {
                "first_name": CustomPrivacyRequestField(
                    label="First name", value="John"
                ),
                "last_name": CustomPrivacyRequestField(label="Last name", value="Doe"),
                "subscriber_ids": CustomPrivacyRequestField(
                    label="Subscriber IDs", value=["123", "456"]
                ),
                "account_ids": CustomPrivacyRequestField(
                    label="Account IDs", value=[123, 456]
                ),
            },
        }

        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = json.dumps([{"id": 1}]).encode()
        mock_send.return_value = mock_response

        get_privacy_request_results(
            db,
            erasure_policy,
            run_privacy_request_task,
            data,
        )

        request_params = mock_send.call_args[0][0]
        assert request_params.query_params == {}
        assert json.loads(request_params.body) == {
            "user_info": {
                "first_name": "John",
                "last_name": "Doe",
                "subscriber_ids": ["123", "456"],
                "account_ids": [123, 456],
            }
        }
