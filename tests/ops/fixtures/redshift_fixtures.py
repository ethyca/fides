import os
from typing import Dict, Generator, List
from uuid import uuid4

import pytest
from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.datasetconfig import DatasetConfig
from fidesops.ops.schemas.connection_configuration.connection_secrets_redshift import (
    RedshiftSchema,
)
from sqlalchemy.orm import Session

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
    uri = integration_config.get("redshift", {}).get("external_uri") or os.environ.get(
        "REDSHIFT_TEST_URI"
    )
    db_schema = integration_config.get("redshift", {}).get(
        "db_schema"
    ) or os.environ.get("REDSHIFT_TEST_DB_SCHEMA")
    if uri and db_schema:
        schema = RedshiftSchema(url=uri, db_schema=db_schema)
        connection_config.secrets = schema.dict()
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
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": redshift_connection_config.id,
            "fides_key": fides_key,
            "dataset": dataset,
        },
    )
    yield dataset_config
    dataset_config.delete(db=db)
