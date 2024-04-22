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
from fides.api.schemas.connection_configuration.connection_secrets_oracle_db import (
    OracleDBSchema,
)

from .application_fixtures import integration_config


@pytest.fixture(scope="function")
def oracle_db_connection_config(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_oracle_db_config",
            "connection_type": ConnectionType.oracle_db,
            "access": AccessLevel.write,
        },
    )

    host = integration_config.get("oracle_db", {}).get("host") or os.environ.get(
        "ORACLE_DB_TEST_HOST"
    )
    port = integration_config.get("oracle_db", {}).get("port") or os.environ.get(
        "ORACLE_DB_TEST_PORT"
    )
    username = integration_config.get("oracle_db", {}).get(
        "username"
    ) or os.environ.get("ORACLE_DB_TEST_USER")
    password = integration_config.get("oracle_db", {}).get(
        "password"
    ) or os.environ.get("ORACLE_DB_TEST_PASSWORD")
    service_name = integration_config.get("oracle_db", {}).get(
        "service_name"
    ) or os.environ.get("ORACLE_DB_TEST_SERVICE_NAME")

    if all([host, port, username, password, service_name]):
        schema = OracleDBSchema(
            host=host,
            port=int(port) if port and port.isdigit() else None,
            username=username,
            password=password,
            service_name=service_name,
        )
        connection_config.secrets = schema.dict()
        connection_config.save(db=db)

    yield connection_config
    connection_config.delete(db)
