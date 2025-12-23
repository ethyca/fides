from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.db.seed import load_default_taxonomy
from fides.api.models.client import ClientDetail
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
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


@pytest.fixture(scope="function", autouse=True)
def load_default_data_categories(db: Session):
    """
    Automatically load default taxonomy for all tests in this module.
    Required for dataset validation which checks data categories against the database.
    """
    load_default_taxonomy(db)


@pytest.fixture(scope="function")
def external_user(db: Session) -> Generator[FidesUser, None, None]:
    """Create a user with external_respondent role for testing."""
    user = FidesUser.create(
        db=db,
        data={
            "username": "external_user",
            "email_address": "external@example.com",
        },
    )
    FidesUserPermissions.create(
        db=db,
        data={"user_id": user.id, "roles": ["external_respondent"]},
    )

    # Create a client for the user (required for auth header generation)
    from fides.api.models.client import ClientDetail
    from fides.config import CONFIG

    client, _ = ClientDetail.create_client_and_secret(
        db,
        CONFIG.security.oauth_client_id_length_bytes,
        CONFIG.security.oauth_client_secret_length_bytes,
        user_id=user.id,
    )

    # Refresh the user to get the client relationship
    db.refresh(user)

    yield user
    if user.permissions:
        user.permissions.delete(db)
    user.delete(db)


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
