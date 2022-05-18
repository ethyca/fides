"""Module that adds functionality for generating or scanning datasets."""
import asyncio
from typing import Dict, List, Optional, Tuple

import sqlalchemy
from pydantic import AnyHttpUrl
from sqlalchemy.engine import Engine

from fidesctl.core.api_helpers import list_server_resources
from fidesctl.core.parse import parse
from fideslang import manifests
from fideslang.models import Dataset, DatasetCollection, DatasetField

from .utils import echo_green, echo_red, get_db_engine

SCHEMA_EXCLUSION = {
    "postgresql": ["information_schema"],
    "mysql": ["mysql", "performance_schema", "sys", "information_schema"],
    "mssql": ["INFORMATION_SCHEMA", "guest", "sys"],
    "snowflake": ["information_schema"],
    "redshift": ["information_schema"],
}


def get_all_server_datasets(
    url: AnyHttpUrl, headers: Dict[str, str], exclude_datasets: List[Dataset]
) -> List[Dataset]:
    """
    Get a list of all of the Datasets that exist on the server. Excludes any datasets
    provided in exclude_datasets
    """
    exclude_dataset_keys = [dataset.fides_key for dataset in exclude_datasets]
    dataset_list = list_server_resources(
        url=url,
        resource_type="dataset",
        exclude_keys=exclude_dataset_keys,
        headers=headers,
    )
    return dataset_list


def include_dataset_schema(schema: str, database_type: str) -> bool:
    """
    Returns whether a schema should be included based on database type and schema name
    """
    schema_exclusion_list = SCHEMA_EXCLUSION.get(database_type, [])
    if database_type == "mssql":
        return schema not in schema_exclusion_list and not schema.startswith("db_")
    return schema not in schema_exclusion_list


def get_db_schemas(
    engine: Engine,
) -> Dict[str, Dict[str, List[str]]]:
    """
    Extract the schema, table and column names from a database given a sqlalchemy engine
    """
    inspector = sqlalchemy.inspect(engine)
    db_schemas: Dict[str, Dict[str, List]] = {}
    for schema in inspector.get_schema_names():
        if include_dataset_schema(schema=schema, database_type=engine.dialect.name):
            db_schemas[schema] = {}
            for table in inspector.get_table_names(schema=schema):
                db_schemas[schema][table] = [
                    column["name"]
                    for column in inspector.get_columns(table, schema=schema)
                ]
    return db_schemas


def create_db_datasets(db_schemas: Dict[str, Dict[str, List[str]]]) -> List[Dataset]:
    """
    Returns a list of dataset objects given a database schema
    mapping.
    """
    datasets = [
        create_db_dataset(schema_name=schema_name, db_tables=db_tables)
        for schema_name, db_tables in db_schemas.items()
    ]
    return datasets


def create_db_dataset(schema_name: str, db_tables: Dict[str, List[str]]) -> Dataset:
    """
    Returns a Dataset object of a database schema given a schema name
    and table definitions.

    Placeholder values are use where needed.
    """
    dataset = Dataset(
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
            for table_name, table in db_tables.items()
        ],
    )
    return dataset


def find_uncategorized_dataset_fields(
    existing_dataset: Optional[Dataset], source_dataset: Dataset
) -> Tuple[List[str], int]:
    """
    Iterates all fields in a source dataset and finds which are not
    defined or categorized in an existing dataset. Returns fields that
    are not categorized or defined, and also the total fields iterated.
    """
    uncategorized_fields = []
    total_field_count = 0

    for source_dataset_collection in source_dataset.collections:
        existing_dataset_collection = (
            next(
                (
                    existing_dataset_collection
                    for existing_dataset_collection in existing_dataset.collections
                    if existing_dataset_collection.name
                    == source_dataset_collection.name
                ),
                None,
            )
            if existing_dataset
            else None
        )

        for db_dataset_field in source_dataset_collection.fields:
            total_field_count += 1
            field_uncategorized = (
                all(
                    field.name != db_dataset_field.name or not field.data_categories
                    for field in existing_dataset_collection.fields
                )
                if existing_dataset_collection
                else True
            )

            if field_uncategorized:
                uncategorized_fields.append(
                    f"{source_dataset.name}.{source_dataset_collection.name}.{db_dataset_field.name}"
                )
    return uncategorized_fields, total_field_count


