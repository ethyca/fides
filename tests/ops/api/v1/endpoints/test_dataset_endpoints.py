import json
import uuid
from typing import Dict, Generator, List, Optional
from unittest import mock
from unittest.mock import Mock
from uuid import uuid4

import pydash
import pytest
from fastapi import HTTPException
from fastapi_pagination import Params
from fideslang import Dataset
from pydash import filter_
from sqlalchemy.orm import Session, make_transient
from sqlalchemy.orm.attributes import flag_modified
from starlette.testclient import TestClient

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.common.api.scope_registry import (
    CTL_DATASET_READ,
    DATASET_CREATE_OR_UPDATE,
    DATASET_DELETE,
    DATASET_READ,
)
from fides.common.api.v1.urn_registry import (
    CONNECTION_DATASETS,
    DATASET_BY_KEY,
    DATASET_CONFIGS,
    DATASET_VALIDATE,
    DATASETCONFIG_BY_KEY,
    DATASETS,
    V1_URL_PREFIX,
    YAML_DATASETS,
)


def _reject_key(dict: Dict, key: str) -> Dict:
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
    assert len(example_datasets[5]["collections"]) == 12
    assert example_datasets[6]["fides_key"] == "mariadb_example_test_dataset"
    assert len(example_datasets[6]["collections"]) == 11
    assert example_datasets[7]["fides_key"] == "bigquery_example_test_dataset"
    assert len(example_datasets[7]["collections"]) == 12
    assert example_datasets[9]["fides_key"] == "email_dataset"
    assert len(example_datasets[9]["collections"]) == 3
    assert example_datasets[11]["fides_key"] == "dynamodb_example_test_dataset"
    assert len(example_datasets[11]["collections"]) == 4
    assert example_datasets[12]["fides_key"] == "postgres_example_test_extended_dataset"


