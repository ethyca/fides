import pytest
from sqlalchemy.orm import Session

from fidesops.common_exceptions import (
    DataCategoryNotSupported,
    PolicyValidationError,
    RuleValidationError,
)
from fidesops.models.client import ClientDetail
from fidesops.models.policy import (
    ActionType,
    Policy,
    Rule,
    RuleTarget,
    _is_ancestor_of_contained_categories,
)
from fidesops.service.masking.strategy.masking_strategy_hash import HASH
from fidesops.service.masking.strategy.masking_strategy_nullify import NULL_REWRITE
from fidesops.util.text import to_snake_case
from fidesops.util.data_category import DataCategory


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
    assert Rule.get(db=db, id=rule.id) is None
    assert RuleTarget.get(db=db, id=target.id) is None
    assert Policy.get(db=db, id=policy.id) is None


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
                    "strategy": HASH,
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


def test_create_access_rule_with_no_storage_destination_is_invalid(
    db: Session,
    policy: Policy,
) -> None:
    with pytest.raises(RuleValidationError) as exc:
        Rule.create(
            db=db,
            data={
                "action_type": ActionType.access.value,
                "client_id": policy.client_id,
                "name": "Invalid Rule",
                "policy_id": policy.id,
            },
        )
    assert exc.value.args[0] == "Access Rules must have a storage destination."


def test_consent_action_is_unsupported(
    db: Session,
    policy: Policy,
) -> None:
    with pytest.raises(RuleValidationError) as exc:
        Rule.create(
            db=db,
            data={
                "action_type": ActionType.consent.value,
                "client_id": policy.client_id,
                "name": "Invalid Rule",
                "policy_id": policy.id,
                "storage_destination_id": policy.rules[0].storage_destination.id,
            },
        )
    assert exc.value.args[0] == "consent Rules are not supported at this time."


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
    assert Rule.get(db=db, id=rule.id) is not None
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
                "strategy": NULL_REWRITE,
                "configuration": {},
            },
        },
    )
    assert Rule.get(db=db, id=rule.id) is not None
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
    assert exc.value.args[0] == "The data category a_fake_category is not supported."


def test_create_rule_target_valid_data_category(
    db: Session,
    policy: Policy,
) -> None:
    target = RuleTarget.create(
        db=db,
        data={
            "client_id": policy.client.id,
            "data_category": DataCategory(
                "user.provided.identifiable.contact.email"
            ).value,
            "rule_id": policy.rules[0].id,
        },
    )
    assert RuleTarget.get(db=db, id=target.id) is not None
    target.delete(db=db)


def test_ancestor_detection():
    is_ancestor, _ = _is_ancestor_of_contained_categories(
        fides_key="user.provided.identifiable.contact.email",
        data_categories=[
            "user.provided.identifiable",
        ],
    )
    # "user.provided.identifiable.contact.email" is a descendent of
    # "user.provided.identifiable"
    assert is_ancestor

    is_ancestor, _ = _is_ancestor_of_contained_categories(
        fides_key="user.provided.identifiable.contact.email",
        data_categories=[
            "user.provided.nonidentifiable",
        ],
    )
    # "user.provided.identifiable.contact.email" is not a descendent of
    # "user.provided.nonidentifiable"
    assert not is_ancestor

    is_ancestor, _ = _is_ancestor_of_contained_categories(
        fides_key="user.provided.identifiable.contact.email",
        data_categories=[
            "user.provided.identifiable.contact.email",
        ],
    )
    # "user.provided.identifiable.contact.email" is not a descendent of
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
                "strategy": NULL_REWRITE,
                "configuration": {},
            },
        },
    )
    RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.provided.identifiable").value,
            "name": "all user provided identifiable data",
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
                "strategy": NULL_REWRITE,
                "configuration": {},
            },
        },
    )
    with pytest.raises(PolicyValidationError):
        RuleTarget.create(
            db=db,
            data={
                "client_id": erasure_policy.client.id,
                "data_category": DataCategory(
                    "user.provided.identifiable.contact.email"
                ).value,
                "name": "all user provided contact emails",
                "rule_id": another_erasure_rule.id,
            },
        )

    erasure_policy.delete(db=db)  # This will tear down everything created here
