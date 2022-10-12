import logging
from typing import Dict

import requests
import setup.constants as constants

from fides.api.ops.api.v1 import urn_registry as urls

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_rule_target(
    auth_header: Dict[str, str],
    policy_key: str = constants.ACCESS_POLICY_KEY,
    rule_key: str = constants.ACCESS_RULE_KEY,
    target_key: str = "target",
    data_category: str = "user",
):
    policy_rules = [
        {
            "data_category": data_category,
            "key": target_key,
            "name": f"Rule Target - {policy_key} - {rule_key}",
        }
    ]

    url = urls.RULE_TARGET_LIST.format(policy_key=policy_key, rule_key=rule_key)
    response = requests.patch(
        f"{constants.BASE_URL}{url}",
        headers=auth_header,
        json=policy_rules,
    )

    if response.ok:
        policies = (response.json())["succeeded"]
        if len(policies) > 0:
            logger.info(
                "Created or updated fides rule target with key=%s via %s",
                target_key,
                url,
            )
            return

    raise RuntimeError(
        f"fides rule target creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )
