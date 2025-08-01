from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    DataCategoryNotSupported,
    PolicyValidationError,
    RuleValidationError,
    StorageConfigNotFoundException,
)
from fides.api.models.client import ClientDetail
from fides.api.models.policy import (
    ActionType,
    Policy,
    Rule,
    RuleTarget,
    _is_ancestor_of_contained_categories,
)
from fides.api.models.storage import StorageConfig
from fides.api.schemas.masking.masking_secrets import MaskingSecretCache, SecretType
from fides.api.service.masking.strategy.masking_strategy_hash import HashMaskingStrategy
from fides.api.service.masking.strategy.masking_strategy_hmac import HmacMaskingStrategy
from fides.api.service.masking.strategy.masking_strategy_nullify import (
    NullMaskingStrategy,
)
from fides.api.util.data_category import DataCategory
from fides.api.util.text import to_snake_case


def test_policy_sets_slug(
    db: Session,
    oauth_client: ClientDetail,
) -> None:
    NAME = "policy"
    policy = Policy.create(
        db=db,
        data={
            "name": NAME,
            "client_id": oauth_client.id,
        },
    )
    assert policy.key == to_snake_case(NAME)
    policy.delete(db=db)


def test_policy_wont_override_slug(
    db: Session,
    oauth_client: ClientDetail,
) -> None:
    slug = "something_different"
    policy = Policy.create(
        db=db,
        data={
            "name": "another policy",
            "key": slug,
            "client_id": oauth_client.id,
        },
    )
    assert policy.key == slug
    policy.delete(db=db)


def test_get_action_type(
    policy: Policy,
    empty_policy: Policy,
    erasure_policy: Policy,
) -> None:
    assert policy.get_action_type() == ActionType.access
    assert erasure_policy.get_action_type() == ActionType.erasure
    assert empty_policy.get_action_type() is None


def test_save_policy_doesnt_update_slug(db: Session, policy: Policy) -> None:
    existing_slug = policy.key
    new_name = "here is another test name"
    policy.name = new_name
    policy = policy.save(db=db)
    assert policy.key == existing_slug


def test_delete_policy_cascades(db: Session, policy: Policy) -> None:
    rule = policy.rules[0]
    target = rule.targets[0]
    policy.delete(db=db)
    assert Rule.get(db=db, object_id=rule.id) is None
    assert RuleTarget.get(db=db, object_id=target.id) is None
    assert Policy.get(db=db, object_id=policy.id) is None


def test_create_erasure_rule_with_destination_is_invalid(
    db: Session,
    policy: Policy,
) -> None:
    with pytest.raises(RuleValidationError) as exc:
        Rule.create(
            db=db,
            data={
                "action_type": ActionType.erasure.value,
                "client_id": policy.client_id,
                "name": "Invalid Rule",
                "policy_id": policy.id,
                "storage_destination_id": policy.rules[0].storage_destination.id,
                "masking_strategy": {
                    "strategy": HashMaskingStrategy.name,
                    "configuration": {
                        "algorithm": "SHA-512",
                        "format_preservation": {"suffix": "@masked.com"},
                    },
                },
            },
        )
    assert exc.value.args[0] == "Erasure Rules cannot have storage destinations."


def test_create_erasure_rule_with_no_masking_strategy_is_invalid(
    db: Session,
    policy: Policy,
) -> None:
    with pytest.raises(RuleValidationError) as exc:
        Rule.create(
            db=db,
            data={
                "action_type": ActionType.erasure.value,
                "client_id": policy.client_id,
                "name": "Invalid Rule",
                "policy_id": policy.id,
            },
        )
    assert exc.value.args[0] == "Erasure Rules must have masking strategies."


def test_create_rule_no_action_is_invalid(
    db: Session,
    policy: Policy,
) -> None:
    with pytest.raises(RuleValidationError) as exc:
        Rule.create(
            db=db,
            data={
                "client_id": policy.client_id,
                "name": "Invalid Rule",
                "policy_id": policy.id,
                "storage_destination_id": policy.rules[0].storage_destination.id,
            },
        )
    assert exc.value.args[0] == "action_type is required."


def test_update_action_is_unsupported(
    db: Session,
    policy: Policy,
) -> None:
    with pytest.raises(RuleValidationError) as exc:
        Rule.create(
            db=db,
            data={
                "action_type": ActionType.update.value,
                "client_id": policy.client_id,
                "name": "Invalid Rule",
                "policy_id": policy.id,
                "storage_destination_id": policy.rules[0].storage_destination.id,
            },
        )
    assert exc.value.args[0] == "update Rules are not supported at this time."


def test_create_access_rule(
    db: Session,
    policy: Policy,
) -> None:
    rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.access.value,
            "client_id": policy.client_id,
            "name": "Valid Access Rule",
            "policy_id": policy.id,
            "storage_destination_id": policy.rules[0].storage_destination.id,
        },
    )
    assert Rule.get(db=db, object_id=rule.id) is not None
    rule.delete(db=db)


def test_create_erasure_rule(
    db: Session,
    policy: Policy,
) -> None:
    rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": policy.client_id,
            "name": "Valid Erasure Rule",
            "policy_id": policy.id,
            "masking_strategy": {
                "strategy": NullMaskingStrategy.name,
                "configuration": {},
            },
        },
    )
    assert Rule.get(db=db, object_id=rule.id) is not None
    rule.delete(db=db)


def test_create_rule_target_invalid_data_category(
    db: Session,
    policy: Policy,
) -> None:
    with pytest.raises(DataCategoryNotSupported) as exc:
        RuleTarget.create(
            db=db,
            data={
                "client_id": policy.client.id,
                "data_category": "a_fake_category",
                "name": "a target",
                "rule_id": policy.rules[0].id,
            },
        )

    assert exc.value.__class__ == DataCategoryNotSupported
    assert (
        exc.value.args[0]
        == "The data category 'a_fake_category' was not found in the database, and is therefore not valid for use here."
    )


def test_create_rule_target_valid_data_category(
    db: Session,
    policy: Policy,
) -> None:
    target = RuleTarget.create(
        db=db,
        data={
            "client_id": policy.client.id,
            "data_category": DataCategory("user.contact.email").value,
            "rule_id": policy.rules[0].id,
        },
    )
    assert RuleTarget.get(db=db, object_id=target.id) is not None
    target.delete(db=db)


def test_create_access_rule_with_no_storage_destination_is_valid(
    db: Session,
    policy: Policy,
    storage_config_default_local: StorageConfig,
) -> None:
    rule: Rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.access.value,
            "client_id": policy.client_id,
            "name": "Invalid Rule",
            "policy_id": policy.id,
        },
    )
    rule_storage_config = rule.get_storage_destination(db)
    assert rule_storage_config == storage_config_default_local


def test_ancestor_detection(fideslang_data_categories):
    is_ancestor, _ = _is_ancestor_of_contained_categories(
        fides_key="user.contact.email",
        data_categories=[
            "user",
        ],
        all_categories=fideslang_data_categories,
    )
    # "user.contact.email" is a descendent of
    # "user"
    assert is_ancestor

    is_ancestor, _ = _is_ancestor_of_contained_categories(
        fides_key="user.contact.email",
        data_categories=[
            "user.account",
        ],
        all_categories=fideslang_data_categories,
    )
    # "user.contact.email" is not a descendent of
    # "user.account"
    assert not is_ancestor

    is_ancestor, _ = _is_ancestor_of_contained_categories(
        fides_key="user.contact.email",
        data_categories=[
            "user.contact.email",
        ],
        all_categories=fideslang_data_categories,
    )
    # "user.contact.email" is not a descendent of
    # itself
    assert not is_ancestor


def test_validate_policy(
    oauth_client: ClientDetail,
    db: Session,
) -> None:
    erasure_policy = Policy.create(
        db=db,
        data={
            "name": "example erasure policy",
            "key": "example_erasure_policy",
            "client_id": oauth_client.id,
        },
    )

    erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": NullMaskingStrategy.name,
                "configuration": {},
            },
        },
    )
    RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user").value,
            "name": "all user data",
            "rule_id": erasure_rule.id,
        },
    )

    another_erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "Another Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": NullMaskingStrategy.name,
                "configuration": {},
            },
        },
    )
    with pytest.raises(PolicyValidationError):
        RuleTarget.create(
            db=db,
            data={
                "client_id": erasure_policy.client.id,
                "data_category": DataCategory("user.contact.email").value,
                "name": "all user contact emails",
                "rule_id": another_erasure_rule.id,
            },
        )

    erasure_policy.delete(db=db)  # This will tear down everything created here


def test_rule_get_storage_destination_local(
    db: Session,
    policy: Policy,
    storage_config: StorageConfig,
    storage_config_default_local: StorageConfig,
) -> None:
    """
    Test that the rule's method to retrieve a proper storage destination
    works as expected in different scenarios for a local storage config
    """
    rule: Rule = policy.rules[0]
    rule_storage_config = rule.get_storage_destination(db)
    assert rule_storage_config == storage_config

    rule.storage_destination = None
    rule_storage_config = rule.get_storage_destination(db)
    assert rule_storage_config == storage_config_default_local

    rule.storage_destination = storage_config
    rule_storage_config = rule.get_storage_destination(db)
    assert rule_storage_config == storage_config


@pytest.mark.usefixtures("set_active_storage_s3")
def test_rule_get_storage_destination_non_local(
    db: Session, policy: Policy, storage_config_default: StorageConfig
) -> None:
    """
    Tests that rule's method to retrieve a proper storage destination
    works as expected to retrieve a non-local storage config
    """
    rule: Rule = policy.rules[0]
    rule.storage_destination = None
    rule_storage_config = rule.get_storage_destination(db)

    assert rule_storage_config == storage_config_default


@pytest.mark.usefixtures("set_active_storage_s3")
def test_rule_get_storage_destination_not_found(
    db: Session,
    policy: Policy,
) -> None:
    """
    Tests that rule's method to retrieve a proper storage destination
    throws an error if the active default storage hasn't been configured
    """
    rule: Rule = policy.rules[0]
    rule.storage_destination = None

    with pytest.raises(StorageConfigNotFoundException):
        rule.get_storage_destination(db)


def test_policy_generate_masking_secrets_accumulates_from_multiple_strategies(
    db: Session, oauth_client: ClientDetail
):
    """
    Test that generate_masking_secrets correctly accumulates secrets when a policy
    has multiple erasure rules, each using a different masking strategy that requires secrets.
    """
    policy = Policy.create(
        db=db,
        data={
            "name": "Test Policy For Multiple Secrets",
            "key": "test_policy_for_multiple_secrets_key",
            "client_id": oauth_client.id,
        },
    )

    # Rule 1: Uses HashMaskingStrategy (generates 1 secret: salt)
    Rule.create(
        db=db,
        data={
            "policy_id": policy.id,
            "action_type": ActionType.erasure,
            "name": "Rule with Hash Strategy",
            "key": "rule_hash_strategy_for_accumulation",
            "masking_strategy": {
                "strategy": HashMaskingStrategy.name,
                "configuration": {},  # Default algorithm: SHA-256
            },
            "client_id": oauth_client.id,
        },
    )

    # Rule 2: Uses HmacMaskingStrategy (generates 2 secrets: key, salt)
    Rule.create(
        db=db,
        data={
            "policy_id": policy.id,
            "action_type": ActionType.erasure,
            "name": "Rule with HMAC Strategy",
            "key": "rule_hmac_strategy_for_accumulation",
            "masking_strategy": {
                "strategy": HmacMaskingStrategy.name,
                "configuration": {},  # Default algorithm: SHA-256
            },
            "client_id": oauth_client.id,
        },
    )

    db.refresh(policy)  # Refresh to load the policy.rules relationship

    generated_secrets = policy.generate_masking_secrets()

    assert generated_secrets is not None
    # Expected: 1 secret from HashMaskingStrategy + 2 secrets from HmacMaskingStrategy
    assert len(generated_secrets) == 3

    hash_secrets = [
        secret
        for secret in generated_secrets
        if secret.masking_strategy == HashMaskingStrategy.name
    ]
    hmac_secrets = [
        secret
        for secret in generated_secrets
        if secret.masking_strategy == HmacMaskingStrategy.name
    ]

    assert len(hash_secrets) == 1
    assert hash_secrets[0].secret_type == SecretType.salt

    assert len(hmac_secrets) == 2
    hmac_secret_types = {secret.secret_type for secret in hmac_secrets}
    assert {SecretType.key, SecretType.salt} == hmac_secret_types


def test_policy_generate_masking_secrets_calls_strategy_once_for_duplicates(
    db: Session, oauth_client: ClientDetail
):
    """
    Tests that generate_masking_secrets processes a given masking strategy
    only once even if that strategy (by name) is used in multiple rules.
    """
    policy = Policy.create(
        db=db,
        data={
            "name": "Test Policy Unique Strategy Call",
            "key": "test_policy_unique_strategy_call_key",
            "client_id": oauth_client.id,
        },
    )

    # Both rules use HashMaskingStrategy.
    # The de-duplication is by strategy_name, so even if configurations were different,
    # secret generation for HashMaskingStrategy would only occur once.
    hash_strategy_config = {
        "strategy": HashMaskingStrategy.name,
        "configuration": {"algorithm": "SHA-256"},
    }

    Rule.create(
        db=db,
        data={
            "policy_id": policy.id,
            "action_type": ActionType.erasure,
            "name": "Rule 1 Same Hash Strategy",
            "key": "rule_1_same_hash_strategy_unique_test",
            "masking_strategy": hash_strategy_config,
            "client_id": oauth_client.id,
        },
    )

    Rule.create(
        db=db,
        data={
            "policy_id": policy.id,
            "action_type": ActionType.erasure,
            "name": "Rule 2 Same Hash Strategy",
            "key": "rule_2_same_hash_strategy_unique_test",
            "masking_strategy": hash_strategy_config,  # Using the same strategy name and config
            "client_id": oauth_client.id,
        },
    )

    db.refresh(policy)

    generated_secrets = policy.generate_masking_secrets()

    # HashMaskingStrategy.generate_secrets_for_cache() returns a list with 1 MaskingSecretCache (for the salt).
    # If de-duplication by strategy_name works, we expect only 1 salt for HashMaskingStrategy.
    # If de-duplication FAILED, generate_secrets_for_cache would be called for each rule,
    # and we'd get 2 salts if using HashMaskingStrategy in both.
    assert generated_secrets is not None
    assert len(generated_secrets) == 1

    # Verify it's the correct secret from HashMaskingStrategy
    assert generated_secrets[0].masking_strategy == HashMaskingStrategy.name
    assert generated_secrets[0].secret_type == SecretType.salt
    assert isinstance(generated_secrets[0].secret, str)


# using mocks to avoid a more complicated setup of Policy and TraversalNode fixtures
class TestPolicyAppliesTo:
    def test_applies_to_exact_match(self):
        mock_node = Mock()
        mock_node.get_data_categories.return_value = {"user.contact"}

        policy = Policy()
        policy.get_access_target_categories = Mock(return_value=["user.contact"])
        policy.get_erasure_target_categories = Mock(return_value=[])

        assert policy.applies_to(mock_node) is True

    def test_applies_to_prefix_match(self):
        mock_node = Mock()
        mock_node.get_data_categories.return_value = {"user.contact.email"}

        policy = Policy()
        policy.get_access_target_categories = Mock(return_value=["user.contact"])
        policy.get_erasure_target_categories = Mock(return_value=[])

        assert policy.applies_to(mock_node) is True

    def test_does_not_apply_to_different_category(self):
        mock_node = Mock()
        mock_node.get_data_categories.return_value = {"system.operations"}

        policy = Policy()
        policy.get_access_target_categories = Mock(return_value=["user.contact"])
        policy.get_erasure_target_categories = Mock(return_value=[])

        assert policy.applies_to(mock_node) is False

    def test_applies_to_either_access_or_erasure_categories(self):
        mock_node = Mock()
        mock_node.get_data_categories.return_value = {"user.preferences"}

        policy = Policy()
        policy.get_access_target_categories = Mock(return_value=["user.contact"])
        policy.get_erasure_target_categories = Mock(return_value=["user.preferences"])

        assert policy.applies_to(mock_node) is True

    def test_applies_to_multiple_node_categories(self):
        mock_node = Mock()
        mock_node.get_data_categories.return_value = {
            "system.operations",
            "user.contact.email",
        }

        policy = Policy()
        policy.get_access_target_categories = Mock(return_value=["user.contact"])
        policy.get_erasure_target_categories = Mock(return_value=[])

        assert policy.applies_to(mock_node) is True

    def test_applies_to_multiple_target_categories(self):
        mock_node = Mock()
        mock_node.get_data_categories.return_value = {"system.operations"}

        policy = Policy()
        policy.get_access_target_categories = Mock(
            return_value=["user.contact", "system"]
        )
        policy.get_erasure_target_categories = Mock(return_value=[])

        assert policy.applies_to(mock_node) is True

    def test_applies_to_empty_node_categories(self):
        mock_node = Mock()
        mock_node.get_data_categories.return_value = set()

        policy = Policy()
        policy.get_access_target_categories = Mock(return_value=["user.contact"])
        policy.get_erasure_target_categories = Mock(return_value=[])

        assert policy.applies_to(mock_node) is False

    def test_applies_to_empty_target_categories(self):
        mock_node = Mock()
        mock_node.get_data_categories.return_value = {"user.contact"}

        policy = Policy()
        policy.get_access_target_categories = Mock(return_value=[])
        policy.get_erasure_target_categories = Mock(return_value=[])

        assert policy.applies_to(mock_node) is False
