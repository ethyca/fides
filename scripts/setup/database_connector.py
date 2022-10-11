import logging
import requests
from typing import Dict

from fides.api.ops.api.v1 import urn_registry as urls
from dataset import create_dataset

import constants


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_database_connector(
    auth_header: Dict[str, str],
    connection_type: str,
    key: str,
    access: str = "write",
):
    connection_create_data = [
        {
            "name": key,
            "key": key,
            "connection_type": connection_type,
            "access": access,
        },
    ]
    response = requests.patch(
        f"{constants.BASE_URL}{urls.CONNECTIONS}",
        headers=auth_header,
        json=connection_create_data,
    )

    if not response.ok:
        raise RuntimeError(
            f"fides connection creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    logger.info(f"Configured fides database connector for {key}")


def update_database_connector_secrets(
    auth_header: Dict[str, str],
    key: str,
    secrets: Dict[str, str],
    verify: bool,
):
    connection_secrets_path = urls.CONNECTION_SECRETS.format(connection_key=key)
    url = f"{constants.BASE_URL}{connection_secrets_path}?verify={verify}"

    response = requests.put(
        url,
        headers=auth_header,
        json=secrets,
    )

    if not response.ok:
        raise RuntimeError(
            f"fides connection configuration failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    if (response.json())["test_status"] == "failed":
        raise RuntimeError(
            f"fides connection test failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    logger.info(f"Configured fides connection secrets via {url}")
