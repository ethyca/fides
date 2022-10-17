import logging
from typing import Dict

import requests

from fides.api.ops.api.v1 import urn_registry as urls

from . import constants, get_secret

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_s3_storage(
    auth_header: Dict[str, str],
    key: str = constants.S3_STORAGE_KEY,
    bucket: str = constants.S3_STORAGE_BUCKET,
):
    logger.info(f"Configuring S3 storage with key={key} and bucket={bucket}")
    url = f"{constants.BASE_URL}{urls.STORAGE_CONFIG}"
    response = requests.patch(
        url,
        headers=auth_header,
        json=[
            {
                "name": key,
                "key": key,
                "type": "s3",
                "format": "json",
                "details": {
                    "auth_method": "secret_keys",
                    "bucket": bucket,
                    "object_name": "requests",
                    "naming": "request_id",
                },
            },
        ],
    )

    logger.info(f"Configuring S3 storage secrets for key={key}")
    if not response.ok:
        raise RuntimeError(
            f"fides storage creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )
    else:
        storage = (response.json())["succeeded"]
        if len(storage) > 0:
            logger.info(f"Created fides storage with key={key} via {url}")

    # Update the storage config with the appropriate secrets
    storage_secrets_path = urls.STORAGE_SECRETS.format(config_key=key)
    url = f"{constants.BASE_URL}{storage_secrets_path}"
    response = requests.put(
        url,
        headers=auth_header,
        json={
            "aws_access_key_id": get_secret("AWS_SECRETS")["access_key_id"],
            "aws_access_secret_id": get_secret("AWS_SECRETS")["access_secret_id"],
        },
    )
    if not response.ok:
        raise RuntimeError(
            f"fides storage secrets failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )
