from typing import Dict

import requests
import yaml
from loguru import logger

from fides.api.ops.api.v1 import urn_registry as urls

from . import constants


def create_dataset(
    auth_header: Dict[str, str],
    connection_key: str,
    yaml_path: str,
):
    with open(yaml_path, "r") as file:
        dataset = yaml.safe_load(file).get("dataset", [])[0]

    # Create ctl_dataset resource first
    dataset_create_data = [dataset]
    dataset_path = "/dataset/upsert"
    url = f"{constants.BASE_URL}{dataset_path}"
    response = requests.post(
        url,
        headers=auth_header,
        json=dataset_create_data,
    )

    if response.ok:
        json_data = response.json()
        logger.info(json_data["message"])
    else:
        raise RuntimeError(
            f"fides dataset creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    # Now link that ctl_dataset to the DatasetConfig
    dataset_config_path = urls.DATASET_CONFIGS.format(connection_key=connection_key)
    url = f"{constants.BASE_URL}{dataset_config_path}"

    fides_key = dataset["fides_key"]
    response = requests.patch(
        url,
        headers=auth_header,
        json=[{"fides_key": fides_key, "ctl_dataset_fides_key": fides_key}],
    )

    if response.ok:
        datasets = (response.json())["succeeded"]
        if len(datasets) > 0:
            logger.info(f"Created fides dataset via {url}")
            return response.json()

    raise RuntimeError(
        f"fides dataset config creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )
