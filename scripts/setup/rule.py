import logging
from typing import Dict

import requests
import setup.constants as constants

from fides.api.ops.api.v1 import urn_registry as urls

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_rule(
    auth_header: Dict[str, str],
    policy_key: str = constants.ACCESS_POLICY_KEY,
    rule_key: str = constants.ACCESS_RULE_KEY,
    storage_key: str = constants.STORAGE_KEY,
    action_type: str = "access",
):
    policy_rules = [
        {
            "storage_destination_key": storage_key,
            "name": f"My User Data {action_type}",
            "action_type": action_type,
            "key": rule_key,
        },
    ]

    if action_type == "erasure":
        policy_rules[0]["masking_strategy"] = {
            "strategy": "null_rewrite",
            "configuration": {},
        }

    url = urls.RULE_LIST.format(policy_key=policy_key)
    response = requests.patch(
        f"{constants.BASE_URL}{url}",
        headers=auth_header,
        json=policy_rules,
    )

    if response.ok:
        policies = (response.json())["succeeded"]
        if len(policies) > 0:
            logger.info(
                "Created or updated fides rule with key=%s via %s", rule_key, url
            )
            return

    raise RuntimeError(
        f"fides rule creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )
