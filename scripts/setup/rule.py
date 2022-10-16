import logging
from typing import Dict

import requests

from fides.api.ops.api.v1 import urn_registry as urls

from . import constants

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_rule(
    auth_header: Dict[str, str],
    policy_key: str = constants.ACCESS_POLICY_KEY,
    rule_key: str = constants.ACCESS_RULE_KEY,
    storage_key: str = constants.STORAGE_KEY,
    action_type: str = "access",
):
    rules = [
        {
            "storage_destination_key": storage_key,
            "name": f"My User Data {action_type}",
            "action_type": action_type,
            "key": rule_key,
        },
    ]

    if action_type == "erasure":
        rules[0]["masking_strategy"] = {
            "strategy": "hmac",
            "configuration": {},
        }

    url = urls.RULE_LIST.format(policy_key=policy_key)
    response = requests.patch(
        f"{constants.BASE_URL}{url}",
        headers=auth_header,
        json=rules,
    )

    if response.ok:
        rules = (response.json())["succeeded"]
        if len(rules) > 0:
            logger.info(
                "Created or updated fides rule with key=%s via %s", rule_key, url
            )
            return

    raise RuntimeError(
        f"fides rule creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )
