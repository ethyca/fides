from typing import Generator

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

from fides.api.models.client import ClientDetail
from fides.api.models.policy import ActionType, Policy, Rule, RuleTarget
from fides.api.models.storage import StorageConfig
from fides.api.util.data_category import DataCategory, get_user_data_categories
from fides.service.privacy_request.masking.strategy.masking_strategy_hmac import (
    HmacMaskingStrategy,
)
from fides.service.privacy_request.masking.strategy.masking_strategy_nullify import (
    NullMaskingStrategy,
)
from fides.service.privacy_request.masking.strategy.masking_strategy_random_string_rewrite import (
    RandomStringRewriteMaskingStrategy,
)
from fides.service.privacy_request.masking.strategy.masking_strategy_string_rewrite import (
    StringRewriteMaskingStrategy,
)


@pytest.fixture(scope="function")
def access_and_erasure_policy(
    db: Session,
    oauth_client: ClientDetail,
    storage_config: StorageConfig,
) -> Generator:
    access_and_erasure_policy = Policy.create(
        db=db,
        data={
            "name": "example access and erasure policy",
            "key": "example_access_erasure_policy",
            "client_id": oauth_client.id,
        },
    )
    access_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.access.value,
            "client_id": oauth_client.id,
            "name": "Access Request Rule",
            "policy_id": access_and_erasure_policy.id,
            "storage_destination_id": storage_config.id,
        },
    )
    access_rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user").value,
            "rule_id": access_rule.id,
        },
    )
    erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "Erasure Rule",
            "policy_id": access_and_erasure_policy.id,
            "masking_strategy": {
                "strategy": "null_rewrite",
                "configuration": {},
            },
        },
    )

    erasure_rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.name").value,
            "rule_id": erasure_rule.id,
        },
    )
    yield access_and_erasure_policy
    try:
        access_rule_target.delete(db)
        erasure_rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        access_rule.delete(db)
        erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        access_and_erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_policy(
    db: Session,
    oauth_client: ClientDetail,
    default_data_categories,  # This needs to be explicitly passed in to ensure data categories are available
) -> Generator:
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
                "strategy": "null_rewrite",
                "configuration": {},
            },
        },
    )

    rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.name").value,
            "rule_id": erasure_rule.id,
        },
    )

    yield erasure_policy
    try:
        rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_policy_address_city(
    db: Session,
    oauth_client: ClientDetail,
) -> Generator:
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
                "strategy": "null_rewrite",
                "configuration": {},
            },
        },
    )

    rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.contact.address.city").value,
            "rule_id": erasure_rule.id,
        },
    )

    yield erasure_policy
    try:
        rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def biquery_erasure_policy(
    db: Session,
    oauth_client: ClientDetail,
) -> Generator:
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
                "strategy": "null_rewrite",
                "configuration": {},
            },
        },
    )

    user_name_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.name").value,
            "rule_id": erasure_rule.id,
        },
    )
    street_address_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.contact.address.street").value,
            "rule_id": erasure_rule.id,
        },
    )
    yield erasure_policy
    try:
        user_name_target.delete(db)
        street_address_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def bigquery_enterprise_erasure_policy(
    db: Session,
    oauth_client: ClientDetail,
) -> Generator:
    erasure_policy = Policy.create(
        db=db,
        data={
            "name": "example enterprise erasure policy",
            "key": "example_enterprise_erasure_policy",
            "client_id": oauth_client.id,
        },
    )

    erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "Erasure Rule Enterprise",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": "null_rewrite",
                "configuration": {},
            },
        },
    )

    user_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.contact").value,
            "rule_id": erasure_rule.id,
        },
    )
    yield erasure_policy
    try:
        user_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_policy_aes(
    db: Session,
    oauth_client: ClientDetail,
    default_data_categories,  # This needs to be explicitly passed in to ensure data categories are available
) -> Generator:
    erasure_policy = Policy.create(
        db=db,
        data={
            "name": "example erasure policy aes",
            "key": "example_erasure_policy_aes",
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
                "strategy": "aes_encrypt",
                "configuration": {},
            },
        },
    )

    rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.name").value,
            "rule_id": erasure_rule.id,
        },
    )
    yield erasure_policy
    try:
        rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_policy_string_rewrite_long(
    db: Session,
    oauth_client: ClientDetail,
) -> Generator:
    erasure_policy = Policy.create(
        db=db,
        data={
            "name": "example erasure policy string rewrite",
            "key": "example_erasure_policy_string_rewrite",
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
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {
                    "rewrite_value": "some rewrite value that is very long and goes on and on"
                },
            },
        },
    )

    rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.name").value,
            "rule_id": erasure_rule.id,
        },
    )
    yield erasure_policy
    try:
        rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_policy_two_rules(
    db: Session, oauth_client: ClientDetail, erasure_policy: Policy
) -> Generator:
    second_erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "Second Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": NullMaskingStrategy.name,
                "configuration": {},
            },
        },
    )

    # TODO set masking strategy in Rule.create() call above, once more masking strategies beyond NULL_REWRITE are supported.
    second_erasure_rule.masking_strategy = {
        "strategy": StringRewriteMaskingStrategy.name,
        "configuration": {"rewrite_value": "*****"},
    }

    second_rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.contact.email").value,
            "rule_id": second_erasure_rule.id,
        },
    )
    yield erasure_policy
    try:
        second_rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        second_erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_policy_all_categories(
    db: Session,
    oauth_client: ClientDetail,
) -> Generator:
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
                "strategy": "null_rewrite",
                "configuration": {},
            },
        },
    )

    filtered_categories = get_user_data_categories()
    rule_targets = []

    for category in filtered_categories:
        rule_targets.append(
            RuleTarget.create(
                db=db,
                data={
                    "client_id": oauth_client.id,
                    "data_category": category,
                    "rule_id": erasure_rule.id,
                },
            )
        )
    yield erasure_policy
    try:
        for rule_target in rule_targets:
            rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def empty_policy(
    db: Session,
    oauth_client: ClientDetail,
) -> Generator:
    policy = Policy.create(
        db=db,
        data={
            "name": "example empty policy",
            "key": "example_empty_policy",
            "client_id": oauth_client.id,
        },
    )
    yield policy
    try:
        policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def policy(
    db: Session,
    oauth_client: ClientDetail,
    storage_config: StorageConfig,
    default_data_categories,  # This needs to be explicitly passed in to ensure data categories are available
) -> Generator:
    access_request_policy = Policy.create(
        db=db,
        data={
            "name": "example access request policy",
            "key": "example_access_request_policy",
            "client_id": oauth_client.id,
            "execution_timeframe": 7,
        },
    )

    access_request_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.access.value,
            "client_id": oauth_client.id,
            "name": "Access Request Rule",
            "policy_id": access_request_policy.id,
            "storage_destination_id": storage_config.id,
        },
    )

    rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user").value,
            "rule_id": access_request_rule.id,
        },
    )
    yield access_request_policy
    try:
        rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        access_request_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        access_request_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def consent_policy(
    db: Session,
    oauth_client: ClientDetail,
) -> Generator:
    """Consent policies only need a ConsentRule attached - no RuleTargets necessary"""
    consent_request_policy = Policy.create(
        db=db,
        data={
            "name": "example consent request policy",
            "key": "example_consent_request_policy",
            "client_id": oauth_client.id,
        },
    )

    consent_request_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.consent.value,
            "client_id": oauth_client.id,
            "name": "Consent Request Rule",
            "policy_id": consent_request_policy.id,
        },
    )

    yield consent_request_policy
    try:
        consent_request_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        consent_request_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def policy_local_storage(
    db: Session,
    oauth_client: ClientDetail,
    storage_config_local: StorageConfig,
    default_data_categories,  # This needs to be explicitly passed in to ensure data categories are available
) -> Generator:
    """
    A basic example policy fixture that uses a local storage config
    in cases where end-to-end request execution must actually succeed
    """
    access_request_policy = Policy.create(
        db=db,
        data={
            "name": "example access request policy",
            "key": "example_access_request_policy",
            "client_id": oauth_client.id,
            "execution_timeframe": 7,
        },
    )

    access_request_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.access.value,
            "client_id": oauth_client.id,
            "name": "Access Request Rule",
            "policy_id": access_request_policy.id,
            "storage_destination_id": storage_config_local.id,
        },
    )

    rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user").value,
            "rule_id": access_request_rule.id,
        },
    )
    yield access_request_policy
    try:
        rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        access_request_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        access_request_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_policy_string_rewrite(
    db: Session,
    oauth_client: ClientDetail,
    default_data_categories,  # This needs to be explicitly passed in to ensure data categories are available
) -> Generator:
    erasure_policy = Policy.create(
        db=db,
        data={
            "name": "string rewrite policy",
            "key": "string_rewrite_policy",
            "client_id": oauth_client.id,
        },
    )

    erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "string rewrite erasure rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"rewrite_value": "MASKED"},
            },
        },
    )

    erasure_rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.name").value,
            "rule_id": erasure_rule.id,
        },
    )

    yield erasure_policy
    try:
        erasure_rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_policy_string_rewrite_address(
    db: Session,
    oauth_client: ClientDetail,
    storage_config: StorageConfig,
) -> Generator:
    erasure_policy = Policy.create(
        db=db,
        data={
            "name": "string rewrite policy",
            "key": "string_rewrite_policy",
            "client_id": oauth_client.id,
        },
    )

    erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "string rewrite erasure rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"rewrite_value": "MASKED"},
            },
        },
    )

    erasure_rule_targets = []
    erasure_rule_targets.append(
        RuleTarget.create(
            db=db,
            data={
                "client_id": oauth_client.id,
                "data_category": DataCategory("user.name").value,
                "rule_id": erasure_rule.id,
            },
        )
    )
    erasure_rule_targets.append(
        RuleTarget.create(
            db=db,
            data={
                "client_id": oauth_client.id,
                "data_category": DataCategory("user.contact.address").value,
                "rule_id": erasure_rule.id,
            },
        )
    )
    erasure_rule_targets.append(
        RuleTarget.create(
            db=db,
            data={
                "client_id": oauth_client.id,
                "data_category": DataCategory("user.contact.phone_number").value,
                "rule_id": erasure_rule.id,
            },
        )
    )
    yield erasure_policy
    try:
        for erasure_rule_target in erasure_rule_targets:
            erasure_rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_policy_string_rewrite_name_and_email(
    db: Session,
    oauth_client: ClientDetail,
    storage_config: StorageConfig,
) -> Generator:
    erasure_policy = Policy.create(
        db=db,
        data={
            "name": "string rewrite policy",
            "key": "string_rewrite_policy",
            "client_id": oauth_client.id,
        },
    )

    string_erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "string rewrite erasure rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"rewrite_value": "MASKED"},
            },
        },
    )

    email_erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "email rewrite erasure rule rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": RandomStringRewriteMaskingStrategy.name,
                "configuration": {
                    "length": 20,
                    "format_preservation": {"suffix": "@email.com"},
                },
            },
        },
    )

    erasure_rule_target_name = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.name").value,
            "rule_id": string_erasure_rule.id,
        },
    )

    erasure_rule_target_email = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.contact.email").value,
            "rule_id": email_erasure_rule.id,
        },
    )

    yield erasure_policy
    try:
        erasure_rule_target_name.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_rule_target_email.delete(db)
    except ObjectDeletedError:
        pass
    try:
        string_erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        email_erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_policy_hmac(
    db: Session,
    oauth_client: ClientDetail,
    storage_config: StorageConfig,
) -> Generator:
    erasure_policy = Policy.create(
        db=db,
        data={
            "name": "hmac policy",
            "key": "hmac_policy",
            "client_id": oauth_client.id,
        },
    )

    erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "hmac erasure rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": HmacMaskingStrategy.name,
                "configuration": {},
            },
        },
    )

    erasure_rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.name").value,
            "rule_id": erasure_rule.id,
        },
    )

    yield erasure_policy
    try:
        erasure_rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass
