import uuid
from unittest import mock

import pydash
import pytest
from fastapi import HTTPException
from fastapi_pagination import Params
from fideslang import Dataset
from pydash import filter_
from sqlalchemy.orm import make_transient
from sqlalchemy.orm.attributes import flag_modified

from fides.api.ops.api.v1.scope_registry import (
    DATASET_CREATE_OR_UPDATE,
    DATASET_DELETE,
    DATASET_READ,
)
from fides.api.ops.api.v1.urn_registry import (
    DATASET_BY_KEY,
    DATASET_CONFIGS,
    DATASET_VALIDATE,
    DATASETCONFIG_BY_KEY,
    DATASETS,
    V1_URL_PREFIX,
    YAML_DATASETS,
)
from fides.api.ops.models.datasetconfig import DatasetConfig


def _reject_key(dict, key):
    """Return a copy of the given dictionary with the given key removed"""
    result = dict.copy()
    result.pop(key, None)
    return result


def test_example_datasets(example_datasets):
    """Ensure the test fixture loads the right sample data"""
    assert example_datasets
    assert example_datasets[0]["fides_key"] == "postgres_example_test_dataset"
    assert len(example_datasets[0]["collections"]) == 11
    assert example_datasets[1]["fides_key"] == "mongo_test"
    assert len(example_datasets[1]["collections"]) == 9
    assert example_datasets[2]["fides_key"] == "snowflake_example_test_dataset"
    assert len(example_datasets[2]["collections"]) == 11
    assert example_datasets[3]["fides_key"] == "redshift_example_test_dataset"
    assert len(example_datasets[3]["collections"]) == 11
    assert example_datasets[4]["fides_key"] == "mssql_example_test_dataset"
    assert len(example_datasets[4]["collections"]) == 11
    assert example_datasets[5]["fides_key"] == "mysql_example_test_dataset"
    assert len(example_datasets[5]["collections"]) == 11
    assert example_datasets[6]["fides_key"] == "mariadb_example_test_dataset"
    assert len(example_datasets[6]["collections"]) == 11
    assert example_datasets[7]["fides_key"] == "bigquery_example_test_dataset"
    assert len(example_datasets[7]["collections"]) == 11
    assert example_datasets[9]["fides_key"] == "email_dataset"
    assert len(example_datasets[9]["collections"]) == 3


