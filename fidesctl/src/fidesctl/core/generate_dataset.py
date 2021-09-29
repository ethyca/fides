"""Module that generates valid dataset manifest files from various data sources."""
from typing import Dict, List

import sqlalchemy
from sqlalchemy.engine import Engine

from fideslang import manifests
from fideslang.models import Dataset, DatasetCollection, DatasetField
from .utils import get_db_engine, echo_green


def get_db_collections_and_fields(engine: Engine) -> Dict[str, List[str]]:
    """
    Return an object containing all of the tables within
    a database and their fields.
    """
    inspector = sqlalchemy.inspect(engine)
    db_tables = {
        f"{schema}.{table}": [column["name"] for column in inspector.get_columns(table)]
        for schema in inspector.get_schema_names()
        for table in inspector.get_table_names(schema=schema)
        if schema != "information_schema"
    }
    return db_tables


def create_dataset_collections(
    db_tables: Dict[str, List[str]]
) -> List[DatasetCollection]:
    """
    Return an object of tables and columns formatted for a Fides manifest
    with dummy values where needed.
    """

    table_manifests = [
        DatasetCollection(
            name=table,
            description=f"Fides Generated Description for Table: {table}",
            fields=[
                DatasetField(
                    name=column,
                    description=f"Fides Generated Description for Column: {column}",
                    data_categories=[],
                )
                for column in db_tables[table]
            ],
        )
        for table in db_tables.keys()
    ]
    return table_manifests


def create_dataset(engine: Engine, collections: List[DatasetCollection]) -> Dataset:
    """
    Generate a partial dataset manifest, sans tables/fields,
    given a database engine.
    """
    url = engine.url
    name = url.database
    dataset = Dataset(
        fides_key=name,
        name=name,
        description=f"Fides Generated Description for Dataset: {name}",
        collections=collections,
    )
    return dataset


def generate_dataset(connection_string: str, file_name: str) -> None:
    """
    Given a database connection string, extract all tables/fields from it
    and write out a boilerplate dataset manifest.
    """
    db_engine = get_db_engine(connection_string)
    db_collections = get_db_collections_and_fields(db_engine)
    collections = create_dataset_collections(db_collections)
    dataset = create_dataset(db_engine, collections)
    manifests.write_manifest(file_name, dataset.dict(), "dataset")
    echo_green(f"Generated dataset manifest written to {file_name}")
