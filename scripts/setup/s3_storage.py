import logging
from typing import Dict

import requests

from fides.api.ops.api.v1 import urn_registry as urls

from . import constants, get_secret
from .policy import create_policy

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_s3_storage(
    auth_header: Dict[str, str],
    key: str = constants.STORAGE_KEY,
    policy_key: str = constants.ACCESS_POLICY_KEY,
):
    logger.info(f"Configuring S3 storage for policy {policy_key}")
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
                    "bucket": "subjectrequests",
                    "object_name": "test_name",
                },
            },
        ],
    )

    if not response.ok:
        raise RuntimeError(
            f"fides storage creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )
    else:
        storage = (response.json())["succeeded"]
        if len(storage) > 0:
            logger.info(f"Created fides storage with key={key} via {url}")

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
    create_policy(auth_header=auth_header, key=policy_key)

    rule_key = f"{key}_rule"
    rule_create_data = {
        "name": rule_key,
        "key": rule_key,
        "action_type": "access",
        "storage_destination_key": key,
    }

    policy_path = urls.RULE_LIST.format(policy_key=policy_key)
    url = f"{constants.BASE_URL}{policy_path}"
    response = requests.patch(
        url,
        headers=auth_header,
        json=[rule_create_data],
    )
    if not response.ok:
        raise RuntimeError(
            f"fides policy rule creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    rule_target_path = urls.RULE_TARGET_LIST.format(
        policy_key=policy_key,
        rule_key=rule_key,
    )
    url = f"{constants.BASE_URL}{rule_target_path}"
    data_category = "user"
    response = requests.patch(
        url,
        headers=auth_header,
        json=[{"data_category": data_category}],
    )

    if response.ok:
        targets = (response.json())["succeeded"]
        if len(targets) > 0:
            logger.info(
                f"Created fides policy rule target for '{data_category}' via {url}"
            )