class TestValidateDataset:
    @pytest.fixture
    def validate_dataset_url(self, connection_config):
        path = V1_URL_PREFIX + DATASET_VALIDATE
        path_params = {"connection_key": connection_config.key}
        return path.format(**path_params)

    def test_put_validate_dataset_not_authenticated(
        self, example_datasets, validate_dataset_url, api_client
    ):
        response = api_client.put(
            validate_dataset_url, headers={}, json=example_datasets[0]
        )
        assert response.status_code == 401

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_put_validate_dataset_wrong_scope(
        self, auth_header, example_datasets, validate_dataset_url, api_client
    ):
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=example_datasets[0]
        )
        assert response.status_code == 403

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_put_validate_dataset_missing_key(
        self,
        auth_header,
        example_datasets,
        validate_dataset_url,
        api_client,
    ):
        invalid_dataset = _reject_key(example_datasets[0], "fides_key")
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=invalid_dataset
        )
        assert response.status_code == 422
        details = response.json()["detail"]
        assert ["body", "fides_key"] in [e["loc"] for e in details]

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_put_validate_dataset_missing_collections(
        self, auth_header, example_datasets, validate_dataset_url, api_client
    ):
        invalid_dataset = _reject_key(example_datasets[0], "collections")
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=invalid_dataset
        )
        assert response.status_code == 422
        details = response.json()["detail"]
        assert ["body", "collections"] in [e["loc"] for e in details]

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_put_validate_dataset_nested_collections(
        self, auth_header, example_datasets, validate_dataset_url, api_client
    ):
        invalid_dataset = example_datasets[0]
        invalid_dataset["collections"][0]["fields"].append(
            {
                "name": "details",
                "fields": [
                    {
                        "name": "phone",
                        "data_categories": ["user.contact"],
                    },
                    {"name": "count", "data_categories": ["system.operations"]},
                ],
            }
        )
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=invalid_dataset
        )
        json_response = response.json()

        # if we extract the details field from the response it will contain
        # the nested fields "phone" and "count"
        details_field = filter_(
            pydash.get(json_response, "dataset.collections.0.fields"),
            {"name": "details"},
        )[0]

        assert set(map(lambda f: f["name"], details_field["fields"])) == {
            "phone",
            "count",
        }

        assert response.status_code == 200

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_put_validate_dataset_invalid_length(
        self, auth_header, example_datasets, validate_dataset_url, api_client
    ):
        invalid_dataset = example_datasets[0]

        # string is properly read:
        invalid_dataset["collections"][0]["fields"][0]["fidesops_meta"] = {
            "length": 123
        }
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=invalid_dataset
        )
        assert response.status_code == 200
        assert (
            response.json()["dataset"]["collections"][0]["fields"][0]["fides_meta"][
                "length"
            ]
            == 123
        )

        # fails with an invalid value
        invalid_dataset["collections"][0]["fields"][0]["fidesops_meta"] = {"length": -1}
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=invalid_dataset
        )

        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"] == "ensure this value is greater than 0"
        )

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_put_validate_dataset_invalid_data_type(
        self, auth_header, example_datasets, validate_dataset_url, api_client
    ):
        invalid_dataset = example_datasets[0]

        # string is properly read:
        invalid_dataset["collections"][0]["fields"][0]["fidesops_meta"] = {
            "data_type": "string"
        }
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=invalid_dataset
        )
        assert response.status_code == 200
        assert (
            response.json()["dataset"]["collections"][0]["fields"][0]["fides_meta"][
                "data_type"
            ]
            == "string"
        )

        # fails with an invalid value
        invalid_dataset["collections"][0]["fields"][0]["fidesops_meta"] = {
            "data_type": "stringsssssss"
        }

        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=invalid_dataset
        )

        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "The data type stringsssssss is not supported."
        )

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_put_validate_dataset_invalid_fidesops_meta(
        self, auth_header, example_datasets, validate_dataset_url, api_client
    ):
        invalid_dataset = example_datasets[0]
        # Add an invalid fidesops_meta annotation to ensure our type-checking is comprehensive
        invalid_dataset["collections"][0]["fields"][0]["fidesops_meta"] = {
            "references": [
                {
                    "dataset": "postgres_example_test_dataset",
                    "field": "another.field",
                    "direction": "invalid direction!",
                },
            ]
        }
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=invalid_dataset
        )
        assert response.status_code == 422
        details = response.json()["detail"]
        assert [
            "body",
            "collections",
            0,
            "fields",
            0,
            "fides_meta",
            "references",
            0,
            "direction",
        ] in [e["loc"] for e in details]

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_put_validate_dataset_invalid_category(
        self, auth_header, example_datasets, validate_dataset_url, api_client
    ):
        invalid_dataset = example_datasets[0].copy()
        invalid_dataset["collections"][0]["fields"][0]["data_categories"].append(
            "user.invalid.category"
        )
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=invalid_dataset
        )
        assert response.status_code == 422
        details = response.json()["detail"]
        assert ["collections", 0, "fields", 0, "data_categories"] in [
            e["loc"] for e in details
        ]

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_put_validate_dataset_invalid_connection_key(
        self, auth_header, example_datasets, api_client
    ):
        path = V1_URL_PREFIX + DATASET_VALIDATE
        path_params = {"connection_key": "nonexistent_key"}
        validate_dataset_url = path.format(**path_params)

        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=example_datasets[0]
        )
        assert response.status_code == 404

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_put_validate_dataset_invalid_traversal(
        self, auth_header, example_datasets, validate_dataset_url, api_client
    ):
        invalid_dataset = example_datasets[0].copy()

        # Remove all the "reference" annotations; this will make traversal impossible
        for collection in invalid_dataset["collections"]:
            for field in collection["fields"]:
                if field.get("fides_meta"):
                    field["fides_meta"]["references"] = None
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=invalid_dataset
        )
        assert response.status_code == 200
        response_body = response.json()
        assert response_body["dataset"]
        assert response_body["traversal_details"]
        assert response_body["traversal_details"]["is_traversable"] is False
        assert (
            "Some nodes were not reachable" in response_body["traversal_details"]["msg"]
        )
        assert (
            "postgres_example_test_dataset:address"
            in response_body["traversal_details"]["msg"]
        )

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_validate_dataset_that_references_another_dataset(
        self, auth_header, example_datasets, validate_dataset_url, api_client
    ):
        dataset = example_datasets[1]

        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=dataset
        )
        assert response.status_code == 200
        response_body = response.json()
        assert response_body["dataset"]
        assert response_body["traversal_details"]
        assert response_body["traversal_details"]["is_traversable"] is False
        assert (
            "Referred to object postgres_example_test_dataset:customer:id does not exist"
            == response_body["traversal_details"]["msg"]
        )

    @pytest.mark.unit_saas
    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_validate_saas_dataset_invalid_traversal(
        self,
        auth_header,
        saas_example_connection_config_with_invalid_saas_config,
        saas_example_dataset,
        api_client,
    ):
        path = V1_URL_PREFIX + DATASET_VALIDATE
        path_params = {
            "connection_key": saas_example_connection_config_with_invalid_saas_config.key
        }
        validate_dataset_url = path.format(**path_params)

        response = api_client.put(
            validate_dataset_url,
            headers=auth_header,
            json=saas_example_dataset,
        )
        assert response.status_code == 200

        response_body = response.json()
        assert response_body["dataset"]
        assert response_body["traversal_details"]
        assert response_body["traversal_details"]["is_traversable"] is False
        assert (
            response_body["traversal_details"]["msg"]
            == "Some nodes were not reachable: saas_connector_example:messages"
        )

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_put_validate_dataset(
        self, auth_header, example_datasets, validate_dataset_url, api_client
    ):
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=example_datasets[0]
        )
        assert response.status_code == 200
        response_body = response.json()
        assert response_body["dataset"]
        assert response_body["dataset"]["fides_key"] == "postgres_example_test_dataset"
        assert response_body["traversal_details"]
        assert response_body["traversal_details"]["is_traversable"] is True
        assert response_body["traversal_details"]["msg"] is None


