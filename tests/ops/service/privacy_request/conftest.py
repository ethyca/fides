from typing import Dict, Generator, List

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.service.connectors import BigQueryConnector
from tests.fixtures.application_fixtures import load_dataset
from tests.fixtures.bigquery_fixtures import _cleanup_test_tables, _create_test_tables
from tests.ops.graph.conftest import create_dataset_config_fixture

optional_identities_dataset_config = create_dataset_config_fixture(
    "optional_identities.yml"
)


def create_modified_bigquery_dataset(
    target_table: str, reference_dataset_key: str = None
) -> Dict:
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

    # Always use the modified dataset key for self-contained references
    reference_key = modified_dataset["fides_key"]

    # Copy all collections, but rename the target table to target_table_missing
    # and update any references to maintain dataset integrity
    for collection in original_dataset.get("collections", []):
        collection_copy = copy.deepcopy(collection)

        if collection["name"] == target_table:
            # Rename the target collection
            collection_copy["name"] = missing_suffix

        # Update any references in ALL collections to use the new dataset key
        # and correct collection names
        if "fields" in collection_copy:
            _update_field_references(
                collection_copy["fields"],
                target_table,
                missing_suffix,
                reference_key,
            )

        # Update erase_after references in fides_meta
        if (
            "fides_meta" in collection_copy
            and "erase_after" in collection_copy["fides_meta"]
        ):
            print(
                f"DEBUG: Processing erase_after for collection {collection_copy['name']}: {collection_copy['fides_meta']['erase_after']}"
            )
            updated_erase_after = []
            for ref in collection_copy["fides_meta"]["erase_after"]:
                # Update dataset reference if it points to the original dataset
                if ref.startswith("bigquery_example_test_dataset."):
                    # Replace the dataset name with the reference key
                    updated_ref = ref.replace(
                        "bigquery_example_test_dataset", reference_key
                    )
                    # If this reference is to the target table, update the collection name
                    if ref.endswith(f".{target_table}"):
                        updated_ref = updated_ref.replace(
                            f".{target_table}", f".{missing_suffix}"
                        )
                    print(
                        f"DEBUG: Updated erase_after reference from {ref} to {updated_ref}"
                    )
                    updated_erase_after.append(updated_ref)
                else:
                    print(f"DEBUG: Keeping erase_after reference as is: {ref}")
                    updated_erase_after.append(ref)
            collection_copy["fides_meta"]["erase_after"] = updated_erase_after
            print(
                f"DEBUG: Final erase_after for collection {collection_copy['name']}: {collection_copy['fides_meta']['erase_after']}"
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
            print(
                f"DEBUG: Processing field {field.get('name', 'unnamed')} with references: {field['fides_meta']['references']}"
            )
            for ref in field["fides_meta"]["references"]:
                print(f"DEBUG: Processing reference: {ref}")
                # First, update the dataset reference if it points to the original dataset
                if ref.get("dataset") == "bigquery_example_test_dataset":
                    print(
                        f"DEBUG: Updating field reference from {ref['field']} to use dataset {dataset_key}"
                    )
                    ref["dataset"] = dataset_key

                    # Update field references to use the correct collection names
                    if "field" in ref and "." in ref["field"]:
                        field_parts = ref["field"].split(".")
                        if len(field_parts) == 2:
                            collection_name, field_name = field_parts
                            # If this is the target table that was renamed, use the missing suffix
                            if collection_name == target_table:
                                new_field = f"{missing_suffix}.{field_name}"
                                print(
                                    f"DEBUG: Updating field reference from {ref['field']} to {new_field}"
                                )
                                ref["field"] = new_field
                            else:
                                # For other collections, keep the original field reference
                                # The collection name should remain the same in the target dataset
                                print(
                                    f"DEBUG: Keeping field reference {ref['field']} but updating dataset to {dataset_key}"
                                )
                else:
                    print(
                        f"DEBUG: Reference dataset is not bigquery_example_test_dataset: {ref.get('dataset')}"
                    )

                # Handle the case where the field reference starts with the target table name
                if ref.get("field", "").startswith(f"{target_table}."):
                    ref["field"] = ref["field"].replace(
                        f"{target_table}.", f"{missing_suffix}."
                    )

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
    bigquery_example_test_dataset_config: DatasetConfig,
    db: Session,
) -> Generator[DatasetConfig, None, None]:
    """Dataset configuration with customer renamed to customer_missing (collection with dependencies)."""
    # Get the reference dataset key from the example dataset config
    reference_dataset_key = bigquery_example_test_dataset_config.fides_key
    dataset_data = create_modified_bigquery_dataset("customer", reference_dataset_key)
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
def bigquery_missing_table_resources(
    bigquery_connection_config: ConnectionConfig,
    db: Session,
):
    """Create BigQuery resources with tables that have _missing suffix for missing table tests."""
    # Increment the ids by a random number to avoid conflicts on concurrent test runs
    import random
    from uuid import uuid4

    random_increment = random.randint(1, 99999)
    connector = BigQueryConnector(bigquery_connection_config)
    bigquery_client = connector.client()

    # Get the dataset name from the connection config
    dataset_name = bigquery_connection_config.secrets.get("dataset", "fidesopstest")

    # Create table names - create tables with original names
    # The missing table scenario is created by the dataset configuration referencing _missing tables
    table_names = {
        "customer": "customer",  # Create customer table, but dataset config will look for customer_missing
        "customer_profile": "customer_profile",  # Create customer_profile table, but dataset config will look for customer_profile_missing
        "address": "address",
        "employee": "employee",
        "visit_partitioned": "visit_partitioned",
    }

    with bigquery_client.connect() as connection:
        # Create unique tables for this test
        _create_test_tables(connection, dataset_name, table_names)

        # For missing table tests, we need to selectively NOT create the table that should be missing
        # The test will determine which table should be missing based on the scenario

        uuid = str(uuid4())
        customer_email = f"customer-{uuid}@example.com"
        customer_name = f"{uuid}"

        # Use unique IDs instead of querying existing tables
        customer_id = random_increment + 1
        address_id = random_increment + 1

        city = "Test City"
        state = "TX"
        stmt = f"""
        insert into {dataset_name}.{table_names['address']} (id, house, street, city, state, zip)
        values ({address_id}, '{111}', 'Test Street', '{city}', '{state}', '55555');
        """
        connection.execute(stmt)

        stmt = f"""
            insert into {dataset_name}.{table_names['customer']} (id, email, name, address_id, `custom id`, extra_address_data, tags, purchase_history, created)
            values ({customer_id}, '{customer_email}', '{customer_name}', {address_id}, 'custom_{customer_id}', STRUCT('{city}' as city, '111' as house, {customer_id} as id, '{state}' as state, 'Test Street' as street, {address_id} as address_id), ['VIP', 'Rewards', 'Premium'], [STRUCT('ITEM-1' as item_id, 29.99 as price, '2023-01-15' as purchase_date, ['electronics', 'gadgets'] as item_tags), STRUCT('ITEM-2' as item_id, 49.99 as price, '2023-02-20' as purchase_date, ['clothing', 'accessories'] as item_tags)], CURRENT_TIMESTAMP);
        """

        connection.execute(stmt)

        # Insert into customer_profile table
        stmt = f"""
            insert into {dataset_name}.{table_names['customer_profile']} (id, contact_info, address)
            values ({customer_id}, STRUCT('{customer_email}', '555-{customer_id}-1234'), '{111} Test Street, {city}, {state} 55555');
        """
        connection.execute(stmt)

        last_visit_date = "2024-10-03 01:00:00"
        stmt = f"""
            insert into {dataset_name}.{table_names['visit_partitioned']} (email, last_visit)
            values ('{customer_email}', '{last_visit_date}');
        """

        connection.execute(stmt)

        # Use unique employee ID instead of querying existing table
        employee_id = customer_id
        employee_email = f"employee-{uuid}@example.com"
        employee_name = f"Jane {uuid}"

        stmt = f"""
           insert into {dataset_name}.{table_names['employee']} (id, email, name, address_id)
           values ({employee_id}, '{employee_email}', '{employee_name}', {address_id});
        """
        connection.execute(stmt)

        yield {
            "email": customer_email,
            "name": customer_name,
            "id": customer_id,
            "client": bigquery_client,
            "address_id": address_id,
            "city": city,
            "state": state,
            "connector": connector,
            "employee_id": employee_id,
            "employee_email": employee_email,
            "table_names": table_names,  # Include table names for tests
        }

        # Clean up the unique tables
        _cleanup_test_tables(connection, dataset_name, table_names)
