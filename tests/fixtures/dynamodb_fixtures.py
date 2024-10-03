import os
from typing import Any, Dict, Generator, List
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
from fides.api.schemas.connection_configuration.connection_secrets_dynamodb import (
    DynamoDBSchema,
)

from .application_fixtures import integration_secrets


@pytest.fixture(scope="function")
def dynamodb_connection_config_without_secrets(db: Session) -> Generator:
    """
    Returns a DynamoDB ConnectionConfig without secrets
    attached that is safe to use in any test.
    """
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_dynamodb_config",
            "connection_type": ConnectionType.dynamodb,
            "access": AccessLevel.write,
            "secrets": integration_secrets["dynamodb_example"],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def dynamodb_connection_config(
    db: Any,  # type: ignore
    integration_config: Dict[str, str],
    dynamodb_connection_config_without_secrets: ConnectionConfig,
) -> Generator:
    """
    Returns a DynamoDB ConectionConfig with secrets attached if secrets are present
    in the configuration.
    """
    dynamodb_connection_config = dynamodb_connection_config_without_secrets
    region = integration_config.get("dynamodb_example", {}).get(
        "region"
    ) or os.environ.get("DYNAMODB_REGION")
    aws_access_key_id = integration_config.get("dynamodb_example", {}).get(
        "aws_access_key_id"
    ) or os.environ.get("DYNAMODB_ACCESS_KEY_ID")
    aws_secret_access_key = integration_config.get("dynamodb_example", {}).get(
        "aws_secret_access_key"
    ) or os.environ.get("DYNAMODB_ACCESS_KEY")
    aws_assume_role_arn = integration_config.get("dynamodb_example", {}).get(
        "aws_assume_role_arn"
    ) or os.environ.get("DYNAMODB_ASSUME_ROLE_ARN")

    if not aws_access_key_id or not aws_secret_access_key or not region:
        raise RuntimeError("DynamoDB env vars must be set!")

    if region is not None:
        schema = DynamoDBSchema(
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_assume_role_arn=aws_assume_role_arn,
            auth_method="secret_keys"
        )
        dynamodb_connection_config.secrets = schema.model_dump(mode="json")
        dynamodb_connection_config.save(db=db)
    yield dynamodb_connection_config


@pytest.fixture
def dynamodb_example_test_dataset_config(
    dynamodb_connection_config: ConnectionConfig,
    db: Any,  # type: ignore
    example_datasets: List[Dict],
) -> Generator:
    dataset = example_datasets[11]
    fides_key = dataset["fides_key"]

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)

    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": dynamodb_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset_config
    dataset_config.delete(db=db)
    ctl_dataset.delete(db=db)
