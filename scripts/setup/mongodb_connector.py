import logging
from typing import Dict

from .database_connector import (
    create_database_connector,
    update_database_connector_secrets,
)
from .dataset import create_dataset

from . import constants

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_mongodb_connector(
    auth_header: Dict[str, str],
    key: str = "mongodb_connector",
    verify: bool = True,
):
    create_database_connector(
        auth_header=auth_header,
        key=key,
        connection_type="mongodb",
    )
    update_database_connector_secrets(
        auth_header=auth_header,
        key=key,
        secrets={
            "host": constants.MONGO_SERVER,
            "port": str(constants.MONGO_PORT),
            "defaultauthdb": constants.MONGO_DB,
            "username": constants.MONGO_USER,
            "password": constants.MONGO_PASSWORD,
        },
        verify=verify,
    )
    create_dataset(
        auth_header=auth_header,
        connection_key=key,
        yaml_path="data/dataset/mongo_example_test_dataset.yml",
    )
