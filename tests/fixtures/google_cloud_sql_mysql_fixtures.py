import ast
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
from fides.api.schemas.connection_configuration import GoogleCloudSQLMySQLSchema

from .application_fixtures import integration_config


@pytest.fixture(scope="function")
def google_cloud_sql_mysql_connection_config(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_google_cloud_mysql_config",
            "connection_type": ConnectionType.google_cloud_sql_mysql,
            "access": AccessLevel.write,
        },
    )
    # Pulling from integration config file or GitHub secrets
    google_cloud_sql_mysql_integration_config = integration_config.get("google_cloud_sql_mysql", {})
    db_iam_user = google_cloud_sql_mysql_integration_config.get(
        "db_iam_user"
    ) or os.environ.get("GOOGLE_CLOUD_SQL_MYSQL_DB_IAM_USER")

    instance_connection_name = google_cloud_sql_mysql_integration_config.get(
        "instance_connection_name"
    ) or os.environ.get("GOOGLE_CLOUD_SQL_MYSQL_INSTANCE_CONNECTION_NAME")

    keyfile_creds = google_cloud_sql_mysql_integration_config.get(
        "keyfile_creds"
    ) or ast.literal_eval(os.environ.get("GOOGLE_CLOUD_SQL_MYSQL_KEYFILE_CREDS"))

    if keyfile_creds:
        schema = GoogleCloudSQLMySQLSchema(
            db_iam_user=db_iam_user,
            instance_connection_name=instance_connection_name,
            keyfile_creds=keyfile_creds,
        )
        connection_config.secrets = schema.dict()
        connection_config.save(db=db)

    yield connection_config
    connection_config.delete(db)
