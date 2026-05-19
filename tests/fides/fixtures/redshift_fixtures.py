import os
from typing import Dict, Generator, List
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.schemas.connection_configuration.connection_secrets_redshift import (
    RedshiftSchema,
)

from .application_fixtures import integration_config


@pytest.fixture(scope="function")
def redshift_connection_config(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_redshift_config",
            "connection_type": ConnectionType.redshift,
            "access": AccessLevel.write,
        },
    )

    host = integration_config.get("redshift", {}).get("host") or os.environ.get(
        "REDSHIFT_TEST_HOST"
    )
    port = integration_config.get("redshift", {}).get("port") or os.environ.get(
        "REDSHIFT_TEST_PORT"
    )
    user = integration_config.get("redshift", {}).get("user") or os.environ.get(
        "REDSHIFT_TEST_USER"
    )
    password = integration_config.get("redshift", {}).get("password") or os.environ.get(
        "REDSHIFT_TEST_PASSWORD"
    )
    database = integration_config.get("redshift", {}).get("database") or os.environ.get(
        "REDSHIFT_TEST_DATABASE"
    )
    db_schema = integration_config.get("redshift", {}).get(
        "db_schema"
    ) or os.environ.get("REDSHIFT_TEST_DB_SCHEMA")

    if all([host, port, user, password, database, db_schema]):
        schema = RedshiftSchema(
            host=host,
            port=int(port) if port and port.isdigit() else None,
            user=user,
            password=password,
            database=database,
            db_schema=db_schema,
        )
        connection_config.secrets = schema.model_dump(mode="json")
        connection_config.save(db=db)

    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def redshift_example_test_dataset_config(
    redshift_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    dataset = example_datasets[3]
    fides_key = dataset["fides_key"]

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)

    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": redshift_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset_config
    dataset_config.delete(db=db)
    ctl_dataset.delete(db=db)
