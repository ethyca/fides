import os
from typing import Generator
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.schemas.connection_configuration import RDSMySQLSchema

from .application_fixtures import integration_config, integration_secrets


@pytest.fixture(scope="function")
def rds_mysql_connection_config(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_rds_mysql_config",
            "connection_type": ConnectionType.rds_mysql,
            "access": AccessLevel.write,
        },
    )

    # Pulling from integration config file or GitHub secrets
    rds_mysql_integration_config = integration_config.get("rds_mysql", {})

    region = rds_mysql_integration_config.get("region") or os.environ.get(
        "RDS_MYSQL_REGION"
    )
    aws_access_key_id = rds_mysql_integration_config.get(
        "aws_access_key_id"
    ) or os.environ.get("RDS_MYSQL_AWS_ACCESS_KEY_ID")
    aws_secret_access_key = rds_mysql_integration_config.get(
        "aws_secret_access_key"
    ) or os.environ.get("RDS_MYSQL_AWS_SECRET_ACCESS_KEY")
    db_username = rds_mysql_integration_config.get("db_username") or os.environ.get(
        "RDS_MYSQL_DB_USERNAME"
    )
    db_instance = rds_mysql_integration_config.get("db_instance") or os.environ.get(
        "RDS_MYSQL_DB_INSTANCE"
    )
    db_name = rds_mysql_integration_config.get("db_name") or os.environ.get(
        "RDS_MYSQL_DB_NAME"
    )

    if not region:
        raise RuntimeError("Missing region for RDS MySQL")

    if not aws_access_key_id:
        raise RuntimeError("Missing aws_access_key_id for RDS MySQL")

    if not aws_secret_access_key:
        raise RuntimeError("Missing aws_secret_access_key for RDS MySQL")

    if not db_username:
        raise RuntimeError("Missing db_username for RDS MySQL")

    if not db_instance:
        raise RuntimeError("Missing db_instance for RDS MySQL")

    if not db_name:
        raise RuntimeError("Missing db_name for RDS MySQL")

    schema = RDSMySQLSchema(
        auth_method="secret_keys",
        region=region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        db_username=db_username,
    )
    connection_config.secrets = schema.model_dump()
    connection_config.save(db=db)

    yield connection_config
    connection_config.delete(db)
