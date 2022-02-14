"""Module that adds functionality for generating or scanning datasets."""
from typing import Dict, List, Tuple, Optional

import sqlalchemy
from sqlalchemy.engine import Engine
from pydantic import AnyHttpUrl

from fidesctl.core.api_helpers import get_server_resource
from fidesctl.core.parse import parse
from fideslang import manifests
from fideslang.models import Dataset, DatasetCollection, DatasetField, Taxonomy
from .utils import get_db_engine, echo_green, echo_red

SCHEMA_EXCLUSION = {
    "postgresql": ["information_schema"],
    "mysql": ["mysql", "performance_schema", "sys", "information_schema"],
    "mssql": ["INFORMATION_SCHEMA", "guest", "sys"],
    "snowflake": ["information_schema"],
    "redshift": ["information_schema"],
}


def include_dataset_schema(schema: str, database_type: str) -> bool:
    """
    Returns whether a schema should be included based on database type and schema name
    """
    schema_exclusion_list = SCHEMA_EXCLUSION.get(database_type, [])
    if database_type == "mssql":
        return schema not in schema_exclusion_list and not schema.startswith("db_")
    return schema not in schema_exclusion_list


def get_db_collections_and_fields(
    engine: Engine,
) -> Dict[str, Dict[str, List[str]]]:
    """
    Extract the table and column names from a database given a sqlalchemy engine

    Returns a mapping of schemas to its tables and all of the table's fields.
    """
    inspector = sqlalchemy.inspect(engine)
    db_tables: Dict[str, Dict[str, List]] = {}
    for schema in inspector.get_schema_names():
        if include_dataset_schema(schema=schema, database_type=engine.dialect.name):
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
    dataset_key: str, dataset: Optional[Dataset], db_dataset: Dict[str, List[str]]
) -> Tuple[List[str], int]:
    """
    Given an object that represents a database dataset definition, finds
    uncategorized keys and coverage ratio.
    """
    uncategorized_fields = []
    total_field_count = 0

    for db_dataset_collection in db_dataset.keys():
        dataset_collection = (
            next(
                (
                    collection
                    for collection in dataset.collections
                    if collection.name == db_dataset_collection
                ),
                None,
            )
            if dataset
            else None
        )

        for db_dataset_field in db_dataset.get(db_dataset_collection, []):
            total_field_count += 1
            field_uncategorized = (
                all(
                    field.name != db_dataset_field or not field.data_categories
                    for field in dataset_collection.fields
                )
                if dataset_collection
                else True
            )

            if field_uncategorized:
                uncategorized_fields.append(
                    f"{dataset_key}.{db_dataset_collection}.{db_dataset_field}"
                )
    return uncategorized_fields, total_field_count


def find_all_uncategorized_dataset_fields(
    manifest_taxonomy: Optional[Taxonomy],
    db_collections: Dict[str, Dict[str, List[str]]],
    url: AnyHttpUrl,
    headers: Dict[str, str],
) -> Tuple[List[str], int]:
    """
    Finds all uncategorized fields given a database modeled object. Datasets
    are pulled from the server unless a manifest taxonomy is supplied.
    """
    uncategorized_fields = []
    total_field_count = 0
    for db_dataset_key in db_collections.keys():
        dataset = (
            next(
                (
                    dataset
                    for dataset in manifest_taxonomy.dataset
                    if dataset.fides_key == db_dataset_key
                ),
                None,
            )
            if manifest_taxonomy
            else get_server_resource(
                url=url,
                resource_type="dataset",
                resource_key=db_dataset_key,
                headers=headers,
            )
        )
        db_dataset = db_collections.get(db_dataset_key, {})
        (
            current_uncategorized_keys,
            current_field_count,
        ) = find_uncategorized_dataset_fields(
            dataset_key=db_dataset_key, dataset=dataset, db_dataset=db_dataset
        )
        total_field_count += current_field_count
        uncategorized_fields += current_uncategorized_keys

    return uncategorized_fields, total_field_count


def print_dataset_scan_result(
    datasets: List[str],
    uncategorized_fields: List[str],
    coverage_percent: int,
    coverage_threshold: int,
) -> None:
    """
    Prints uncategorized fields and raises an exception if coverage
    is lower than provided threshold.
    """
    output: str = "Successfully scanned the following datasets:\n"
    output += "\t{}\n".format("\n\t".join(datasets))
    echo_green(output)

    if uncategorized_fields:
        uncategorized_output = (
            "The following fields are missing data category annotations:\n"
        )
        uncategorized_output += "\t{}\n".format("\n\t".join(uncategorized_fields))
        echo_red(uncategorized_output)
    annotation_output = "Annotation coverage: {}%".format(coverage_percent)
    if coverage_percent < coverage_threshold:
        echo_red(annotation_output)
        raise SystemExit(1)
    echo_green(annotation_output)


def scan_dataset(
    connection_string: str,
    manifest_dir: Optional[str],
    coverage_threshold: int,
    url: AnyHttpUrl,
    headers: Dict[str, str],
) -> None:
    """
    Given a database connection string, fetches collections
    and fields and compares them to existing datasets or datasets in a
    local manifest (if one is provided).
    """
    manifest_taxonomy = parse(manifest_dir) if manifest_dir else None

    # Generate the collections and fields for the target database
    db_engine = get_db_engine(connection_string)
    db_collections = get_db_collections_and_fields(db_engine)

    uncategorized_fields, db_field_count = find_all_uncategorized_dataset_fields(
        manifest_taxonomy=manifest_taxonomy,
        db_collections=db_collections,
        url=url,
        headers=headers,
    )
    if db_field_count < 1:
        echo_red("Database did not contain any dataset fields to evaluate coverage")
        raise SystemExit(1)

    coverage_percent = int(
        ((db_field_count - len(uncategorized_fields)) / db_field_count) * 100
    )
    print_dataset_scan_result(
        datasets=list(db_collections.keys()),
        uncategorized_fields=uncategorized_fields,
        coverage_percent=coverage_percent,
        coverage_threshold=coverage_threshold,
    )


def generate_dataset(connection_string: str, file_name: str, include_null: bool) -> str:
    """
    Given a database connection string, extract all tables/fields from it
    and write out a boilerplate dataset manifest, excluding optional null attributes.

    An optional flag can be passed to include null fields, such as retention and
    nested fields.
    """
    db_engine = get_db_engine(connection_string)
    db_collections = get_db_collections_and_fields(db_engine)
    collections = create_dataset_collections(db_collections)
    manifests.write_manifest(
        file_name,
        [i.dict(exclude_none=not include_null) for i in collections],
        "dataset",
    )
    echo_green(f"Generated dataset manifest written to {file_name}")
    return file_name
