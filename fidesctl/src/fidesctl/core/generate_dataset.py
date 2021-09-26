"""Module that generates valid dataset manifest files from various data sources."""
from typing import Dict, List

import sqlalchemy
from sqlalchemy.engine import Engine

from fideslang import manifests
from .utils import get_db_engine, echo_green


def get_db_tables(engine: Engine) -> Dict[str, List[str]]:
    """
    Return an object containing all of the tables within
    a database and their columns
    """
    inspector = sqlalchemy.inspect(engine)
    db_tables = {
        f"{schema}.{table}": [column["name"] for column in inspector.get_columns(table)]
        for schema in inspector.get_schema_names()
        for table in inspector.get_table_names(schema=schema)
        if schema != "information_schema"
    }
    return db_tables


def generate_table_manifests(
    db_tables: Dict[str, List[str]]
) -> List[Dict[str, object]]:
    """
    Return an object of tables and columns formatted for a Fides manifest
    with dummy values where needed.
    """
    table_manifests = [
        {
            "name": table,
            "description": f"Fides Generated Description for Table: {table}",
            "dataset_fields": [
                {
                    "name": column,
                    "description": f"Fides Generated Description for Column: {column}",
                    "data_categories": [],
                }
                for column in db_tables[table]
            ],
        }
        for table in db_tables.keys()
    ]
    return table_manifests


def generate_dataset_info(engine: Engine) -> Dict[str, List]:
    """
    Generate a partial dataset manifest, sans tables/fields,
    given a database engine.
    """
    url = engine.url
    name = url.database
    dataset_type = engine.name
    dataset_location = f"{url.host}:{url.port}"
    dataset_info = {
        "dataset": [
            {
                "organization_fides_key": 1,
                "fides_key": name,
                "name": name,
                "description": f"Fides Generated Description for Dataset: {name}",
                "dataset_type": dataset_type,
                "dataset_location": dataset_location,
            }
        ]
    }
    return dataset_info


def generate_dataset(connection_string: str, file_name: str) -> None:
    """
    Given a database connection string, extract all tables/fields from it
    and write out a boilerplate dataset manifest.
    """
    db_engine = get_db_engine(connection_string)
    db_tables = get_db_tables(db_engine)
    table_manifests = generate_table_manifests(db_tables)
    dataset_info = generate_dataset_info(db_engine)
    dataset_info["dataset"][0]["datasetTables"] = table_manifests
    manifests.write_manifest(file_name, dataset_info)
    echo_green(f"Generated dataset manifest written to {file_name}")