@pytest.mark.asyncio
class TestPutDatasetConfigs:
    @pytest.fixture
    def datasets_url(self, connection_config):
        path = V1_URL_PREFIX + DATASET_CONFIGS
        path_params = {"connection_key": connection_config.key}
        return path.format(**path_params)

    @pytest.fixture
    def request_body(self, ctl_dataset):
        return [
            {
                "fides_key": "test_fides_key",
                "ctl_dataset_fides_key": ctl_dataset.fides_key,
            }
        ]

    def test_patch_dataset_configs_not_authenticated(
        self, datasets_url, api_client, request_body
    ):
        response = api_client.patch(datasets_url, headers={}, json=request_body)
        assert response.status_code == 401

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_patch_dataset_configs_wrong_scope(
        self, auth_header, request_body, datasets_url, api_client
    ):
        response = api_client.patch(
            datasets_url, headers=auth_header, json=request_body
        )
        assert response.status_code == 403

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_create_dataset_configs_by_ctl_dataset_key(
        self,
        auth_header,
        ctl_dataset,
        api_client,
        datasets_url,
        db,
        request_body,
    ):
        response = api_client.patch(
            datasets_url,
            headers=auth_header,
            json=request_body,
        )
        assert response.status_code == 200
        dataset_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="test_fides_key"
        )
        assert dataset_config.ctl_dataset_id == ctl_dataset.id
        assert (
            dataset_config.ctl_dataset.fides_key == ctl_dataset.fides_key
        ), "Differs from datasetconfig.fides_key in this case"

        succeeded = response.json()["succeeded"][0]
        assert (
            succeeded["fides_key"] == "postgres_example_subscriptions_dataset"
        ), "Returns the fides_key of the ctl_dataset not the DatasetConfig"
        assert succeeded["collections"] == Dataset.from_orm(ctl_dataset).collections

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_create_datasetconfigs_bad_data_category(
        self,
        auth_header,
        ctl_dataset,
        api_client,
        datasets_url,
        db,
        request_body,
    ):
        ctl_dataset.collections[0]["fields"][0]["data_categories"] = ["bad_category"]
        flag_modified(ctl_dataset, "collections")
        db.add(ctl_dataset)
        db.commit()
        db.refresh(ctl_dataset)

        response = api_client.patch(
            datasets_url,
            headers=auth_header,
            json=request_body,
        )
        assert response.status_code == 422
        dataset_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="test_fides_key"
        )
        assert dataset_config is None
        assert (
            response.json()["detail"][0]["msg"]
            == "The data category bad_category is not supported."
        )

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_create_datasets_configs_invalid_connection_key(
        self, auth_header, request_body, api_client
    ):
        path = V1_URL_PREFIX + DATASET_CONFIGS
        path_params = {"connection_key": "nonexistent_key"}
        datasets_url = path.format(**path_params)

        response = api_client.patch(
            datasets_url, headers=auth_header, json=request_body
        )
        assert response.status_code == 404

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_dataset_configs_ctl_dataset_id_does_not_exist(
        self, auth_header, request_body, api_client, datasets_url
    ):
        request_body.append(
            {
                "fides_key": "second_dataset_config",
                "ctl_dataset_fides_key": "bad_ctl_dataset_key",
            }
        )

        response = api_client.patch(
            datasets_url, headers=auth_header, json=request_body
        )
        assert response.status_code == 404

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_dataset_configs_bulk_create_limit_exceeded(
        self, auth_header, api_client, request_body, datasets_url
    ):
        payload = []
        for _ in range(0, 51):
            payload.append(request_body[0])

        response = api_client.patch(datasets_url, headers=auth_header, json=payload)

        assert 422 == response.status_code
        assert (
            response.json()["detail"][0]["msg"]
            == "ensure this value has at most 50 items"
        )

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_create_dataset_configs_bulk_create(
        self, auth_header, ctl_dataset, api_client, datasets_url, db, request_body
    ):
        request_body.append(
            {
                "fides_key": "second_dataset_config",
                "ctl_dataset_fides_key": ctl_dataset.fides_key,
            }
        )

        response = api_client.patch(
            datasets_url,
            headers=auth_header,
            json=request_body,
        )

        assert response.status_code == 200
        response_body = response.json()
        assert len(response_body["succeeded"]) == 2
        assert len(response_body["failed"]) == 0

        first_dataset_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="test_fides_key"
        )
        assert first_dataset_config.ctl_dataset == ctl_dataset
        assert (
            response_body["succeeded"][0]["collections"]
            == Dataset.from_orm(first_dataset_config.ctl_dataset).collections
        )
        assert response_body["succeeded"][0]["fides_key"] == ctl_dataset.fides_key
        assert len(first_dataset_config.ctl_dataset.collections) == 1

        second_dataset_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="second_dataset_config"
        )
        assert (
            response_body["succeeded"][1]["collections"]
            == Dataset.from_orm(second_dataset_config.ctl_dataset).collections
        )
        assert response_body["succeeded"][1]["fides_key"] == ctl_dataset.fides_key
        assert second_dataset_config.ctl_dataset == ctl_dataset

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_update_dataset_configs(
        self, auth_header, ctl_dataset, api_client, datasets_url, db, dataset_config
    ):

        old_ctl_dataset_id = dataset_config.ctl_dataset.id
        assert dataset_config.ctl_dataset == ctl_dataset
        updated = dataset_config.updated_at

        db.expunge(ctl_dataset)
        make_transient(ctl_dataset)

        ctl_dataset.id = str(uuid.uuid4())
        ctl_dataset.fides_key = "new_ctl_dataset"
        ctl_dataset.description = "updated description"
        db.add(ctl_dataset)
        db.commit()
        db.refresh(ctl_dataset)

        response = api_client.patch(
            datasets_url,
            headers=auth_header,
            json=[
                {
                    "fides_key": dataset_config.fides_key,
                    "ctl_dataset_fides_key": "new_ctl_dataset",
                }
            ],
        )

        assert response.status_code == 200
        response_body = response.json()
        assert len(response_body["succeeded"]) == 1
        assert len(response_body["failed"]) == 0

        db.refresh(dataset_config)
        assert dataset_config.ctl_dataset_id != old_ctl_dataset_id
        assert dataset_config.updated_at != updated
        assert response_body["succeeded"][0]["fides_key"] == "new_ctl_dataset"
        assert response_body["succeeded"][0]["description"] == "updated description"
        assert dataset_config.ctl_dataset.description == "updated description"
        assert len(dataset_config.ctl_dataset.collections) == 1

    @pytest.mark.unit_saas
    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_dataset_configs_missing_saas_config(
        self,
        auth_header,
        saas_example_connection_config_without_saas_config,
        saas_ctl_dataset,
        api_client,
    ):
        path = V1_URL_PREFIX + DATASET_CONFIGS
        path_params = {
            "connection_key": saas_example_connection_config_without_saas_config.key
        }
        datasets_url = path.format(**path_params)

        response = api_client.patch(
            datasets_url,
            headers=auth_header,
            json=[
                {
                    "fides_key": saas_ctl_dataset.fides_key,
                    "ctl_dataset_fides_key": saas_ctl_dataset.fides_key,
                }
            ],
        )
        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == f"Connection config '{saas_example_connection_config_without_saas_config.key}' "
            "must have a SaaS config before validating or adding a dataset"
        )

    @pytest.mark.unit_saas
    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_dataset_configs_extra_reference(
        self,
        auth_header,
        saas_example_connection_config,
        saas_ctl_dataset,
        api_client,
        db,
    ):
        path = V1_URL_PREFIX + DATASET_CONFIGS
        path_params = {"connection_key": saas_example_connection_config.key}
        datasets_url = path.format(**path_params)

        saas_ctl_dataset.collections[0]["fields"][0]["fides_meta"]["references"] = [
            {
                "dataset": "postgres_example_test_dataset",
                "field": "another.field",
                "direction": "from",
            },
        ]
        flag_modified(saas_ctl_dataset, "collections")
        db.add(saas_ctl_dataset)
        db.commit()

        response = api_client.patch(
            datasets_url,
            headers=auth_header,
            json=[
                {
                    "fides_key": saas_example_connection_config.saas_config[
                        "fides_key"
                    ],
                    "ctl_dataset_fides_key": saas_ctl_dataset.fides_key,
                }
            ],
        )
        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == "A dataset for a ConnectionConfig type of 'saas' is not allowed to have "
            "references or identities. Please add them to the SaaS config."
        )

    @pytest.mark.unit_saas
    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_dataset_configs_extra_identity(
        self,
        auth_header,
        saas_example_connection_config,
        saas_ctl_dataset,
        api_client,
        db,
    ):
        path = V1_URL_PREFIX + DATASET_CONFIGS
        path_params = {"connection_key": saas_example_connection_config.key}
        datasets_url = path.format(**path_params)

        saas_ctl_dataset.collections[0]["fields"][0]["fides_meta"]["identity"] = "email"
        flag_modified(saas_ctl_dataset, "collections")
        db.add(saas_ctl_dataset)
        db.commit()

        response = api_client.patch(
            datasets_url,
            headers=auth_header,
            json=[
                {
                    "fides_key": saas_example_connection_config.saas_config[
                        "fides_key"
                    ],
                    "ctl_dataset_fides_key": saas_ctl_dataset.fides_key,
                }
            ],
        )
        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == "A dataset for a ConnectionConfig type of 'saas' is not allowed to have "
            "references or identities. Please add them to the SaaS config."
        ), "Validation is done when attaching dataset to Saas Config"

    @pytest.mark.unit_saas
    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_dataset_configs_fides_key_mismatch(
        self,
        auth_header,
        saas_example_connection_config,
        saas_ctl_dataset,
        api_client,
        db,
    ):
        path = V1_URL_PREFIX + DATASET_CONFIGS
        path_params = {"connection_key": saas_example_connection_config.key}
        datasets_url = path.format(**path_params)

        saas_ctl_dataset.fides_key = "different_key"
        db.add(saas_ctl_dataset)
        db.commit()

        response = api_client.patch(
            datasets_url,
            headers=auth_header,
            json=[
                {
                    "fides_key": saas_example_connection_config.saas_config[
                        "fides_key"
                    ],
                    "ctl_dataset_fides_key": saas_ctl_dataset.fides_key,
                }
            ],
        )

        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == "The fides_key 'different_key' of the dataset does not match the fides_key "
            "'saas_connector_example' of the connection config"
        )

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    @mock.patch("fides.api.ops.models.datasetconfig.DatasetConfig.create_or_update")
    def test_patch_dataset_configs_failed_response(
        self, mock_create, auth_header, request_body, datasets_url, api_client
    ):
        mock_create.side_effect = HTTPException(mock.Mock(status=400), "Test error")
        response = api_client.patch(
            datasets_url, headers=auth_header, json=request_body
        )
        assert response.status_code == 200  # Returns 200 regardless
        response_body = response.json()
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1

        for failed_response in response_body["failed"]:
            assert "Dataset create/update failed" in failed_response["message"]
            assert set(failed_response.keys()) == {"message", "data"}

        for _, failed in enumerate(response_body["failed"]):
            assert failed["data"]["fides_key"] == request_body[0]["fides_key"]

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_dataset_configs_failed_ctl_dataset_validation(
        self, auth_header, ctl_dataset, api_client, datasets_url, db, request_body
    ):
        ctl_dataset.organization_fides_key = None
        db.add(ctl_dataset)
        db.commit()
        db.refresh(ctl_dataset)

        response = api_client.patch(
            datasets_url,
            headers=auth_header,
            json=request_body,
        )
        assert response.status_code == 422


