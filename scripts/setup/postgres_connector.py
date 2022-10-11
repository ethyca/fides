import logging
import requests
from typing import Dict

from fides.api.ops.api.v1 import urn_registry as urls
from dataset import create_dataset

import constants


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_postgres_connector(
    auth_header: Dict[str, str],
    key: str = "postgres_connector",
    verify: bool = True,
):
    connection_create_data = [
        {
            "name": key,
            "key": key,
            "connection_type": "postgres",
            "access": "write",
        },
    ]
    response = requests.patch(
        f"{constants.BASE_URL}{urls.CONNECTIONS}",
        headers=auth_header,
        json=connection_create_data,
    )

    if not response.ok:
        raise RuntimeError(
            f"fidesops connection creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    connection_secrets_path = urls.CONNECTION_SECRETS.format(connection_key=key)
    url = f"{constants.BASE_URL}{connection_secrets_path}?verify={verify}"
    postgres_secrets_data = {
        "host": constants.POSTGRES_SERVER,
        "port": constants.POSTGRES_PORT,
        "dbname": constants.POSTGRES_DB_NAME,
        "username": constants.POSTGRES_USER,
        "password": constants.POSTGRES_PASSWORD,
    }
    response = requests.put(
        url,
        headers=auth_header,
        json=postgres_secrets_data,
    )

    if not response.ok:
        raise RuntimeError(
            f"fidesops connection configuration failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    if (response.json())["test_status"] == "failed":
        raise RuntimeError(
            f"fidesops connection test failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    logger.info(f"Configured fidesops postgres connection secrets for via {url}")

    create_dataset(
        connection_key=key,
        yaml_path="data/dataset/postgres_example_test_dataset.yml",
    )