class TestValidateDataset:
    @pytest.fixture
    def validate_dataset_url(self, connection_config) -> str:
        path = V1_URL_PREFIX + DATASET_VALIDATE
        path_params = {"connection_key": connection_config.key}
        return path.format(**path_params)

    def test_put_validate_dataset_not_authenticated(
        self, example_datasets: List, validate_dataset_url: str, api_client
    ) -> None:
        response = api_client.put(
            validate_dataset_url, headers={}, json=example_datasets[0]
        )
        assert response.status_code == 401

    def test_put_validate_dataset_wrong_scope(
        self,
        example_datasets: List,
        validate_dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=example_datasets[0]
        )
        assert response.status_code == 403

    def test_put_validate_dataset_missing_key(
        self,
        example_datasets: List,
        validate_dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        invalid_dataset = _reject_key(example_datasets[0], "fides_key")
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=invalid_dataset
        )
        assert response.status_code == 422
        details = json.loads(response.text)["detail"]
        assert ["body", "fides_key"] in [e["loc"] for e in details]

    def test_put_validate_dataset_missing_collections(
        self,
        example_datasets: List,
        validate_dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        invalid_dataset = _reject_key(example_datasets[0], "collections")
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=invalid_dataset
        )
        assert response.status_code == 422
        details = json.loads(response.text)["detail"]
        assert ["body", "collections"] in [e["loc"] for e in details]

    def test_validate_with_valid_skipped_collections(
        self,
        example_datasets: List,
        validate_dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])

        dataset = example_datasets[0]
        skipped_collection = next(
            col for col in dataset["collections"] if col["name"] == "login"
        )
        skipped_collection["fides_meta"] = {}
        skipped_collection["fides_meta"]["skip_processing"] = True
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=dataset
        )
        assert response.status_code == 200

        details = response.json()["traversal_details"]
        assert details["is_traversable"]

    def test_validate_with_invalid_skipped_collections(
        self,
        example_datasets: List,
        validate_dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])

        dataset = example_datasets[0]
        skipped_collection = next(
            col for col in dataset["collections"] if col["name"] == "address"
        )
        skipped_collection["fides_meta"] = {}
        skipped_collection["fides_meta"]["skip_processing"] = True
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=dataset
        )
        assert response.status_code == 200

        details = response.json()["traversal_details"]
        assert not details["is_traversable"]
        assert (
            details["msg"]
            == "Referred to object postgres_example_test_dataset:address:id does not exist"
        )

    def test_put_validate_dataset_nested_collections(
        self,
        example_datasets: List,
        validate_dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
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
        json_response = json.loads(response.text)
        print(json_response)

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

    def test_put_validate_dataset_invalid_length(
        self,
        example_datasets: List,
        validate_dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
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
            json.loads(response.text)["dataset"]["collections"][0]["fields"][0][
                "fides_meta"
            ]["length"]
            == 123
        )

        # fails with an invalid value
        invalid_dataset["collections"][0]["fields"][0]["fidesops_meta"] = {"length": -1}
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=invalid_dataset
        )

        assert response.status_code == 422
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "Input should be greater than 0"
        )

    def test_put_validate_dataset_invalid_data_type(
        self,
        example_datasets: List,
        validate_dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
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
            json.loads(response.text)["dataset"]["collections"][0]["fields"][0][
                "fides_meta"
            ]["data_type"]
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
            json.loads(response.text)["detail"][0]["msg"]
            == "Value error, The data type stringsssssss is not supported."
        )

    def test_put_validate_dataset_invalid_fidesops_meta(
        self,
        example_datasets: List,
        validate_dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
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
        details = json.loads(response.text)["detail"]
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

    def test_put_validate_dataset_invalid_category(
        self,
        example_datasets: List,
        validate_dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        invalid_dataset = example_datasets[0].copy()
        invalid_dataset["collections"][0]["fields"][0]["data_categories"].append(
            "user.invalid.category"
        )
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=invalid_dataset
        )
        assert response.status_code == 422
        details = json.loads(response.text)["detail"]
        assert ["collections", 0, "fields", 0, "data_categories"] in [
            e["loc"] for e in details
        ]

    def test_put_validate_dataset_invalid_connection_key(
        self, example_datasets: List, api_client: TestClient, generate_auth_header
    ) -> None:
        path = V1_URL_PREFIX + DATASET_VALIDATE
        path_params = {"connection_key": "nonexistent_key"}
        validate_dataset_url = path.format(**path_params)

        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=example_datasets[0]
        )
        assert response.status_code == 404

    def test_put_validate_dataset_invalid_traversal(
        self,
        example_datasets: List,
        validate_dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
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
        response_body = json.loads(response.text)
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

    def test_validate_dataset_that_references_another_dataset(
        self,
        example_datasets: List,
        validate_dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        dataset = example_datasets[1]

        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=dataset
        )
        print(response.text)
        assert response.status_code == 200
        response_body = json.loads(response.text)
        assert response_body["dataset"]
        assert response_body["traversal_details"]
        assert response_body["traversal_details"]["is_traversable"] is False
        assert (
            "Referred to object postgres_example_test_dataset:customer:id does not exist"
            == response_body["traversal_details"]["msg"]
        )

    @pytest.mark.unit_saas
    def test_validate_saas_dataset_invalid_traversal(
        self,
        db,
        saas_example_connection_config_with_invalid_saas_config,
        saas_example_dataset,
        api_client: TestClient,
        generate_auth_header,
    ):
        path = V1_URL_PREFIX + DATASET_VALIDATE
        path_params = {
            "connection_key": saas_example_connection_config_with_invalid_saas_config.key
        }
        validate_dataset_url = path.format(**path_params)

        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.put(
            validate_dataset_url,
            headers=auth_header,
            json=saas_example_dataset,
        )
        assert response.status_code == 200

        response_body = json.loads(response.text)
        assert response_body["dataset"]
        assert response_body["traversal_details"]
        assert response_body["traversal_details"]["is_traversable"] is False
        assert (
            response_body["traversal_details"]["msg"]
            == "Some nodes were not reachable: saas_connector_example:messages"
        )

    def test_put_validate_dataset(
        self,
        example_datasets: List,
        validate_dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.put(
            validate_dataset_url, headers=auth_header, json=example_datasets[0]
        )
        assert response.status_code == 200
        response_body = json.loads(response.text)
        assert response_body["dataset"]
        assert response_body["dataset"]["fides_key"] == "postgres_example_test_dataset"
        assert response_body["traversal_details"]
        assert response_body["traversal_details"]["is_traversable"] is True
        assert response_body["traversal_details"]["msg"] is None


@pytest.mark.asyncio
class TestPatchDatasetConfigs:
    @pytest.fixture
    def datasets_url(self, connection_config) -> str:
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
    ) -> None:
        response = api_client.patch(datasets_url, headers={}, json=request_body)
        assert response.status_code == 401

    def test_patch_dataset_configs_wrong_scope(
        self,
        request_body,
        datasets_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.patch(
            datasets_url, headers=auth_header, json=request_body
        )
        assert response.status_code == 403

    def test_create_dataset_configs_by_ctl_dataset_key(
        self,
        ctl_dataset,
        generate_auth_header,
        api_client,
        datasets_url,
        db,
        request_body,
    ):
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
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
        assert succeeded["collections"] == [
            coll.model_dump(mode="json")
            for coll in Dataset.model_validate(ctl_dataset).collections
        ]

        dataset_config.delete(db)

    def test_create_datasetconfigs_bad_data_category(
        self,
        ctl_dataset,
        generate_auth_header,
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

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
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
            == "Value error, The data category bad_category is not supported."
        )

    def test_create_datasets_configs_invalid_connection_key(
        self, request_body, api_client: TestClient, generate_auth_header
    ) -> None:
        path = V1_URL_PREFIX + DATASET_CONFIGS
        path_params = {"connection_key": "nonexistent_key"}
        datasets_url = path.format(**path_params)

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.patch(
            datasets_url, headers=auth_header, json=request_body
        )
        assert response.status_code == 404

    def test_patch_dataset_configs_ctl_dataset_id_does_not_exist(
        self, request_body, api_client: TestClient, generate_auth_header, datasets_url
    ) -> None:
        request_body.append(
            {
                "fides_key": "second_dataset_config",
                "ctl_dataset_fides_key": "bad_ctl_dataset_key",
            }
        )

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.patch(
            datasets_url, headers=auth_header, json=request_body
        )
        assert response.status_code == 404

    def test_patch_dataset_configs_bulk_create_limit_exceeded(
        self, api_client: TestClient, request_body, generate_auth_header, datasets_url
    ):
        payload = []
        for i in range(0, 51):
            payload.append(request_body[0])

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.patch(datasets_url, headers=auth_header, json=payload)

        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "List should have at most 50 items after validation, not 51"
        )

    def test_patch_create_dataset_configs_bulk_create(
        self,
        ctl_dataset,
        generate_auth_header,
        api_client,
        datasets_url,
        db,
        request_body,
    ):
        request_body.append(
            {
                "fides_key": "second_dataset_config",
                "ctl_dataset_fides_key": ctl_dataset.fides_key,
            }
        )

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.patch(
            datasets_url,
            headers=auth_header,
            json=request_body,
        )

        assert response.status_code == 200
        response_body = json.loads(response.text)
        assert len(response_body["succeeded"]) == 2
        assert len(response_body["failed"]) == 0

        first_dataset_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="test_fides_key"
        )
        assert first_dataset_config.ctl_dataset == ctl_dataset
        assert response_body["succeeded"][0]["collections"] == [
            coll.model_dump(mode="json")
            for coll in Dataset.model_validate(
                first_dataset_config.ctl_dataset
            ).collections
        ]
        assert response_body["succeeded"][0]["fides_key"] == ctl_dataset.fides_key
        assert len(first_dataset_config.ctl_dataset.collections) == 1

        second_dataset_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="second_dataset_config"
        )
        assert response_body["succeeded"][1]["collections"] == [
            coll.model_dump(mode="json")
            for coll in Dataset.model_validate(
                second_dataset_config.ctl_dataset
            ).collections
        ]
        assert response_body["succeeded"][1]["fides_key"] == ctl_dataset.fides_key
        assert second_dataset_config.ctl_dataset == ctl_dataset

        first_dataset_config.delete(db)
        second_dataset_config.delete(db)

    def test_patch_update_dataset_configs(
        self,
        ctl_dataset,
        generate_auth_header,
        api_client,
        datasets_url,
        db,
        request_body,
        dataset_config,
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

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
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
        response_body = json.loads(response.text)
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
    def test_patch_dataset_configs_missing_saas_config(
        self,
        saas_example_connection_config_without_saas_config,
        saas_ctl_dataset,
        api_client: TestClient,
        generate_auth_header,
    ):
        path = V1_URL_PREFIX + DATASET_CONFIGS
        path_params = {
            "connection_key": saas_example_connection_config_without_saas_config.key
        }
        datasets_url = path.format(**path_params)

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
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

        response_body = json.loads(response.text)
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == f"Connection config '{saas_example_connection_config_without_saas_config.key}' "
            "must have a SaaS config before validating or adding a dataset"
        )

    @pytest.mark.unit_saas
    def test_patch_dataset_configs_extra_reference(
        self,
        saas_example_connection_config,
        saas_ctl_dataset,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
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

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
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

        response_body = json.loads(response.text)
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == "A dataset for a ConnectionConfig type of 'saas' is not allowed to have "
            "references or identities. Please add them to the SaaS config."
        )

    @pytest.mark.unit_saas
    def test_patch_dataset_configs_extra_identity(
        self,
        saas_example_connection_config,
        saas_ctl_dataset,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
    ):
        path = V1_URL_PREFIX + DATASET_CONFIGS
        path_params = {"connection_key": saas_example_connection_config.key}
        datasets_url = path.format(**path_params)

        saas_ctl_dataset.collections[0]["fields"][0]["fides_meta"]["identity"] = "email"
        flag_modified(saas_ctl_dataset, "collections")
        db.add(saas_ctl_dataset)
        db.commit()

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
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

        response_body = json.loads(response.text)
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == "A dataset for a ConnectionConfig type of 'saas' is not allowed to have "
            "references or identities. Please add them to the SaaS config."
        ), "Validation is done when attaching dataset to Saas Config"

    @pytest.mark.unit_saas
    def test_patch_dataset_configs_fides_key_mismatch(
        self,
        saas_example_connection_config,
        saas_ctl_dataset,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
    ):
        path = V1_URL_PREFIX + DATASET_CONFIGS
        path_params = {"connection_key": saas_example_connection_config.key}
        datasets_url = path.format(**path_params)

        saas_ctl_dataset.fides_key = "different_key"
        db.add(saas_ctl_dataset)
        db.commit()

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
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

        response_body = json.loads(response.text)
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == "The fides_key 'different_key' of the dataset does not match the fides_key "
            "'saas_connector_example' of the connection config"
        )

    @mock.patch("fides.api.models.datasetconfig.DatasetConfig.create_or_update")
    def test_patch_dataset_configs_failed_response(
        self,
        mock_create: Mock,
        request_body,
        datasets_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        mock_create.side_effect = HTTPException(mock.Mock(status=400), "Test error")
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.patch(
            datasets_url, headers=auth_header, json=request_body
        )
        assert response.status_code == 200  # Returns 200 regardless
        response_body = json.loads(response.text)
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1

        for failed_response in response_body["failed"]:
            assert "Dataset create/update failed" in failed_response["message"]
            assert set(failed_response.keys()) == {"message", "data"}

        for index, failed in enumerate(response_body["failed"]):
            assert failed["data"]["fides_key"] == request_body[0]["fides_key"]

    def test_patch_dataset_configs_failed_ctl_dataset_validation(
        self,
        ctl_dataset,
        generate_auth_header,
        api_client,
        datasets_url,
        db,
        request_body,
    ):
        ctl_dataset.organization_fides_key = None
        db.add(ctl_dataset)
        db.commit()
        db.refresh(ctl_dataset)

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.patch(
            datasets_url,
            headers=auth_header,
            json=request_body,
        )
        assert response.status_code == 422


class TestPutDatasetConfigs:
    @pytest.fixture
    def datasets_url(self, connection_config) -> str:
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

    def test_put_dataset_configs_not_authenticated(
        self, datasets_url, api_client, request_body
    ) -> None:
        response = api_client.put(datasets_url, headers={}, json=request_body)
        assert response.status_code == 401

    def test_put_dataset_configs_wrong_scope(
        self,
        request_body,
        datasets_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.patch(
            datasets_url, headers=auth_header, json=request_body
        )
        assert response.status_code == 403

    def test_put_create_dataset_configs_add_and_remove(
        self,
        db,
        example_datasets,
        generate_auth_header,
        api_client,
        datasets_url,
        connection_config: ConnectionConfig,
    ):
        # create ctl_datasets
        postgres_dataset = CtlDataset(
            **example_datasets[0], organization_fides_key="default_organization"
        )
        db.add(postgres_dataset)
        postgres_extended_dataset = CtlDataset(
            **example_datasets[12], organization_fides_key="default_organization"
        )
        db.add(postgres_extended_dataset)
        db.commit()

        # add the first dataset to the connection
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.put(
            datasets_url,
            headers=auth_header,
            json=[
                {
                    "fides_key": postgres_dataset.fides_key,
                    "ctl_dataset_fides_key": postgres_dataset.fides_key,
                }
            ],
        )
        assert response.status_code == 200

        db.refresh(connection_config)
        assert len(connection_config.datasets) == 1

        # add the second dataset to the connection
        response = api_client.put(
            datasets_url,
            headers=auth_header,
            json=[
                {
                    "fides_key": postgres_dataset.fides_key,
                    "ctl_dataset_fides_key": postgres_dataset.fides_key,
                },
                {
                    "fides_key": postgres_extended_dataset.fides_key,
                    "ctl_dataset_fides_key": postgres_extended_dataset.fides_key,
                },
            ],
        )
        assert response.status_code == 200

        db.refresh(connection_config)
        assert len(connection_config.datasets) == 2

        # verify that the second dataset is removed if it's not included in the payload
        response = api_client.put(
            datasets_url,
            headers=auth_header,
            json=[
                {
                    "fides_key": postgres_dataset.fides_key,
                    "ctl_dataset_fides_key": postgres_dataset.fides_key,
                }
            ],
        )
        assert response.status_code == 200

        db.refresh(connection_config)
        assert len(connection_config.datasets) == 1


class TestPutDatasets:
    @pytest.fixture
    def datasets_url(self, connection_config) -> str:
        path = V1_URL_PREFIX + CONNECTION_DATASETS
        path_params = {"connection_key": connection_config.key}
        return path.format(**path_params)

    def test_patch_datasets_not_authenticated(
        self, example_datasets: List, datasets_url, api_client
    ) -> None:
        response = api_client.patch(datasets_url, headers={}, json=example_datasets)
        assert response.status_code == 401

    def test_patch_datasets_wrong_scope(
        self,
        example_datasets: List,
        datasets_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.patch(
            datasets_url, headers=auth_header, json=example_datasets
        )
        assert response.status_code == 403

    def test_patch_datasets_invalid_connection_key(
        self, example_datasets: List, api_client: TestClient, generate_auth_header
    ) -> None:
        path = V1_URL_PREFIX + CONNECTION_DATASETS
        path_params = {"connection_key": "nonexistent_key"}
        datasets_url = path.format(**path_params)

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.patch(
            datasets_url, headers=auth_header, json=example_datasets
        )
        assert response.status_code == 404

    def test_patch_datasets_bulk_create_limit_exceeded(
        self, api_client: TestClient, db: Session, generate_auth_header, datasets_url
    ):
        payload = []
        for i in range(0, 51):
            payload.append({"collections": [{"fields": [], "fides_key": i}]})

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.patch(datasets_url, headers=auth_header, json=payload)

        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "List should have at most 50 items after validation, not 51"
        )

    def test_patch_datasets_bulk_create(
        self,
        example_datasets: List,
        datasets_url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
        connection_config,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.patch(
            datasets_url, headers=auth_header, json=example_datasets
        )
        assert response.status_code == 200
        response_body = json.loads(response.text)
        assert len(response_body["succeeded"]) == 16
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
        assert len(mysql_dataset["collections"]) == 12
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

        # Confirm that scylla dataset matches the values we provided
        scylladb_dataset = response_body["succeeded"][15]
        scylladb_config = DatasetConfig.get_by(
            db=db, field="fides_key", value="scylladb_example_test_dataset"
        )
        assert scylladb_config is not None
        scylladb_ctl_dataset = scylladb_config.ctl_dataset
        assert scylladb_ctl_dataset is not None
        assert scylladb_dataset["fides_key"] == "scylladb_example_test_dataset"
        assert scylladb_dataset["name"] == "Example ScyllaDB dataset"
        assert (
            "ScyllaDB dataset containing a users table"
            in scylladb_dataset["description"]
        )
        assert len(scylladb_dataset["collections"]) == 4
        assert len(scylladb_ctl_dataset.collections) == 4

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

        scylladb_config.delete(db)
        scylladb_ctl_dataset.delete(db)

    def test_patch_datasets_bulk_update(
        self,
        example_datasets,
        datasets_url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
    ) -> None:
        # Create first, then update
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
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
        response_body = json.loads(response.text)
        assert len(response_body["succeeded"]) == 16
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
    def test_patch_datasets_missing_saas_config(
        self,
        saas_example_connection_config_without_saas_config,
        saas_example_dataset,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
    ):
        path = V1_URL_PREFIX + CONNECTION_DATASETS
        path_params = {
            "connection_key": saas_example_connection_config_without_saas_config.key
        }
        datasets_url = path.format(**path_params)

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.patch(
            datasets_url, headers=auth_header, json=[saas_example_dataset]
        )
        assert response.status_code == 200

        response_body = json.loads(response.text)
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == f"Connection config '{saas_example_connection_config_without_saas_config.key}' "
            "must have a SaaS config before validating or adding a dataset"
        )

    @pytest.mark.unit_saas
    def test_patch_datasets_extra_reference(
        self,
        saas_example_connection_config,
        saas_example_dataset,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
    ):
        path = V1_URL_PREFIX + CONNECTION_DATASETS
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

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.patch(
            datasets_url, headers=auth_header, json=[invalid_dataset]
        )
        assert response.status_code == 200

        response_body = json.loads(response.text)
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == "A dataset for a ConnectionConfig type of 'saas' is not allowed to have "
            "references or identities. Please add them to the SaaS config."
        )

    @pytest.mark.unit_saas
    def test_patch_datasets_extra_identity(
        self,
        saas_example_connection_config,
        saas_example_dataset,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
    ):
        path = V1_URL_PREFIX + CONNECTION_DATASETS
        path_params = {"connection_key": saas_example_connection_config.key}
        datasets_url = path.format(**path_params)

        invalid_dataset = saas_example_dataset
        invalid_dataset["collections"][0]["fields"][0]["fidesops_meta"] = {
            "identity": "email"
        }

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.patch(
            datasets_url, headers=auth_header, json=[invalid_dataset]
        )
        assert response.status_code == 200

        response_body = json.loads(response.text)
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == "A dataset for a ConnectionConfig type of 'saas' is not allowed to have "
            "references or identities. Please add them to the SaaS config."
        )

    @pytest.mark.unit_saas
    def test_patch_datasets_fides_key_mismatch(
        self,
        saas_example_connection_config,
        saas_example_dataset,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
    ):
        path = V1_URL_PREFIX + CONNECTION_DATASETS
        path_params = {"connection_key": saas_example_connection_config.key}
        datasets_url = path.format(**path_params)

        invalid_dataset = saas_example_dataset
        invalid_dataset["fides_key"] = "different_key"

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.patch(
            datasets_url, headers=auth_header, json=[invalid_dataset]
        )
        assert response.status_code == 200

        response_body = json.loads(response.text)
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1
        assert (
            response_body["failed"][0]["message"]
            == "The fides_key 'different_key' of the dataset does not match the fides_key "
            "'saas_connector_example' of the connection config"
        )

    @mock.patch("fides.api.models.datasetconfig.DatasetConfig.upsert_with_ctl_dataset")
    def test_patch_datasets_failed_response(
        self,
        mock_create: Mock,
        example_datasets: List,
        datasets_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        mock_create.side_effect = HTTPException(mock.Mock(status=400), "Test error")
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.patch(
            datasets_url, headers=auth_header, json=example_datasets
        )
        assert response.status_code == 200  # Returns 200 regardless
        response_body = json.loads(response.text)
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 16

        for failed_response in response_body["failed"]:
            assert "Dataset create/update failed" in failed_response["message"]
            assert set(failed_response.keys()) == {"message", "data"}

        for index, failed in enumerate(response_body["failed"]):
            assert failed["data"]["fides_key"] == example_datasets[index]["fides_key"]


class TestPutYamlDatasets:
    @pytest.fixture
    def dataset_url(self, connection_config) -> str:
        path = V1_URL_PREFIX + YAML_DATASETS
        path_params = {"connection_key": connection_config.key}
        return path.format(**path_params)

    def test_patch_dataset_not_authenticated(
        self, example_yaml_dataset: str, dataset_url, api_client
    ) -> None:
        response = api_client.patch(dataset_url, headers={}, data=example_yaml_dataset)
        assert response.status_code == 401

    def test_patch_datasets_wrong_scope(
        self,
        example_yaml_dataset: str,
        dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.patch(
            dataset_url, headers=auth_header, data=example_yaml_dataset
        )
        assert response.status_code == 403

    def test_patch_dataset_invalid_connection_key(
        self, example_yaml_dataset: str, api_client: TestClient, generate_auth_header
    ) -> None:
        path = V1_URL_PREFIX + YAML_DATASETS
        path_params = {"connection_key": "nonexistent_key"}
        dataset_url = path.format(**path_params)

        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.patch(
            dataset_url, headers=auth_header, data=example_yaml_dataset
        )
        assert response.status_code == 404

    def test_patch_dataset_invalid_content_type(
        self,
        dataset_url: str,
        example_datasets: str,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.patch(
            dataset_url, headers=auth_header, json=example_datasets
        )
        assert response.status_code == 415

    def test_patch_dataset_invalid_content(
        self,
        dataset_url: str,
        example_invalid_yaml_dataset: str,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        headers = {"Content-type": "application/x-yaml"}
        headers.update(auth_header)
        response = api_client.patch(
            dataset_url, headers=headers, data=example_invalid_yaml_dataset
        )
        assert response.status_code == 400

    @mock.patch("fides.api.models.datasetconfig.DatasetConfig.upsert_with_ctl_dataset")
    def test_patch_datasets_failed_response(
        self,
        mock_create: Mock,
        example_yaml_dataset: str,
        dataset_url,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        mock_create.side_effect = HTTPException(mock.Mock(status=400), "Test error")
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        headers = {"Content-type": "application/x-yaml"}
        headers.update(auth_header)
        response = api_client.patch(
            dataset_url, headers=headers, data=example_yaml_dataset
        )
        assert response.status_code == 200  # Returns 200 regardless
        response_body = json.loads(response.text)
        assert len(response_body["succeeded"]) == 0
        assert len(response_body["failed"]) == 1

        for failed_response in response_body["failed"]:
            assert "Dataset create/update failed" in failed_response["message"]
            assert set(failed_response.keys()) == {"message", "data"}

    def test_patch_dataset_create(
        self,
        example_yaml_dataset: List,
        dataset_url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        headers = {"Content-type": "application/x-yaml"}
        headers.update(auth_header)
        response = api_client.patch(
            dataset_url, headers=headers, data=example_yaml_dataset
        )

        assert response.status_code == 200
        response_body = json.loads(response.text)
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

        postgres_config.delete(db)

    def test_patch_datasets_create(
        self,
        example_yaml_datasets: List,
        dataset_url,
        api_client: TestClient,
        db: Session,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        headers = {"Content-type": "application/x-yaml"}
        headers.update(auth_header)
        response = api_client.patch(
            dataset_url, headers=headers, data=example_yaml_datasets
        )

        assert response.status_code == 200
        response_body = json.loads(response.text)
        assert len(response_body["succeeded"]) == 2
        assert len(response_body["failed"]) == 0


class TestGetConnectionDatasets:
    @pytest.fixture
    def datasets_url(self, connection_config) -> str:
        path = V1_URL_PREFIX + CONNECTION_DATASETS
        path_params = {"connection_key": connection_config.key}
        return path.format(**path_params)

    def test_get_datasets_not_authenticated(
        self, dataset_config, datasets_url, api_client: TestClient, generate_auth_header
    ) -> None:
        response = api_client.get(datasets_url, headers={})
        assert response.status_code == 401

    def test_get_datasets_invalid_connection_key(
        self, dataset_config, datasets_url, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        path = V1_URL_PREFIX + CONNECTION_DATASETS
        path_params = {"connection_key": "nonexistent_key"}
        datasets_url = path.format(**path_params)

        response = api_client.get(datasets_url, headers=auth_header)
        assert response.status_code == 404

    def test_get_datasets(
        self, dataset_config, datasets_url, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(datasets_url, headers=auth_header)
        assert response.status_code == 200

        response_body = json.loads(response.text)
        assert len(response_body["items"]) == 1
        dataset_response = response_body["items"][0]
        assert dataset_response["fides_key"] == "postgres_example_subscriptions_dataset"
        assert len(dataset_response["collections"]) == 1

        assert response_body["total"] == 1
        assert response_body["page"] == 1
        assert response_body["size"] == Params().size


class TestGetDatasetConfigs:
    @pytest.fixture
    def datasets_url(self, connection_config) -> str:
        path = V1_URL_PREFIX + DATASET_CONFIGS
        path_params = {"connection_key": connection_config.key}
        return path.format(**path_params)

    def test_get_dataset_configs_not_authenticated(
        self, datasets_url, api_client: TestClient
    ) -> None:
        response = api_client.get(datasets_url, headers={})
        assert response.status_code == 401

    def test_get_dataset_configs_invalid_connection_key(
        self, datasets_url, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        path = V1_URL_PREFIX + DATASET_CONFIGS
        path_params = {"connection_key": "nonexistent_key"}
        datasets_url = path.format(**path_params)

        response = api_client.get(datasets_url, headers=auth_header)
        assert response.status_code == 404

    def test_get_dataset_configs(
        self, dataset_config, datasets_url, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(datasets_url, headers=auth_header)
        assert response.status_code == 200

        response_body = json.loads(response.text)
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


def get_connection_dataset_url(
    connection_config: Optional[ConnectionConfig] = None,
    dataset_config: Optional[DatasetConfig] = None,
) -> str:
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


@pytest.mark.asyncio
class TestGetCtlDatasetFilter:
    @pytest.fixture
    def url(self) -> str:
        return V1_URL_PREFIX + "/filter" + DATASETS

    def test_get_dataset_not_authenticated(self, url, api_client) -> None:
        response = api_client.get(url, headers={})
        assert response.status_code == 401

    def test_get_dataset_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header(scopes=[CTL_DATASET_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 403

    def test_get_only_unlinked_datasets(
        self, generate_auth_header, api_client, url, unlinked_dataset, linked_dataset
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        unlinked_url = f"{url}?only_unlinked_datasets=True"
        response = api_client.get(unlinked_url, headers=auth_header)
        print(unlinked_url)
        assert response.status_code == 200
        print([dataset["fides_key"] for dataset in response.json()])
        assert len(response.json()) == 1
        assert response.json()[0]["fides_key"] == unlinked_dataset.fides_key

        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        assert len(response.json()) == 2


    def test_saas_dataset_filter(
        self,
        generate_auth_header,
        api_client,
        url,
        secondary_hubspot_instance,
        linked_dataset,
        unlinked_dataset,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        saas_fides_key = secondary_hubspot_instance[1].fides_key
        # Should filter out saas datasets by default
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert saas_fides_key not in [d["fides_key"] for d in response.json()]

        # Should filter out saas datasets if remove_saas_datasets is True
        response = api_client.get(
            f"{url}?remove_saas_datasets=True", headers=auth_header
        )
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert saas_fides_key not in [d["fides_key"] for d in response.json()]

        # Should include saas datasets if remove_saas_datasets is False
        response = api_client.get(
            f"{url}?remove_saas_datasets=False", headers=auth_header
        )
        assert response.status_code == 200
        assert len(response.json()) == 3
        assert saas_fides_key in [d["fides_key"] for d in response.json()]


    def test_unlinked_and_no_saas_datasets(
        self,
        generate_auth_header,
        api_client,
        url,
        unlinked_dataset,
        secondary_hubspot_instance,
        linked_dataset,
    ) -> None:
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(
            f"{url}?only_unlinked_datasets=True", headers=auth_header
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["fides_key"] == unlinked_dataset.fides_key

        # It should still return one with saas datasets being included because they're linked
        response = api_client.get(
            f"{url}?only_unlinked_datasets=True&remove_saas_datasets=False",
            headers=auth_header,
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["fides_key"] == unlinked_dataset.fides_key


class TestGetConnectionDataset:
    def test_get_dataset_not_authenticated(
        self, dataset_config, connection_config, api_client
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        response = api_client.get(dataset_url, headers={})
        assert response.status_code == 401

    def test_get_dataset_wrong_scope(
        self,
        dataset_config,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.get(dataset_url, headers=auth_header)
        assert response.status_code == 403

    def test_get_dataset_does_not_exist(
        self,
        dataset_config,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, None)
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(dataset_url, headers=auth_header)
        assert response.status_code == 404

    def test_get_dataset_invalid_connection_key(
        self,
        dataset_config,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(None, dataset_config)
        dataset_url.replace(connection_config.key, "nonexistent_key")
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(dataset_url, headers=auth_header)
        assert response.status_code == 404

    def test_get_dataset(
        self,
        dataset_config,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ):
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(dataset_url, headers=auth_header)
        assert response.status_code == 200

        response_body = json.loads(response.text)
        assert response_body["fides_key"] == dataset_config.fides_key
        assert len(response_body["collections"]) == 1


def get_dataset_config_url(
    connection_config: Optional[ConnectionConfig] = None,
    dataset_config: Optional[DatasetConfig] = None,
) -> str:
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
    ) -> None:
        dataset_url = get_dataset_config_url(connection_config, dataset_config)
        response = api_client.get(dataset_url, headers={})
        assert response.status_code == 401

    def test_get_dataset_config_wrong_scope(
        self,
        dataset_config,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_dataset_config_url(connection_config, dataset_config)
        auth_header = generate_auth_header(scopes=[DATASET_CREATE_OR_UPDATE])
        response = api_client.get(dataset_url, headers=auth_header)
        assert response.status_code == 403

    def test_get_dataset_config_does_not_exist(
        self,
        dataset_config,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_dataset_config_url(connection_config, None)
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(dataset_url, headers=auth_header)
        assert response.status_code == 404

    def test_get_dataset_config_invalid_connection_key(
        self,
        dataset_config,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_dataset_config_url(None, dataset_config)
        dataset_url.replace(connection_config.key, "nonexistent_key")
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(dataset_url, headers=auth_header)
        assert response.status_code == 404

    def test_get_dataset_config(
        self,
        dataset_config,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ):
        dataset_url = get_dataset_config_url(connection_config, dataset_config)
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(dataset_url, headers=auth_header)
        assert response.status_code == 200

        response_body = json.loads(response.text)
        assert response_body["fides_key"] == dataset_config.fides_key
        assert (
            response_body["ctl_dataset"]["fides_key"]
            == dataset_config.ctl_dataset.fides_key
        )
        assert len(response_body["ctl_dataset"]["collections"]) == 1


class TestDeleteDataset:
    def test_delete_dataset_not_authenticated(
        self, dataset_config, connection_config, api_client
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        response = api_client.delete(dataset_url, headers={})
        assert response.status_code == 401

    def test_delete_dataset_wrong_scope(
        self,
        dataset_config,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.delete(dataset_url, headers=auth_header)
        assert response.status_code == 403

    def test_delete_dataset_does_not_exist(
        self,
        dataset_config,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(connection_config, None)
        auth_header = generate_auth_header(scopes=[DATASET_DELETE])
        response = api_client.delete(dataset_url, headers=auth_header)
        assert response.status_code == 404

    def test_delete_dataset_invalid_connection_key(
        self,
        dataset_config,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        dataset_url = get_connection_dataset_url(None, dataset_config)
        auth_header = generate_auth_header(scopes=[DATASET_DELETE])
        response = api_client.delete(dataset_url, headers=auth_header)
        assert response.status_code == 404

    def test_delete_dataset(
        self,
        db: Session,
        connection_config,
        api_client: TestClient,
        generate_auth_header,
        ctl_dataset,
    ) -> None:
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

        dataset_url = get_connection_dataset_url(connection_config, dataset_config)
        auth_header = generate_auth_header(scopes=[DATASET_DELETE])
        response = api_client.delete(dataset_url, headers=auth_header)
        assert response.status_code == 204

        assert (
            DatasetConfig.get_by(
                db=db, field="fides_key", value=dataset_config.fides_key
            )
            is None
        )


class TestListDataset:
    @pytest.fixture
    def dataset_with_categories(self, db: Session) -> Generator[CtlDataset, None, None]:
        dataset = CtlDataset.create_from_dataset_dict(
            db,
            {
                "fides_key": f"dataset_key-f{uuid4()}",
                "data_categories": ["user.contact.email", "user.contact.phone_number"],
                "collections": [
                    {
                        "name": "customer",
                        "fields": [
                            {
                                "name": "email",
                                "data_categories": ["user.contact.email"],
                            },
                            {"name": "first_name"},
                        ],
                    }
                ],
            },
        )
        yield dataset
        db.delete(dataset)


    def test_list_dataset_no_pagination(
        self,
        api_client: TestClient,
        generate_auth_header,
        ctl_dataset,
        secondary_hubspot_instance,
    ):
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(f"{V1_URL_PREFIX}/dataset", headers=auth_header)

        assert response.status_code == 200

        response_json = response.json()
        assert len(response_json) == 2

        sorted_items = sorted(response_json, key=lambda x: x["fides_key"])
        assert sorted_items[0]["fides_key"] == ctl_dataset.fides_key
        assert sorted_items[1]["fides_key"] == secondary_hubspot_instance[1].fides_key


    def test_list_dataset_no_pagination_exclude_saas(
        self,
        api_client: TestClient,
        generate_auth_header,
        ctl_dataset,
        secondary_hubspot_instance,
    ):
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(
            f"{V1_URL_PREFIX}/dataset?exclude_saas_datasets=True",
            headers=auth_header,
        )

        assert response.status_code == 200
        response_json = response.json()
        assert len(response_json) == 1
        assert response_json[0]["fides_key"] == ctl_dataset.fides_key


    def test_list_dataset_no_pagination_only_unlinked_datasets(
        self,
        api_client: TestClient,
        generate_auth_header,
        unlinked_dataset,
        linked_dataset,
    ):
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(
            f"{V1_URL_PREFIX}/dataset?only_unlinked_datasets=True",
            headers=auth_header,
        )

        assert response.status_code == 200
        response_json = response.json()
        assert len(response_json) == 1
        assert response_json[0]["fides_key"] == unlinked_dataset.fides_key


    def test_list_dataset_with_pagination(
        self,
        api_client: TestClient,
        generate_auth_header,
        ctl_dataset,
        secondary_hubspot_instance,
    ):
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(
            f"{V1_URL_PREFIX}/dataset?page=1&size=5", headers=auth_header
        )

        assert response.status_code == 200
        response_json = response.json()

        assert response_json["total"] == 2
        sorted_items = sorted(response_json["items"], key=lambda x: x["fides_key"])

        assert len(sorted_items) == 2
        assert sorted_items[0]["fides_key"] == ctl_dataset.fides_key
        assert sorted_items[1]["fides_key"] == secondary_hubspot_instance[1].fides_key


    def test_list_dataset_with_pagination_exclude_saas(
        self,
        api_client: TestClient,
        generate_auth_header,
        ctl_dataset,
        secondary_hubspot_instance,
    ):
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(
            f"{V1_URL_PREFIX}/dataset?page=1&size=5&exclude_saas_datasets=True",
            headers=auth_header,
        )

        assert response.status_code == 200
        response_json = response.json()

        assert response_json["total"] == 1
        assert response_json["items"][0]["fides_key"] == ctl_dataset.fides_key

    def test_list_dataset_with_pagination_only_unlinked_datasets(
        self,
        api_client: TestClient,
        generate_auth_header,
        unlinked_dataset,
        linked_dataset,
    ):
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(
            f"{V1_URL_PREFIX}/dataset?page=1&size=5&only_unlinked_datasets=True",
            headers=auth_header,
        )

        assert response.status_code == 200
        response_json = response.json()

        assert response_json["total"] == 1
        assert response_json["items"][0]["fides_key"] == unlinked_dataset.fides_key

    def test_list_dataset_with_pagination_default_page(
        self,
        api_client: TestClient,
        generate_auth_header,
        ctl_dataset,
        saas_ctl_dataset,
    ):
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        # We don't pass in the page but we pass in the size,
        # so we should get a paginated response with the default page number (1)
        response = api_client.get(
            f"{V1_URL_PREFIX}/dataset?size=5", headers=auth_header
        )

        assert response.status_code == 200
        response_json = response.json()

        assert response_json["total"] == 2
        assert response_json["page"] == 1

        sorted_items = sorted(response_json["items"], key=lambda x: x["fides_key"])
        assert len(sorted_items) == 2
        assert sorted_items[0]["fides_key"] == ctl_dataset.fides_key
        assert sorted_items[1]["fides_key"] == saas_ctl_dataset.fides_key

    def test_list_dataset_with_pagination_default_size(
        self,
        api_client: TestClient,
        generate_auth_header,
        ctl_dataset,
        saas_ctl_dataset,
    ):
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        # We don't pass in the size but we pass in the page,
        # so we should get a paginated response with the default size (50)
        response = api_client.get(
            f"{V1_URL_PREFIX}/dataset?page=1", headers=auth_header
        )

        assert response.status_code == 200
        response_json = response.json()

        assert response_json["total"] == 2
        assert response_json["page"] == 1
        assert response_json["size"] == 50

        sorted_items = sorted(response_json["items"], key=lambda x: x["fides_key"])
        assert len(sorted_items) == 2
        assert sorted_items[0]["fides_key"] == ctl_dataset.fides_key
        assert sorted_items[1]["fides_key"] == saas_ctl_dataset.fides_key

    def test_list_dataset_with_pagination_and_filters(
        self,
        api_client: TestClient,
        generate_auth_header,
        ctl_dataset,
        saas_ctl_dataset,
        dataset_with_categories,
    ):
        auth_header = generate_auth_header(scopes=[DATASET_READ])
        response = api_client.get(
            f"{V1_URL_PREFIX}/dataset?page=1&size=1&data_categories=user.contact.email",
            headers=auth_header,
        )

        assert response.status_code == 200
        response_json = response.json()

        assert response_json["total"] == 1
        assert len(response_json["items"]) == 1
        assert (
            response_json["items"][0]["fides_key"] == dataset_with_categories.fides_key
        )