def find_all_uncategorized_dataset_fields(
    existing_datasets: List[Dataset], source_datasets: List[Dataset]
) -> Tuple[List[str], int]:
    """
    Finds all uncategorized fields given a list of source datasets
    and existing datasets to compare against.
    """
    uncategorized_fields = []
    total_field_count = 0
    for source_dataset in source_datasets:
        existing_dataset = next(
            (
                existing_dataset
                for existing_dataset in existing_datasets
                if existing_dataset.name == source_dataset.name
            ),
            None,
        )

        (
            current_uncategorized_keys,
            current_field_count,
        ) = find_uncategorized_dataset_fields(
            existing_dataset=existing_dataset, source_dataset=source_dataset
        )
        total_field_count += current_field_count
        uncategorized_fields += current_uncategorized_keys

    return uncategorized_fields, total_field_count


def print_dataset_db_scan_result(
    datasets: List[Dataset],
    uncategorized_fields: List[str],
    coverage_percent: int,
    coverage_threshold: int,
) -> None:
    """
    Prints uncategorized fields and raises an exception if coverage
    is lower than provided threshold.
    """
    dataset_names = [dataset.name for dataset in datasets]
    output: str = "Successfully scanned the following datasets:\n"
    output += "\t{}\n".format("\n\t".join(dataset_names))
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


def get_dataset_resource_ids(datasets: List[Dataset]) -> List[str]:
    """
    Given a list of datasets, build a list of resource ids
    """
    dataset_resource_ids = []
    for dataset in datasets:
        resource_id = get_dataset_resource_id(dataset=dataset)
        if resource_id:
            dataset_resource_ids.append(resource_id)
    return dataset_resource_ids


def get_dataset_resource_id(dataset: Dataset) -> Optional[str]:
    """
    Given a resource dataset, returns the resource id. Returns None
    if a resource_id is not found in metadata.
    """
    dataset_resource_id = (
        dataset.fidesctl_meta.resource_id
        if dataset.fidesctl_meta and dataset.fidesctl_meta.resource_id
        else None
    )
    return dataset_resource_id


def find_missing_datasets(
    source_datasets: List[Dataset],
    existing_datasets: List[Dataset],
) -> List[Dataset]:
    """
    Given a list of source and existing okta datasets, returns a list
    of datasets which are not found in the existing list.
    """
    existing_resource_ids = get_dataset_resource_ids(datasets=existing_datasets)
    missing_datasets = [
        source_dataset
        for source_dataset in source_datasets
        if get_dataset_resource_id(dataset=source_dataset) not in existing_resource_ids
    ]
    return missing_datasets


def print_dataset_resource_scan_result(
    source_datasets: List[Dataset],
    missing_datasets: List[Dataset],
    coverage_threshold: int,
) -> None:
    """
    Prints missing datasets and raises an exception if coverage
    is lower than provided threshold.
    """
    output: str = "Successfully scanned the following datasets:\n"
    for source_dataset in source_datasets:
        output += "\t{}(id={})\n".format(
            source_dataset.name, get_dataset_resource_id(dataset=source_dataset)
        )
    echo_green(output)

    if missing_datasets:
        missing_datasets_output = (
            "The following datasets were not found in existing manifest:\n"
        )
        for missing_dataset in missing_datasets:
            missing_datasets_output += "\t{}(id={})\n".format(
                missing_dataset.name, get_dataset_resource_id(dataset=missing_dataset)
            )
        echo_red(missing_datasets_output)

    coverage_percent = int(
        ((len(source_datasets) - len(missing_datasets)) / len(source_datasets)) * 100
    )
    annotation_output = "Resource coverage: {}%".format(coverage_percent)
    if coverage_percent < coverage_threshold:
        echo_red(annotation_output)
        raise SystemExit(1)
    echo_green(annotation_output)


