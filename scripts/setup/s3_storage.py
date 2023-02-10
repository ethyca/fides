from typing import Dict

import requests
from loguru import logger

from fides.api.ops.api.v1 import urn_registry as urls

from . import constants, get_secret


def create_s3_storage(
    auth_header: Dict[str, str],
    bucket: str = constants.S3_STORAGE_BUCKET,
):
    logger.info(f"Configuring S3 storage with bucket={bucket}")
    url = f"{constants.BASE_URL}{urls.STORAGE_DEFAULT}"
    response = requests.put(
        url,
        headers=auth_header,
        json={
            "type": "s3",
            "format": "json",
            "details": {
                "auth_method": "secret_keys",
                "bucket": bucket,
                "naming": "request_id",
            },
        },
    )

    logger.info(f"Configuring S3 storage secrets for default s3 storage")
    if not response.ok:
        raise RuntimeError(
            f"fides storage creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    logger.info(f"Created default s3 storage via {url}")

    # Update the storage config with the appropriate secrets
    storage_secrets_path = urls.STORAGE_DEFAULT_SECRETS.format(storage_type="s3")
    url = f"{constants.BASE_URL}{storage_secrets_path}"
    response = requests.put(
        url,
        headers=auth_header,
        json={
            "aws_access_key_id": get_secret("AWS_SECRETS")["access_key_id"],
            "aws_secret_access_key": get_secret("AWS_SECRETS")["secret_access_key"],
        },
    )
    if not response.ok:
        raise RuntimeError(
            f"fides storage secrets failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    url = f"{constants.BASE_URL}{urls.CONFIG}"
    response = requests.patch(
        url,
        headers=auth_header,
        json={"storage": {"active_default_storage_type": "s3"}},
    )
    if not response.ok:
        raise RuntimeError(
            f"Failed to make s3 storage the active default storage type!"
        )

    logger.info(f"Successfully made s3 storage the active default storage type")
