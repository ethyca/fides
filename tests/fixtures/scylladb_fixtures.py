from typing import Dict, List

import pytest
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.schemas.connection_configuration.connection_secrets_scylla import (
    ScyllaSchema,
)
from fides.api.service.connectors.scylla_connector import ScyllaConnector


@pytest.fixture(scope="function")
def scylladb_integration_with_keyspace(integration_scylladb_config_with_keyspace):
    connector = ScyllaConnector(integration_scylladb_config_with_keyspace)
    client = connector.create_client()
    yield client


@pytest.fixture(scope="function")
def scylladb_integration_no_keyspace(integration_scylladb_config):
    connector = ScyllaConnector(integration_scylladb_config)
    client = connector.create_client()
    yield client


@pytest.fixture(scope="function")
def scylladb_test_dataset_config(
    integration_scylladb_config_with_keyspace: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
):
    scylladb_dataset = example_datasets[15]
    fides_key = scylladb_dataset["fides_key"]
    integration_scylladb_config_with_keyspace.name = fides_key
    integration_scylladb_config_with_keyspace.key = fides_key
    integration_scylladb_config_with_keyspace.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, scylladb_dataset)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": integration_scylladb_config_with_keyspace.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def scylla_db_integration(integration_scylladb_config_with_keyspace):
    scylla_config = ScyllaSchema(**integration_scylladb_config_with_keyspace.secrets)
    auth_provider = PlainTextAuthProvider(
        username=scylla_config.username, password=scylla_config.password
    )
    cluster = Cluster(
        [scylla_config.host], port=scylla_config.port, auth_provider=auth_provider
    )
    return cluster