def scan_dataset_db(
    connection_string: str,
    manifest_dir: Optional[str],
    coverage_threshold: int,
    url: AnyHttpUrl,
    headers: Dict[str, str],
) -> None:
    """
    Given a database connection string, fetches collections
    and fields and compares them to existing datasets and prioritizes
    datasets in a local manifest (if one is provided).
    """
    manifest_taxonomy = parse(manifest_dir) if manifest_dir else None
    manifest_datasets = manifest_taxonomy.dataset if manifest_taxonomy else []
    server_datasets = get_all_server_datasets(
        url=url, headers=headers, exclude_datasets=manifest_datasets
    )

    dataset_keys = [
        dataset.fides_key for dataset in manifest_datasets + server_datasets
    ]
    echo_green(
        "Loaded the following dataset manifests:\n\t{}".format(
            "\n\t".join(dataset_keys)
        )
    )

    # Generate the collections and fields for the target database
    db_engine = get_db_engine(connection_string)
    db_schemas = get_db_schemas(engine=db_engine)
    db_datasets = create_db_datasets(db_schemas=db_schemas)
    uncategorized_fields, db_field_count = find_all_uncategorized_dataset_fields(
        existing_datasets=manifest_datasets + server_datasets,
        source_datasets=db_datasets,
    )
    if db_field_count < 1:
        echo_red("Database did not contain any dataset fields to evaluate coverage")
        raise SystemExit(1)

    coverage_percent = int(
        ((db_field_count - len(uncategorized_fields)) / db_field_count) * 100
    )
    print_dataset_db_scan_result(
        datasets=db_datasets,
        uncategorized_fields=uncategorized_fields,
        coverage_percent=coverage_percent,
        coverage_threshold=coverage_threshold,
    )


def scan_dataset_okta(
    manifest_dir: str,
    org_url: str,
    coverage_threshold: int,
    url: AnyHttpUrl,
    headers: Dict[str, str],
) -> None:
    """
    Given an organization url, fetches Okta applications and compares them
    against existing datasets in the server and manifest supplied.
    """

    _check_okta_import()

    manifest_taxonomy = parse(manifest_dir) if manifest_dir else None
    manifest_datasets = manifest_taxonomy.dataset if manifest_taxonomy else []
    server_datasets = get_all_server_datasets(
        url=url, headers=headers, exclude_datasets=manifest_datasets
    )

    import fidesctl.connectors.okta as okta_connector

    okta_client = okta_connector.get_okta_client(org_url)
    okta_applications = asyncio.run(
        okta_connector.list_okta_applications(okta_client=okta_client)
    )
    okta_datasets = okta_connector.create_okta_datasets(
        okta_applications=okta_applications
    )
    if len(okta_datasets) < 1:
        echo_red("Okta did not return any applications to scan datasets")
        raise SystemExit(1)

    missing_datasets = find_missing_datasets(
        source_datasets=okta_datasets,
        existing_datasets=server_datasets + manifest_datasets,
    )
    print_dataset_resource_scan_result(
        source_datasets=okta_datasets,
        missing_datasets=missing_datasets,
        coverage_threshold=coverage_threshold,
    )


def write_dataset_manifest(
    file_name: str, include_null: bool, datasets: List[Dataset]
) -> None:
    """
    Given a list of datasets, writes a manifest file with the given datasets.

    An optional flag can be passed to include null fields.
    """
    manifests.write_manifest(
        file_name,
        [i.dict(exclude_none=not include_null) for i in datasets],
        "dataset",
    )
    echo_green(f"Generated dataset manifest written to {file_name}")


def generate_dataset_db(
    connection_string: str, file_name: str, include_null: bool
) -> str:
    """
    Given a database connection string, extract all tables/fields from it
    and write out a boilerplate dataset manifest, excluding optional null attributes.
    """
    db_engine = get_db_engine(connection_string)
    db_schemas = get_db_schemas(engine=db_engine)
    db_datasets = create_db_datasets(db_schemas=db_schemas)
    write_dataset_manifest(
        file_name=file_name, include_null=include_null, datasets=db_datasets
    )
    return file_name


def generate_dataset_okta(org_url: str, file_name: str, include_null: bool) -> str:
    """
    Given an organization url, generates a dataset manifest from existing Okta
    applications.
    """

    _check_okta_import()

    import fidesctl.connectors.okta as okta_connector

    okta_client = okta_connector.get_okta_client(org_url)
    okta_applications = asyncio.run(
        okta_connector.list_okta_applications(okta_client=okta_client)
    )
    okta_datasets = okta_connector.create_okta_datasets(
        okta_applications=okta_applications
    )
    write_dataset_manifest(
        file_name=file_name, include_null=include_null, datasets=okta_datasets
    )
    return file_name


def _check_okta_import() -> None:
    "Validate okta can be imported"
    try:
        import okta  # pylint: disable=unused-import
    except ModuleNotFoundError:
        echo_red('Packages not found, try: pip install "fidesctl[okta]"')
        raise SystemExit