class TestPutDatasets:
    @pytest.fixture
    def datasets_url(self, connection_config):
        path = V1_URL_PREFIX + DATASETS
        path_params = {"connection_key": connection_config.key}
        return path.format(**path_params)

    def test_patch_datasets_not_authenticated(
        self, example_datasets, datasets_url, api_client
    ):
        response = api_client.patch(datasets_url, headers={}, json=example_datasets)
        assert response.status_code == 401

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_patch_datasets_wrong_scope(
        self, auth_header, example_datasets, datasets_url, api_client
    ):
        response = api_client.patch(
            datasets_url, headers=auth_header, json=example_datasets
        )
        assert response.status_code == 403

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_datasets_invalid_connection_key(
        self, auth_header, example_datasets, api_client
    ):
        path = V1_URL_PREFIX + DATASETS
        path_params = {"connection_key": "nonexistent_key"}
        datasets_url = path.format(**path_params)

        response = api_client.patch(
            datasets_url, headers=auth_header, json=example_datasets
        )
        assert response.status_code == 404

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_datasets_bulk_create_limit_exceeded(
        self, auth_header, api_client, datasets_url
    ):
        payload = []
        for i in range(0, 51):
            payload.append({"collections": [{"fields": [], "fides_key": i}]})

        response = api_client.patch(datasets_url, headers=auth_header, json=payload)

        assert 422 == response.status_code
        assert (
            response.json()["detail"][0]["msg"]
            == "ensure this value has at most 50 items"
        )

    @pytest.mark.usefixtures("connection_config")
    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_datasets_bulk_create(
        self, auth_header, example_datasets, datasets_url, api_client, db
    ):
        response = api_client.patch(
            datasets_url, headers=auth_header, json=example_datasets
        )
        assert response.status_code == 200
        response_body = response.json()
        assert len(response_body["succeeded"]) == 11
        assert len(response_body["failed"]) == 0

        # Confirm that postgres dataset matches the values we provided
        postgres_dataset = response_body["succeeded"][0]
        postgres_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="postgres_example_test_dataset"
        )
        assert postgres_config is not None
        postgres_ctl_dataset = postgres_config.ctl_dataset
        assert postgres_ctl_dataset is not None
        assert postgres_dataset["fides_key"] == "postgres_example_test_dataset"
        assert postgres_dataset["name"] == "Postgres Example Test Dataset"
        assert "Example of a Postgres dataset" in postgres_dataset["description"]
        assert len(postgres_dataset["collections"]) == 11
        assert len(postgres_ctl_dataset.collections) == 11

        # Check the mongo dataset was created as well
        mongo_dataset = response_body["succeeded"][1]
        mongo_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="mongo_test"
        )
        assert mongo_config is not None
        mongo_ctl_dataset = mongo_config.ctl_dataset
        assert mongo_ctl_dataset is not None
        assert mongo_dataset["fides_key"] == "mongo_test"
        assert mongo_dataset["name"] == "Mongo Example Test Dataset"
        assert "Example of a Mongo dataset" in mongo_dataset["description"]
        assert len(mongo_dataset["collections"]) == 9
        assert len(mongo_ctl_dataset.collections) == 9

        # Check the mssql dataset
        mssql_dataset = response_body["succeeded"][4]
        mssql_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="mssql_example_test_dataset"
        )
        assert mssql_config is not None
        mssql_ctl_dataset = mssql_config.ctl_dataset
        assert mssql_ctl_dataset is not None
        assert mssql_dataset["fides_key"] == "mssql_example_test_dataset"
        assert mssql_dataset["name"] == "Microsoft SQLServer Example Test Dataset"
        assert (
            "Example of a Microsoft SQLServer dataset" in mssql_dataset["description"]
        )
        assert len(mssql_dataset["collections"]) == 11
        assert len(mssql_ctl_dataset.collections) == 11

        # check the mysql dataset
        mysql_dataset = response_body["succeeded"][5]
        mysql_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="mysql_example_test_dataset"
        )
        assert mysql_config is not None
        mysql_ctl_dataset = mysql_config.ctl_dataset
        assert mysql_ctl_dataset is not None
        assert mysql_dataset["fides_key"] == "mysql_example_test_dataset"
        assert mysql_dataset["name"] == "MySQL Example Test Dataset"
        assert "Example of a MySQL dataset" in mysql_dataset["description"]
        assert len(mysql_dataset["collections"]) == 11
        assert len(mssql_ctl_dataset.collections) == 11

        # check the mariadb dataset
        mariadb_dataset = response_body["succeeded"][6]
        mariadb_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="mariadb_example_test_dataset"
        )
        assert mariadb_config is not None
        mariadb_ctl_dataset = mariadb_config.ctl_dataset
        assert mariadb_ctl_dataset is not None
        assert mariadb_dataset["fides_key"] == "mariadb_example_test_dataset"
        assert mariadb_dataset["name"] == "MariaDB Example Test Dataset"
        assert "Example of a MariaDB dataset" in mariadb_dataset["description"]
        assert len(mariadb_dataset["collections"]) == 11
        assert len(mssql_ctl_dataset.collections) == 11

        postgres_config.delete(db)
        postgres_ctl_dataset.delete(db)

        mongo_config.delete(db)
        mongo_ctl_dataset.delete(db)

        mssql_config.delete(db)
        mssql_ctl_dataset.delete(db)

        mysql_config.delete(db)
        mysql_ctl_dataset.delete(db)

        mariadb_config.delete(db)
        mariadb_ctl_dataset.delete(db)

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_datasets_bulk_update(
        self, auth_header, example_datasets, datasets_url, api_client, db
    ):
        # Create first, then update
        api_client.patch(datasets_url, headers=auth_header, json=example_datasets)

        updated_datasets = example_datasets.copy()
        # Remove all collections from the postgres example, except for the customer table.
        # Note we also need to remove customer.address_id as it references the addresses table
        updated_datasets[0]["collections"] = [
            c for c in updated_datasets[0]["collections"] if c["name"] == "customer"
        ]
        updated_datasets[0]["collections"][0]["fields"] = [
            f
            for f in updated_datasets[0]["collections"][0]["fields"]
            if f["name"] != "address_id"
        ]
        # Remove the birthday field from the mongo example
        updated_datasets[1]["collections"][0]["fields"] = [
            f
            for f in updated_datasets[1]["collections"][0]["fields"]
            if f["name"] != "birthday"
        ]
        # Remove city field from snowflake example
        updated_datasets[2]["collections"][0]["fields"] = [
            f
            for f in updated_datasets[1]["collections"][0]["fields"]
            if f["name"] != "city"
        ]
        # Remove city field from mssql example
        updated_datasets[4]["collections"][0]["fields"] = [
            f
            for f in updated_datasets[1]["collections"][0]["fields"]
            if f["name"] != "city"
        ]
        # Remove city field from bigquery example
        updated_datasets[7]["collections"][0]["fields"] = [
            f
            for f in updated_datasets[1]["collections"][0]["fields"]
            if f["name"] != "city"
        ]
        response = api_client.patch(
            datasets_url, headers=auth_header, json=updated_datasets
        )

        assert response.status_code == 200
        response_body = response.json()
        assert len(response_body["succeeded"]) == 11
        assert len(response_body["failed"]) == 0

        # test postgres
        postgres_dataset = response_body["succeeded"][0]
        assert postgres_dataset["fides_key"] == "postgres_example_test_dataset"
        assert (
            len(postgres_dataset["collections"]) == 1
        )  # all non-customer fields should be removed
        postgres_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="postgres_example_test_dataset"
        )
        assert postgres_config is not None
        assert postgres_config.updated_at is not None
        postgres_ctl_dataset = postgres_config.ctl_dataset
        assert postgres_ctl_dataset is not None
        assert len(postgres_ctl_dataset.collections) == 1

        # test mongo
        mongo_dataset = response_body["succeeded"][1]
        assert mongo_dataset["fides_key"] == "mongo_test"
        assert "birthday" not in [
            f["name"] for f in mongo_dataset["collections"][0]["fields"]
        ]  # "birthday field should be removed
        mongo_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="mongo_test"
        )
        assert mongo_config is not None
        assert mongo_config.updated_at is not None
        mongo_ctl_dataset = mongo_config.ctl_dataset
        assert mongo_ctl_dataset is not None
        assert "birthday" not in [
            f["name"] for f in mongo_ctl_dataset.collections[0]["fields"]
        ]  # "birthday field should be removed

        # test snowflake
        snowflake_dataset = response_body["succeeded"][2]
        assert snowflake_dataset["fides_key"] == "snowflake_example_test_dataset"
        assert "city" not in [
            f["name"] for f in snowflake_dataset["collections"][0]["fields"]
        ]
        snowflake_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="snowflake_example_test_dataset"
        )
        assert snowflake_config is not None
        assert snowflake_config.updated_at is not None
        snowflake_ctl_dataset = snowflake_config.ctl_dataset
        assert "city" not in [
            f["name"] for f in snowflake_ctl_dataset.collections[0]["fields"]
        ]

        # test mssql
        mssql_dataset = response_body["succeeded"][4]
        assert mssql_dataset["fides_key"] == "mssql_example_test_dataset"
        assert "city" not in [
            f["name"] for f in mssql_dataset["collections"][0]["fields"]
        ]
        mssql_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="mssql_example_test_dataset"
        )
        assert mssql_config is not None
        assert mssql_config.updated_at is not None
        mssql_ctl_dataset = mssql_config.ctl_dataset
        assert mssql_ctl_dataset is not None
        assert "city" not in [
            f["name"] for f in mssql_ctl_dataset.collections[0]["fields"]
        ]

        # test bigquery
        bigquery_dataset = response_body["succeeded"][7]
        assert bigquery_dataset["fides_key"] == "bigquery_example_test_dataset"
        assert "city" not in [
            f["name"] for f in bigquery_dataset["collections"][0]["fields"]
        ]
        bigquery_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="bigquery_example_test_dataset"
        )
        assert bigquery_config is not None
        assert bigquery_config.updated_at is not None
        bigquery_ctl_dataset = bigquery_config.ctl_dataset
        assert "city" not in [
            f["name"] for f in bigquery_ctl_dataset.collections[0]["fields"]
        ]

        postgres_config.delete(db)
        postgres_ctl_dataset.delete(db)

        mongo_config.delete(db)
        mongo_ctl_dataset.delete(db)

        snowflake_config.delete(db)
        snowflake_ctl_dataset.delete(db)

        mssql_config.delete(db)
        mssql_ctl_dataset.delete(db)

        bigquery_config.delete(db)
        bigquery_ctl_dataset.delete(db)

    @pytest.mark.unit_saas
    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_datasets_missing_saas_config(
        self,
        auth_header,
        saas_example_connection_config_without_saas_config,
        saas_example_dataset,
        api_client,
    ):
        path = V1_URL_PREFIX + DATASETS
        path_params = {
            "connection_key": saas_example_connection_config_without_saas_config.key
        }
        datasets_url = path.format(**path_params)

        response = api_client.patch(
            datasets_url, headers=auth_header, json=[saas_example_dataset]
        )
        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == f"Connection config '{saas_example_connection_config_without_saas_config.key}' "
            "must have a SaaS config before validating or adding a dataset"
        )

    @pytest.mark.unit_saas
    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_datasets_extra_reference(
        self,
        auth_header,
        saas_example_connection_config,
        saas_example_dataset,
        api_client,
    ):
        path = V1_URL_PREFIX + DATASETS
        path_params = {"connection_key": saas_example_connection_config.key}
        datasets_url = path.format(**path_params)

        invalid_dataset = saas_example_dataset
        invalid_dataset["collections"][0]["fields"][0]["fidesops_meta"] = {
            "references": [
                {
                    "dataset": "postgres_example_test_dataset",
                    "field": "another.field",
                    "direction": "from",
                },
            ]
        }

        response = api_client.patch(
            datasets_url, headers=auth_header, json=[invalid_dataset]
        )
        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == "A dataset for a ConnectionConfig type of 'saas' is not allowed to have "
            "references or identities. Please add them to the SaaS config."
        )

    @pytest.mark.unit_saas
    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_datasets_extra_identity(
        self,
        auth_header,
        saas_example_connection_config,
        saas_example_dataset,
        api_client,
        db,
    ):
        path = V1_URL_PREFIX + DATASETS
        path_params = {"connection_key": saas_example_connection_config.key}
        datasets_url = path.format(**path_params)

        invalid_dataset = saas_example_dataset
        invalid_dataset["collections"][0]["fields"][0]["fidesops_meta"] = {
            "identity": "email"
        }

        response = api_client.patch(
            datasets_url, headers=auth_header, json=[invalid_dataset]
        )
        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == "A dataset for a ConnectionConfig type of 'saas' is not allowed to have "
            "references or identities. Please add them to the SaaS config."
        )

    @pytest.mark.unit_saas
    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_datasets_fides_key_mismatch(
        self,
        auth_header,
        saas_example_connection_config,
        saas_example_dataset,
        api_client,
        db,
    ):
        path = V1_URL_PREFIX + DATASETS
        path_params = {"connection_key": saas_example_connection_config.key}
        datasets_url = path.format(**path_params)

        invalid_dataset = saas_example_dataset
        invalid_dataset["fides_key"] = "different_key"

        response = api_client.patch(
            datasets_url, headers=auth_header, json=[invalid_dataset]
        )
        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == "The fides_key 'different_key' of the dataset does not match the fides_key "
            "'saas_connector_example' of the connection config"
        )

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    @mock.patch(
        "fides.api.ops.models.datasetconfig.DatasetConfig.upsert_with_ctl_dataset"
    )
    def test_patch_datasets_failed_response(
        self, mock_create, auth_header, example_datasets, datasets_url, api_client
    ):
        mock_create.side_effect = HTTPException(mock.Mock(status=400), "Test error")
        response = api_client.patch(
            datasets_url, headers=auth_header, json=example_datasets
        )
        assert response.status_code == 200  # Returns 200 regardless
        response_body = response.json()
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 11

        for failed_response in response_body["failed"]:
            assert "Dataset create/update failed" in failed_response["message"]
            assert set(failed_response.keys()) == {"message", "data"}

        for index, failed in enumerate(response_body["failed"]):
            assert failed["data"]["fides_key"] == example_datasets[index]["fides_key"]


class TestPutYamlDatasets:
    @pytest.fixture
    def dataset_url(self, connection_config):
        path = V1_URL_PREFIX + YAML_DATASETS
        path_params = {"connection_key": connection_config.key}
        return path.format(**path_params)

    def test_patch_dataset_not_authenticated(
        self, example_yaml_dataset, dataset_url, api_client
    ):
        response = api_client.patch(dataset_url, headers={}, data=example_yaml_dataset)
        assert response.status_code == 401

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_patch_datasets_wrong_scope(
        self, auth_header, example_yaml_dataset, dataset_url, api_client
    ):
        response = api_client.patch(
            dataset_url, headers=auth_header, data=example_yaml_dataset
        )
        assert response.status_code == 403

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_dataset_invalid_connection_key(
        self, auth_header, example_yaml_dataset, api_client
    ):
        path = V1_URL_PREFIX + YAML_DATASETS
        path_params = {"connection_key": "nonexistent_key"}
        dataset_url = path.format(**path_params)

        response = api_client.patch(
            dataset_url, headers=auth_header, data=example_yaml_dataset
        )
        assert response.status_code == 404

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_dataset_invalid_content_type(
        self, auth_header, dataset_url, example_datasets, api_client
    ):
        response = api_client.patch(
            dataset_url, headers=auth_header, json=example_datasets
        )
        assert response.status_code == 415

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_dataset_invalid_content(
        self, auth_header, dataset_url, example_invalid_yaml_dataset, api_client
    ):
        headers = {"Content-type": "application/x-yaml"}
        headers.update(auth_header)
        response = api_client.patch(
            dataset_url, headers=headers, data=example_invalid_yaml_dataset
        )
        assert response.status_code == 400

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    @mock.patch(
        "fides.api.ops.models.datasetconfig.DatasetConfig.upsert_with_ctl_dataset"
    )
    def test_patch_datasets_failed_response(
        self, mock_create, auth_header, example_yaml_dataset, dataset_url, api_client
    ):
        mock_create.side_effect = HTTPException(mock.Mock(status=400), "Test error")
        headers = {"Content-type": "application/x-yaml"}
        headers.update(auth_header)
        response = api_client.patch(
            dataset_url, headers=headers, data=example_yaml_dataset
        )
        assert response.status_code == 200  # Returns 200 regardless
        response_body = response.json()
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1

        for failed_response in response_body["failed"]:
            assert "Dataset create/update failed" in failed_response["message"]
            assert set(failed_response.keys()) == {"message", "data"}

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_dataset_create(
        self, auth_header, example_yaml_dataset, dataset_url, api_client, db
    ):
        headers = {"Content-type": "application/x-yaml"}
        headers.update(auth_header)
        response = api_client.patch(
            dataset_url, headers=headers, data=example_yaml_dataset
        )

        assert response.status_code == 200
        response_body = response.json()
        assert len(response_body["succeeded"]) == 1
        assert len(response_body["failed"]) == 0

        # Confirm that postgres dataset matches the values we provided
        postgres_dataset = response_body["succeeded"][0]
        postgres_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="postgres_example_test_dataset"
        )
        assert postgres_config is not None
        assert postgres_dataset["fides_key"] == "postgres_example_test_dataset"
        assert postgres_dataset["name"] == "Postgres Example Test Dataset"
        assert "Example of a Postgres dataset" in postgres_dataset["description"]
        assert len(postgres_dataset["collections"]) == 11

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_patch_datasets_create(
        self, auth_header, example_yaml_datasets, dataset_url, api_client
    ):
        headers = {"Content-type": "application/x-yaml"}
        headers.update(auth_header)
        response = api_client.patch(
            dataset_url, headers=headers, data=example_yaml_datasets
        )

        assert response.status_code == 200
        response_body = response.json()
        assert len(response_body["succeeded"]) == 2
        assert len(response_body["failed"]) == 0


