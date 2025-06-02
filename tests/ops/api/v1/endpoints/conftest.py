from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.client import ClientDetail
from fides.api.models.policy import ActionType, Policy, Rule, RuleTarget
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.models.storage import StorageConfig
from fides.api.schemas.masking.masking_configuration import (
    AesEncryptionMaskingConfiguration,
)
from fides.api.service.masking.strategy.masking_strategy_aes_encrypt import (
    AesEncryptionMaskingStrategy,
)
from fides.api.service.masking.strategy.masking_strategy_string_rewrite import (
    StringRewriteMaskingStrategy,
)
from fides.api.util.data_category import DataCategory
from tests.fixtures.application_fixtures import _create_privacy_request_for_policy


@pytest.fixture(scope="function")
def policy_drp_action(
    db: Session,
    oauth_client: ClientDetail,
    storage_config: StorageConfig,
    default_data_categories,  # This needs to be explicitly passed in to ensure data categories are available
) -> Generator:

    access_request_policy = Policy.create(
        db=db,
        data={
            "name": "example access request policy drp",
            "key": "example_access_request_policy_drp",
            "drp_action": "access",
            "client_id": oauth_client.id,
        },
    )

    access_request_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.access.value,
            "client_id": oauth_client.id,
            "name": "Access Request Rule DRP",
            "policy_id": access_request_policy.id,
            "storage_destination_id": storage_config.id,
        },
    )

    RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user").value,
            "rule_id": access_request_rule.id,
        },
    )
    yield access_request_policy


@pytest.fixture(scope="function")
def policy_drp_action_erasure(
    db: Session,
    oauth_client: ClientDetail,
    default_data_categories,  # This needs to be explicitly passed in to ensure data categories are available
) -> Generator:
    erasure_request_policy = Policy.create(
        db=db,
        data={
            "name": "example erasure request policy drp",
            "key": "example_erasure_request_policy_drp",
            "drp_action": "deletion",
            "client_id": oauth_client.id,
        },
    )

    erasure_request_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "Erasure Request Rule DRP",
            "policy_id": erasure_request_policy.id,
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"rewrite_value": "MASKED"},
            },
        },
    )

    RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user").value,
            "rule_id": erasure_request_rule.id,
        },
    )
    yield erasure_request_policy


@pytest.fixture(scope="function")
def policy_drp_action_erasure_aes(
    db: Session,
    oauth_client: ClientDetail,
    default_data_categories,  # This needs to be explicitly passed in to ensure data categories are available
) -> Generator:
    erasure_request_policy = Policy.create(
        db=db,
        data={
            "name": "example erasure request policy drp aes",
            "key": "example_erasure_request_policy_drp_aes",
            "drp_action": "deletion",
            "client_id": oauth_client.id,
        },
    )

    erasure_request_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "Erasure Request Rule DRP AES",
            "policy_id": erasure_request_policy.id,
            "masking_strategy": {
                "strategy": AesEncryptionMaskingStrategy.name,
                "configuration": {
                    "mode": AesEncryptionMaskingConfiguration.Mode.GCM.value
                },
            },
        },
    )

    RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user").value,
            "rule_id": erasure_request_rule.id,
        },
    )
    yield erasure_request_policy


@pytest.fixture(scope="function")
def privacy_request_with_drp_action(
    db: Session, policy_drp_action: Policy
) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy_drp_action,
    )
    return privacy_request
