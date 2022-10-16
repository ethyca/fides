import logging
from typing import Dict

import requests

from fides.api.ops.api.v1 import urn_registry as urls

from . import constants

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_dsr_policy(
    auth_header: Dict[str, str],
    key: str = constants.ACCESS_POLICY_KEY,
    execution_timeframe: int = 45,
):
    policy_create_data = [
        {
            "name": key,
            "key": key,
            "execution_timeframe": execution_timeframe,
        },
    ]
    response = requests.patch(
        f"{constants.BASE_URL}{urls.POLICY_LIST}",
        headers=auth_header,
        json=policy_create_data,
    )

    if response.ok:
        policies = (response.json())["succeeded"]
        if len(policies) > 0:
            logger.info(
                "Created or updated fides policy with key=%s via /api/v1/policy", key
            )
            return

    raise RuntimeError(
        f"fides policy creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


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