class TestGetDatasets:
    @pytest.fixture
    def datasets_url(self, connection_config):
        path = V1_URL_PREFIX + DATASETS
        path_params = {"connection_key": connection_config.key}
        return path.format(**path_params)

    @pytest.mark.usefixtures("dataset_config")
    def test_get_datasets_not_authenticated(self, datasets_url, api_client):
        response = api_client.get(datasets_url, headers={})
        assert response.status_code == 401

    @pytest.mark.usefixtures("dataset_config")
    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_get_datasets_invalid_connection_key(
        self, auth_header, datasets_url, api_client
    ):
        path = V1_URL_PREFIX + DATASETS
        path_params = {"connection_key": "nonexistent_key"}
        datasets_url = path.format(**path_params)

        response = api_client.get(datasets_url, headers=auth_header)
        assert response.status_code == 404

    @pytest.mark.usefixtures("dataset_config")
    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_get_datasets(self, auth_header, datasets_url, api_client):
        response = api_client.get(datasets_url, headers=auth_header)
        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["items"]) == 1
        dataset_response = response_body["items"][0]
        assert dataset_response["fides_key"] == "postgres_example_subscriptions_dataset"
        assert len(dataset_response["collections"]) == 1

        assert response_body["total"] == 1
        assert response_body["page"] == 1
        assert response_body["size"] == Params().size


