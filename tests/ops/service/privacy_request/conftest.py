from typing import Dict, Generator, List

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from tests.fixtures.application_fixtures import load_dataset
from tests.ops.graph.conftest import create_dataset_config_fixture

optional_identities_dataset_config = create_dataset_config_fixture(
    "optional_identities.yml"
)


def create_modified_bigquery_dataset(target_table: str) -> Dict:
    """
    Create a modified BigQuery dataset configuration with the specified table renamed
    to {table}_missing to simulate a missing table scenario.
    """
    import copy

    # Load the original BigQuery dataset
    original_datasets = load_dataset("data/dataset/bigquery_example_test_dataset.yml")
    original_dataset = copy.deepcopy(
        original_datasets[0]
    )  # BigQuery dataset is the first in the file

    # Modify the dataset key and metadata
    missing_suffix = f"{target_table}_missing"
    modified_dataset = {
        "fides_key": f"bigquery_missing_{target_table}_dataset",
        "name": f"BigQuery Missing {target_table.title()} Dataset",
        "description": f"Modified BigQuery dataset for testing missing table handling - {target_table} collection renamed to {missing_suffix}.",
        "collections": [],
    }

    # Copy all collections, but rename the target table to target_table_missing
    # and update any references to maintain dataset integrity
    for collection in original_dataset.get("collections", []):
        collection_copy = copy.deepcopy(collection)

        if collection["name"] == target_table:
            # Rename the target collection
            collection_copy["name"] = missing_suffix
        else:
            # Update any references to the renamed table in other collections
            if "fields" in collection_copy:
                _update_field_references(
                    collection_copy["fields"],
                    target_table,
                    missing_suffix,
                    modified_dataset["fides_key"],
                )

        modified_dataset["collections"].append(collection_copy)

    return modified_dataset


def _update_field_references(
    fields: List[Dict], target_table: str, missing_suffix: str, dataset_key: str
):
    """Recursively update field references to renamed tables."""
    for field in fields:
        # Update direct references
        if "fides_meta" in field and "references" in field["fides_meta"]:
            for ref in field["fides_meta"]["references"]:
                if ref.get("field", "").startswith(f"{target_table}."):
                    ref["field"] = ref["field"].replace(
                        f"{target_table}.", f"{missing_suffix}."
                    )
                if ref.get("dataset") == "bigquery_example_test_dataset":
                    ref["dataset"] = dataset_key

        # Handle nested fields (like in structs/objects)
        if "fields" in field:
            _update_field_references(
                field["fields"], target_table, missing_suffix, dataset_key
            )


@pytest.fixture(scope="function")
def bigquery_missing_customer_profile_config(
    bigquery_connection_config: ConnectionConfig,
    db: Session,
) -> Generator[DatasetConfig, None, None]:
    """Dataset configuration with customer_profile renamed to customer_profile_missing (leaf collection)."""
    dataset_data = create_modified_bigquery_dataset("customer_profile")
    fides_key = dataset_data["fides_key"]

    # Create new connection config with same secrets but different key
    new_connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": fides_key,
            "key": fides_key,
            "connection_type": bigquery_connection_config.connection_type,
            "access": bigquery_connection_config.access,
        },
    )
    new_connection_config.secrets = bigquery_connection_config.secrets
    new_connection_config.save(db=db)

    # Create CTL dataset
    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_data)

    # Create dataset config
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": new_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )

    yield dataset_config
    dataset_config.delete(db=db)
    ctl_dataset.delete(db=db)
    new_connection_config.delete(db=db)


@pytest.fixture(scope="function")
def bigquery_missing_customer_config(
    bigquery_connection_config: ConnectionConfig,
    db: Session,
) -> Generator[DatasetConfig, None, None]:
    """Dataset configuration with customer renamed to customer_missing (collection with dependencies)."""
    dataset_data = create_modified_bigquery_dataset("customer")
    fides_key = dataset_data["fides_key"]

    # Create new connection config with same secrets but different key
    new_connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": fides_key,
            "key": fides_key,
            "connection_type": bigquery_connection_config.connection_type,
            "access": bigquery_connection_config.access,
        },
    )
    new_connection_config.secrets = bigquery_connection_config.secrets
    new_connection_config.save(db=db)

    # Create CTL dataset
    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_data)

    # Create dataset config
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": new_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )

    yield dataset_config
    dataset_config.delete(db=db)
    ctl_dataset.delete(db=db)
    new_connection_config.delete(db=db)


@pytest.fixture(scope="function")
def bigquery_missing_table_resources(bigquery_resources):
    """Reuse existing bigquery_resources since test data setup is the same."""
    return bigquery_resources
