import logging
import requests
from typing import Dict

from fides.api.ops.api.v1 import urn_registry as urls
from setup.database_connector import (
    create_database_connector,
    update_database_connector_secrets,
)
from setup.dataset import create_dataset

import setup.constants as constants


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_postgres_connector(
    auth_header: Dict[str, str],
    key: str = "postgres_connector",
    verify: bool = True,
):
    create_database_connector(
        auth_header=auth_header,
        key=key,
        connection_type="postgres",
    )
    update_database_connector_secrets(
        auth_header=auth_header,
        key=key,
        secrets={
            "host": constants.POSTGRES_SERVER,
            "port": constants.POSTGRES_PORT,
            "dbname": constants.POSTGRES_DB_NAME,
            "username": constants.POSTGRES_USER,
            "password": constants.POSTGRES_PASSWORD,
        },
        verify=verify,
    )
    create_dataset(
        connection_key=key,
        yaml_path="data/dataset/postgres_example_test_dataset.yml",
    )