class TestGetDatasetConfigs:
    @pytest.fixture
    def datasets_url(self, connection_config):
        path = V1_URL_PREFIX + DATASET_CONFIGS
        path_params = {"connection_key": connection_config.key}
        return path.format(**path_params)

    def test_get_dataset_configs_not_authenticated(self, datasets_url, api_client):
        response = api_client.get(datasets_url, headers={})
        assert response.status_code == 401

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_get_dataset_configs_invalid_connection_key(
        self, auth_header, datasets_url, api_client
    ):
        path = V1_URL_PREFIX + DATASET_CONFIGS
        path_params = {"connection_key": "nonexistent_key"}
        datasets_url = path.format(**path_params)

        response = api_client.get(datasets_url, headers=auth_header)
        assert response.status_code == 404

    @pytest.mark.usefixtures("dataset_config")
    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_get_dataset_configs(self, auth_header, datasets_url, api_client):
        response = api_client.get(datasets_url, headers=auth_header)
        assert response.status_code == 200

        response_body = response.json()
        assert len(response_body["items"]) == 1
        dataset_response = response_body["items"][0]
        assert dataset_response["fides_key"] == "postgres_example_subscriptions_dataset"

        assert (
            dataset_response["ctl_dataset"]["fides_key"]
            == "postgres_example_subscriptions_dataset"
        )
        assert len(dataset_response["ctl_dataset"]["collections"]) == 1

        assert response_body["total"] == 1
        assert response_body["page"] == 1
        assert response_body["size"] == Params().size


def get_dataset_url(
    connection_config=None,
    dataset_config=None,
):
    """Helper to construct the DATASET_BY_KEY URL, substituting valid/invalid keys in the path"""
    path = V1_URL_PREFIX + DATASET_BY_KEY
    connection_key = "nonexistent_key"
    if connection_config:
        connection_key = connection_config.key
    fides_key = "nonexistent_key"
    if dataset_config:
        fides_key = dataset_config.fides_key
    path_params = {"connection_key": connection_key, "fides_key": fides_key}
    return path.format(**path_params)


