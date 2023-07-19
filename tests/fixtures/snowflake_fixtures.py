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
from fides.api.schemas.connection_configuration.connection_secrets_snowflake import (
    SnowflakeSchema,
)


@pytest.fixture(scope="function")
def snowflake_connection_config_without_secrets(
    db: Session,
) -> Generator:
    """
    Returns a Snowflake ConnectionConfig without secrets
    attached that is safe to usein any tests.
    """
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_snowflake_config",
            "connection_type": ConnectionType.snowflake,
            "access": AccessLevel.write,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def snowflake_connection_config(
    db: Session,
    integration_config: Dict[str, str],
    snowflake_connection_config_without_secrets: ConnectionConfig,
) -> Generator:
    """
    Returns a Snowflake ConectionConfig with secrets attached if secrets are present
    in the configuration.
    """
    connection_config = snowflake_connection_config_without_secrets

    account_identifier = integration_config.get("snowflake", {}).get(
        "account_identifier"
    ) or os.environ.get("SNOWFLAKE_TEST_ACCOUNT_IDENTIFIER")
    user_login_name = integration_config.get("snowflake", {}).get(
        "user_login_name"
    ) or os.environ.get("SNOWFLAKE_TEST_USER_LOGIN_NAME")
    password = integration_config.get("snowflake", {}).get(
        "password"
    ) or os.environ.get("SNOWFLAKE_TEST_PASSWORD")
    warehouse_name = integration_config.get("snowflake", {}).get(
        "warehouse_name"
    ) or os.environ.get("SNOWFLAKE_TEST_WAREHOUSE_NAME")
    database_name = integration_config.get("snowflake", {}).get(
        "database_name"
    ) or os.environ.get("SNOWFLAKE_TEST_DATABASE_NAME")
    schema_name = integration_config.get("snowflake", {}).get(
        "schema_name"
    ) or os.environ.get("SNOWFLAKE_TEST_SCHEMA_NAME")

    if all(
        [
            account_identifier,
            user_login_name,
            password,
            warehouse_name,
            database_name,
            schema_name,
        ]
    ):
        schema = SnowflakeSchema(
            account_identifier=account_identifier,
            user_login_name=user_login_name,
            password=password,
            warehouse_name=warehouse_name,
            database_name=database_name,
            schema_name=schema_name,
        )
        connection_config.secrets = schema.dict()
        connection_config.save(db=db)

    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def snowflake_example_test_dataset_config(
    snowflake_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    dataset = example_datasets[2]
    fides_key = dataset["fides_key"]

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)

    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": snowflake_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset_config
    dataset_config.delete(db=db)
    ctl_dataset.delete(db=db)
