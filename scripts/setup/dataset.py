import logging
import requests
from typing import Dict
import yaml

from fides.api.ops.api.v1 import urn_registry as urls

import constants


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_dataset(
    auth_header: Dict[str, str],
    connection_key: str,
    yaml_path: str,
):
    with open(yaml_path, "r") as file:
        dataset = yaml.safe_load(file).get("dataset", [])[0]

    dataset_create_data = [dataset]
    dataset_path = urls.DATASETS.format(connection_key=connection_key)
    url = f"{constants.BASE_URL}{dataset_path}"
    response = requests.patch(
        url,
        headers=auth_header,
        json=dataset_create_data,
    )

    if response.ok:
        datasets = (response.json())["succeeded"]
        if len(datasets) > 0:
            logger.info(f"Created fidesops dataset via {url}")
            return response.json()

    raise RuntimeError(
        f"fidesops dataset creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )
