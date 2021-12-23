"""Module that generates valid dataset manifest files from various data sources."""
from typing import Dict, List, Tuple

import sqlalchemy
from sqlalchemy.engine import Engine
from pydantic import AnyHttpUrl

from fidesctl.core.api_helpers import get_server_resource
from fideslang import manifests
from fideslang.models import Dataset, DatasetCollection, DatasetField
from .utils import get_db_engine, echo_green, echo_red


def get_postgres_collections_and_fields(
    engine: Engine,
) -> Dict[str, Dict[str, List[str]]]:
    """
    Postgres-specific implementation that to ingest all of the
    schemas and tables from a database.

    Returns a mapping of schemas to its tables and all of the table's fields.
    """
    inspector = sqlalchemy.inspect(engine)
    schema_exclusion_list = ["information_schema"]

    db_tables: Dict[str, Dict[str, List]] = {}
    for schema in inspector.get_schema_names():
        if schema not in schema_exclusion_list:
            db_tables[schema] = {}
            for table in inspector.get_table_names(schema=schema):
                db_tables[schema][f"{schema}.{table}"] = [
                    column["name"]
                    for column in inspector.get_columns(table, schema=schema)
                ]
    return db_tables


def get_mysql_collections_and_fields(engine: Engine) -> Dict[str, Dict[str, List[str]]]:
    """
    Postgres-specific implementation that to ingest all of the
    schemas and tables from a database.

    Returns a mapping of schemas to its tables and all of the table's fields.

    Because MySQL doesn't have schemas this is filled in by the database name.
    """
    inspector = sqlalchemy.inspect(engine)
    schema_exclusion_list = ["mysql", "performance_schema", "sys", "information_schema"]

    db_tables: Dict[str, Dict[str, List]] = {}
    for schema in inspector.get_schema_names():
        if schema not in schema_exclusion_list:
            db_tables[schema] = {}
            for table in inspector.get_table_names(schema=schema):
                db_tables[schema][table] = [
                    column["name"]
                    for column in inspector.get_columns(table, schema=schema)
                ]
    return db_tables


def get_mssql_collections_and_fields(engine: Engine) -> Dict[str, Dict[str, List[str]]]:
    """
    SQL Server-specific implementation that to ingest all of the
    schemas and tables from a database.

    Returns a mapping of schemas to its tables and all of the table's fields.

    Because SQL Server doesn't have schemas this is filled in by the database name.
    """
    inspector = sqlalchemy.inspect(engine)
    schema_exclusion_list = ["INFORMATION_SCHEMA", "guest", "sys"]
    exclude_prefix = "db_"

    db_tables: Dict[str, Dict[str, List]] = {}
    for schema in inspector.get_schema_names():
        if schema not in schema_exclusion_list and schema[:3] != exclude_prefix:
            db_tables[schema] = {}
            for table in inspector.get_table_names(schema=schema):
                db_tables[schema][table] = [
                    column["name"]
                    for column in inspector.get_columns(table, schema=schema)
                ]
    return db_tables


def create_dataset_collections(
    db_tables: Dict[str, Dict[str, List[str]]]
) -> List[Dataset]:
    """
    Return an object of tables and columns formatted for a Fides manifest
    with placeholder values where needed.
    """

    table_manifests = [
        Dataset(
            fides_key=schema_name,
            name=schema_name,
            description=f"Fides Generated Description for Schema: {schema_name}",
            data_categories=[],
            collections=[
                DatasetCollection(
                    name=table_name,
                    description=f"Fides Generated Description for Table: {table_name}",
                    data_categories=[],
                    fields=[
                        DatasetField(
                            name=column,
                            description=f"Fides Generated Description for Column: {column}",
                            data_categories=[],
                        )
                        for column in table
                    ],
                )
                for table_name, table in schema.items()
            ],
        )
        for schema_name, schema in db_tables.items()
    ]
    return table_manifests


def find_uncategorized_dataset_fields(
    dataset: Dataset, db_collections: Dict[str, Dict[str, List[str]]]
) -> Tuple[List[str], float]:
    """
    Given an object that represents a database definition, finds uncategorized
    keys and coverage ratio.
    """
    missing_keys = []
    total_field_count = 0
    db_dataset = db_collections.get(dataset.name)
    if not db_dataset:
        echo_red(
            f"Dataset ({dataset.name}) could not be found in database. Found datasets ({db_collections.keys()})"
        )
        raise SystemExit(1)

    for db_dataset_collection in db_dataset.keys():
        dataset_collection = next(
            (
                colection
                for colection in dataset.collections
                if colection.name == db_dataset_collection
            ),
            None,
        )

        for db_dataset_field in db_dataset.get(db_dataset_collection, []):
            total_field_count += 1
            field_found = (
                any(
                    field.name == db_dataset_field and field.data_categories
                    for field in dataset_collection.fields
                )
                if dataset_collection
                else False
            )

            if not field_found:
                missing_keys.append(
                    f"{dataset.name}.{db_dataset_collection}.{db_dataset_field}"
                )

    coverage_rate = (
        (total_field_count - len(missing_keys)) / total_field_count
        if total_field_count > 0
        else 1
    )
    return missing_keys, coverage_rate


def database_coverage(
    connection_string: str,
    dataset_key: str,
    coverage_threshold: float,
    url: AnyHttpUrl,
    headers: Dict[str, str],
) -> None:
    """
    Given a database connection string, fetches collections
    and fields and compares them to an existing dataset with a
    provided key

    Prints uncategorized fields and raises exception if coverage
    is lower than provided threshold.
    """
    db_engine = get_db_engine(connection_string)
    db_collections = get_db_collections_and_fields(db_engine)

    dataset = get_server_resource(
        url=url, resource_type="dataset", resource_key=dataset_key, headers=headers
    )
    if not dataset:
        echo_red(f"Dataset ({dataset_key}) does not exist in existing taxonomy")
        raise SystemExit(1)

    uncategorized_keys, coverage_rate = find_uncategorized_dataset_fields(
        dataset=dataset, db_collections=db_collections
    )
    output = f"`{dataset_key}` annotation coverage: {int(coverage_rate * 100)}% \n"
    if uncategorized_keys:
        output += "The following fields do not have any data category annotations: \n"
        output += "\n".join(uncategorized_keys)

    if coverage_rate < coverage_threshold:
        echo_red(output)
        raise SystemExit(1)
    echo_green(output)


def generate_dataset(connection_string: str, file_name: str) -> str:
    """
    Given a database connection string, extract all tables/fields from it
    and write out a boilerplate dataset manifest.
    """
    database_ingestion_functions = {
        "postgresql": get_postgres_collections_and_fields,
        "mysql": get_mysql_collections_and_fields,
        "mssql": get_mssql_collections_and_fields,
    }

    db_engine = get_db_engine(connection_string)
    db_collections = database_ingestion_functions[db_engine.dialect.name](db_engine)
    collections = create_dataset_collections(db_collections)
    manifests.write_manifest(file_name, [i.dict() for i in collections], "dataset")
    echo_green(f"Generated dataset manifest written to {file_name}")
    return file_name
