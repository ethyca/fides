import os
from typing import Any, Dict, Generator
from uuid import uuid4

import pytest
from loguru import logger
from pymongo import MongoClient

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.service.connectors import MongoDBConnector
from tests.fixtures.integration_fixtures import (
    generate_integration_records,
    generate_mongo_specific_records,
    mongo_dataset_dict,
)
from tests.ops.integration_tests.mongodb_atlas.mongo_sample import mongo_sample_data


@pytest.fixture(scope="function")
def unique_database_name() -> str:
    """Generate a unique MongoDB database name per-test to avoid duplicate key errors."""
    return f"mongo_test_{str(uuid4()).replace('-', '')[:8]}"


# Helper functions
def mongodb_atlas_insert(
    client: MongoClient, db_name: str, collection_name: str, record: Dict[str, Any]
) -> None:
    db = client[db_name]
    collection = db[collection_name]
    return collection.insert_one(record).inserted_id


def mongodb_atlas_delete(
    client: MongoClient,
    db_name: str,
    collection_name: str,
) -> None:
    """
    Deletion in the context of this test. This deletion is not using the mongo _id fields,
    since those are generated at the time of the test."""

    db = client[db_name]
    collection = db[collection_name]

    # Delete the entire collection
    return collection.delete_many({})


@pytest.fixture(scope="function")
def integration_mongodb_atlas_config(db) -> Generator[ConnectionConfig, None, None]:
    """MongoDB Atlas connection config with SRV and SSL enabled"""

    # Apply environment variable fallbacks with defaults
    atlas_secrets = {
        "host": os.environ.get("MONGODB_ATLAS_HOST"),
        "defaultauthdb": os.environ.get("MONGODB_ATLAS_DEFAULT_AUTH_DB"),
        "username": os.environ.get("MONGODB_ATLAS_USERNAME"),
        "password": os.environ.get("MONGODB_ATLAS_PASSWORD"),
        "use_srv": os.environ.get("MONGODB_ATLAS_USE_SRV", "true").lower() == "true",
        "ssl_enabled": os.environ.get("MONGODB_ATLAS_SSL_ENABLED", "true").lower()
        == "true",
    }

    connection_config = ConnectionConfig(
        key="mongodb_atlas",
        connection_type=ConnectionType.mongodb,
        access=AccessLevel.write,
        secrets=atlas_secrets,
        name="mongodb_atlas",
    )
    connection_config.save(db)
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def integration_mongodb_atlas_config_with_dataset(
    db,
    integration_mongodb_atlas_config,
    integration_postgres_config_with_dataset,
    unique_database_name,
) -> Generator[ConnectionConfig, None, None]:
    """MongoDB Atlas connection config with associated dataset"""
    connection_config = integration_mongodb_atlas_config

    # The postgres config is used to generate the dataset references in `mongo_atlas_dataset_dict`
    ctl_dataset = CtlDataset.create_from_dataset_dict(
        db,
        mongo_dataset_dict(
            unique_database_name, integration_postgres_config_with_dataset.key
        ),
    )
    DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": connection_config.key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )

    yield connection_config


@pytest.fixture(scope="function")
def integration_mongodb_atlas_connector(
    integration_mongodb_atlas_config,
) -> MongoClient:
    """MongoDB Atlas connector client"""
    return MongoDBConnector(integration_mongodb_atlas_config).client()


@pytest.fixture(scope="function")
def seed_mongo_sample_data(
    integration_mongodb_atlas_connector,
    unique_database_name,
) -> Generator[None, None, None]:
    """Load sample data into a new MongoDB Atlas database then drop the database after the test is complete"""

    records = mongo_sample_data

    for table_name, record_list in records.items():
        for record in record_list:
            mongodb_atlas_insert(
                integration_mongodb_atlas_connector,
                unique_database_name,
                table_name,
                record,
            )
    yield records
    drop_database(integration_mongodb_atlas_connector, unique_database_name)


@pytest.fixture(scope="function")
def mongodb_atlas_inserts(integration_mongodb_atlas_connector, unique_database_name):
    """Insert test data into MongoDB Atlas and clean up afterwards"""

    # Use the same data generation as standard MongoDB tests
    records = generate_integration_records()
    records.update(generate_mongo_specific_records())
    for table_name, record_list in records.items():
        for record in record_list:
            mongodb_atlas_insert(
                integration_mongodb_atlas_connector,
                unique_database_name,
                table_name,
                record,
            )
    yield records
    drop_database(integration_mongodb_atlas_connector, unique_database_name)


def drop_database(client: MongoClient, database_name: str) -> None:
    """Drop the specified database."""
    try:
        logger.info(f"Dropping database: {database_name}")
        client.drop_database(database_name)
        logger.info(f"Successfully dropped database: {database_name}")
    except Exception as exc:
        logger.error(
            "Make sure the MongoDB Atlas user credentials have the Atlas Admin role to be able to drop databases."
        )
        raise exc
