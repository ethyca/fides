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
        connection_config.secrets = schema.model_dump(mode="json")
        connection_config.save(db=db)

    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def snowflake_connection_config_without_default_dataset_or_schema(
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

    if all([account_identifier, user_login_name, password, warehouse_name]):
        schema = SnowflakeSchema(
            account_identifier=account_identifier,
            user_login_name=user_login_name,
            password=password,
            warehouse_name=warehouse_name,
        )
        connection_config.secrets = schema.model_dump(mode="json")
        connection_config.save(db=db)

    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def snowflake_connection_config_with_keypair(
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
    private_key = integration_config.get("snowflake", {}).get(
        "private_key"
    ) or os.environ.get("SNOWFLAKE_TEST_PRIVATE_KEY")
    private_key_passphrase = integration_config.get("snowflake", {}).get(
        "private_key_passphrase"
    ) or os.environ.get("SNOWFLAKE_TEST_PRIVATE_KEY_PASSPHRASE")
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
            private_key,
            private_key_passphrase,
            warehouse_name,
            database_name,
            schema_name,
        ]
    ):
        schema = SnowflakeSchema(
            account_identifier=account_identifier,
            user_login_name=user_login_name,
            private_key=private_key,
            private_key_passphrase=private_key_passphrase,
            warehouse_name=warehouse_name,
            database_name=database_name,
            schema_name=schema_name,
        )
        connection_config.secrets = schema.model_dump()
        connection_config.save(db=db)

    yield connection_config
    connection_config.delete(db)


@pytest.fixture(
    params=[
        "snowflake_connection_config",
        "snowflake_connection_config_with_keypair",
    ]
)
def snowflake_example_test_dataset_config(
    request,
    snowflake_connection_config: ConnectionConfig,
    snowflake_connection_config_with_keypair: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:

    if request.param == "snowflake_connection_config":
        config: ConnectionConfig = snowflake_connection_config
    elif request.param == "snowflake_connection_config_with_keypair":
        config: ConnectionConfig = snowflake_connection_config_with_keypair

    dataset = example_datasets[2]
    fides_key = dataset["fides_key"]

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)

    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset_config
    dataset_config.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def snowflake_example_test_dataset_config_with_namespace_meta(
    snowflake_connection_config_without_default_dataset_or_schema: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:

    connection_config = snowflake_connection_config_without_default_dataset_or_schema
    dataset = example_datasets[2]
    dataset["fides_meta"] = {
        "namespace": {"database_name": "FIDESOPS_TEST", "schema": "TEST"}
    }
    fides_key = dataset["fides_key"]

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)

    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset_config
    dataset_config.delete(db=db)
    ctl_dataset.delete(db=db)