class TestGetDataset:
    def test_get_dataset_not_authenticated(
        self, dataset_config, connection_config, api_client
    ):
        dataset_url = get_dataset_url(connection_config, dataset_config)
        response = api_client.get(dataset_url, headers={})
        assert response.status_code == 401

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_get_dataset_wrong_scope(
        self, auth_header, dataset_config, connection_config, api_client
    ):
        dataset_url = get_dataset_url(connection_config, dataset_config)
        response = api_client.get(dataset_url, headers=auth_header)
        assert response.status_code == 403

    @pytest.mark.usefixtures("dataset_config")
    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_get_dataset_does_not_exist(
        self, auth_header, connection_config, api_client
    ):
        dataset_url = get_dataset_url(connection_config, None)
        response = api_client.get(dataset_url, headers=auth_header)
        assert response.status_code == 404

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_get_dataset_invalid_connection_key(
        self, auth_header, dataset_config, connection_config, api_client
    ):
        dataset_url = get_dataset_url(None, dataset_config)
        dataset_url.replace(connection_config.key, "nonexistent_key")
        response = api_client.get(dataset_url, headers=auth_header)
        assert response.status_code == 404

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_get_dataset(
        self, auth_header, dataset_config, connection_config, api_client
    ):
        dataset_url = get_dataset_url(connection_config, dataset_config)
        response = api_client.get(dataset_url, headers=auth_header)
        assert response.status_code == 200

        response_body = response.json()
        assert response_body["fides_key"] == dataset_config.fides_key
        assert len(response_body["collections"]) == 1


def get_dataset_config_url(
    connection_config=None,
    dataset_config=None,
):
    """Helper to construct the DATASETCONFIG_BY_KEY URL, substituting valid/invalid keys in the path"""
    path = V1_URL_PREFIX + DATASETCONFIG_BY_KEY
    connection_key = "nonexistent_key"
    if connection_config:
        connection_key = connection_config.key
    fides_key = "nonexistent_key"
    if dataset_config:
        fides_key = dataset_config.fides_key
    path_params = {"connection_key": connection_key, "fides_key": fides_key}
    return path.format(**path_params)


class TestGetDatasetConfig:
    def test_get_dataset_config_not_authenticated(
        self, dataset_config, connection_config, api_client
    ):
        dataset_url = get_dataset_config_url(connection_config, dataset_config)
        response = api_client.get(dataset_url, headers={})
        assert response.status_code == 401

    @pytest.mark.parametrize("auth_header", [[DATASET_CREATE_OR_UPDATE]], indirect=True)
    def test_get_dataset_config_wrong_scope(
        self, auth_header, dataset_config, connection_config, api_client
    ):
        dataset_url = get_dataset_config_url(connection_config, dataset_config)
        response = api_client.get(dataset_url, headers=auth_header)
        assert response.status_code == 403

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_get_dataset_config_does_not_exist(
        self, auth_header, connection_config, api_client
    ):
        dataset_url = get_dataset_config_url(connection_config, None)
        response = api_client.get(dataset_url, headers=auth_header)
        assert response.status_code == 404

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_get_dataset_config_invalid_connection_key(
        self, auth_header, dataset_config, connection_config, api_client
    ):
        dataset_url = get_dataset_config_url(None, dataset_config)
        dataset_url.replace(connection_config.key, "nonexistent_key")
        response = api_client.get(dataset_url, headers=auth_header)
        assert response.status_code == 404

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_get_dataset_config(
        self, auth_header, dataset_config, connection_config, api_client
    ):
        dataset_url = get_dataset_config_url(connection_config, dataset_config)
        response = api_client.get(dataset_url, headers=auth_header)
        assert response.status_code == 200

        response_body = response.json()
        assert response_body["fides_key"] == dataset_config.fides_key
        assert (
            response_body["ctl_dataset"]["fides_key"]
            == dataset_config.ctl_dataset.fides_key
        )
        assert len(response_body["ctl_dataset"]["collections"]) == 1


class TestDeleteDataset:
    def test_delete_dataset_not_authenticated(
        self, dataset_config, connection_config, api_client
    ):
        dataset_url = get_dataset_url(connection_config, dataset_config)
        response = api_client.delete(dataset_url, headers={})
        assert response.status_code == 401

    @pytest.mark.parametrize("auth_header", [[DATASET_READ]], indirect=True)
    def test_delete_dataset_wrong_scope(
        self, auth_header, dataset_config, connection_config, api_client
    ):
        dataset_url = get_dataset_url(connection_config, dataset_config)
        response = api_client.delete(dataset_url, headers=auth_header)
        assert response.status_code == 403

    @pytest.mark.parametrize("auth_header", [[DATASET_DELETE]], indirect=True)
    def test_delete_dataset_does_not_exist(
        self, auth_header, connection_config, api_client
    ):
        dataset_url = get_dataset_url(connection_config, None)
        response = api_client.delete(dataset_url, headers=auth_header)
        assert response.status_code == 404

    @pytest.mark.parametrize("auth_header", [[DATASET_DELETE]], indirect=True)
    def test_delete_dataset_invalid_connection_key(
        self, auth_header, dataset_config, api_client
    ):
        dataset_url = get_dataset_url(None, dataset_config)
        response = api_client.delete(dataset_url, headers=auth_header)
        assert response.status_code == 404

    @pytest.mark.parametrize("auth_header", [[DATASET_DELETE]], indirect=True)
    def test_delete_dataset(
        self, auth_header, db, connection_config, api_client, ctl_dataset
    ):
        # Create a new dataset config so we don't run into issues trying to clean up an
        # already deleted fixture
        dataset_config = DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "postgres_example_subscriptions",
                "ctl_dataset_id": ctl_dataset.id,
            },
        )

        dataset_url = get_dataset_url(connection_config, dataset_config)
        response = api_client.delete(dataset_url, headers=auth_header)
        assert response.status_code == 204

        assert (
            DatasetConfig.get_by(
                db=db, field="fides_key", value=dataset_config.fides_key
            )
            is None
        )
