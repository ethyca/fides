from typing import Any, Dict, Generator

import pytest
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError
from toml import load as load_toml

from fides.api.ctl.sql_models import Dataset as CtlDataset
from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.models.policy import ActionType, Policy, Rule, RuleTarget
from fides.api.ops.schemas.saas.saas_config import ParamValue
from fides.api.ops.schemas.saas.strategy_configuration import (
    OAuth2AuthorizationCodeConfiguration,
)
from fides.api.ops.service.masking.strategy.masking_strategy_nullify import (
    NullMaskingStrategy,
)
from fides.api.ops.service.masking.strategy.masking_strategy_random_string_rewrite import (
    RandomStringRewriteMaskingStrategy,
)
from fides.api.ops.service.masking.strategy.masking_strategy_string_rewrite import (
    StringRewriteMaskingStrategy,
)
from fides.api.ops.util.data_category import DataCategory
from fides.api.ops.util.saas_util import (
    encode_file_contents,
    load_as_string,
    load_config,
    load_yaml_as_string,
)
from fides.lib.models.client import ClientDetail
from tests.fixtures.application_fixtures import load_dataset


@pytest.fixture(scope="function")
def saas_example_secrets():
    return {
        "domain": "domain",
        "username": "username",
        "api_key": "api_key",
        "api_version": "2.0",
        "account_types": ["checking"],
        "page_size": "10",
        "customer_id": {  # an example external dataset reference
            "dataset": "saas_connector_external_example",
            "field": "customer_id_reference_table.customer_id",
            "direction": "from",
        },
    }


@pytest.fixture
def saas_example_config() -> Dict:
    return load_config("tests/fixtures/saas/test_data/saas_example_config.yml")


@pytest.fixture
def saas_external_example_config() -> Dict:
    return load_config("tests/fixtures/saas/test_data/saas_external_example_config.yml")


@pytest.fixture
def saas_example_dataset() -> Dict:
    return load_dataset("tests/fixtures/saas/test_data/saas_example_dataset.yml")[0]


@pytest.fixture
def saas_ctl_dataset(db: Session) -> Dict:
    dataset = load_dataset("tests/fixtures/saas/test_data/saas_example_dataset.yml")[0]
    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)
    yield ctl_dataset
    ctl_dataset.delete(db)


@pytest.fixture
def saas_external_example_dataset() -> Dict:
    return load_dataset("tests/fixtures/saas/test_data/saas_example_dataset.yml")[1]


@pytest.fixture(scope="function")
def saas_example_connection_config(
    db: Session,
    saas_example_config: Dict[str, Any],
    saas_example_secrets: Dict[str, Any],
) -> Generator:
    fides_key = saas_example_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": saas_example_secrets,
            "saas_config": saas_example_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def saas_external_example_connection_config(
    db: Session,
    saas_external_example_config: Dict[str, Any],
    saas_example_secrets: Dict[str, Any],
) -> Generator:
    fides_key = saas_external_example_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": saas_example_secrets,
            "saas_config": saas_external_example_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def saas_example_dataset_config(
    db: Session,
    saas_example_connection_config: ConnectionConfig,
    saas_example_dataset: Dict,
) -> Generator:
    fides_key = saas_example_dataset["fides_key"]
    saas_example_connection_config.name = fides_key
    saas_example_connection_config.key = fides_key
    saas_example_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, saas_example_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": saas_example_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db)


@pytest.fixture
def saas_external_example_dataset_config(
    db: Session,
    saas_external_example_connection_config: ConnectionConfig,
    saas_external_example_dataset: Dict,
) -> Generator:
    fides_key = saas_external_example_dataset["fides_key"]
    saas_external_example_connection_config.name = fides_key
    saas_external_example_connection_config.key = fides_key
    saas_external_example_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, saas_external_example_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": saas_external_example_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def saas_example_connection_config_without_saas_config(
    db: Session, saas_example_secrets
) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": "connection_config_without_saas_config",
            "name": "connection_config_without_saas_config",
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.read,
            "secrets": saas_example_secrets,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def saas_example_connection_config_with_invalid_saas_config(
    db: Session,
    saas_example_config: Dict[str, Any],
    saas_example_secrets: Dict[str, Any],
) -> Generator:
    invalid_saas_config = saas_example_config.copy()
    invalid_saas_config["endpoints"][0]["requests"]["read"]["param_values"].pop()

    # remove external reference params since we don't want to test that with this fixture
    # replace with placholder identity
    invalid_saas_config["endpoints"][6]["requests"]["read"]["param_values"].pop()
    invalid_saas_config["endpoints"][6]["requests"]["read"]["param_values"].append(
        ParamValue(name="placeholder", identity="email").dict()
    )
    invalid_saas_config["endpoints"][6]["requests"]["update"]["param_values"].pop()

    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": "connection_config_with_invalid_saas_config",
            "name": "connection_config_with_invalid_saas_config",
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.read,
            "secrets": saas_example_secrets,
            "saas_config": invalid_saas_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def oauth2_authorization_code_configuration() -> OAuth2AuthorizationCodeConfiguration:
    return {
        "authorization_request": {
            "method": "GET",
            "path": "/auth/authorize",
            "query_params": [
                {"name": "client_id", "value": "<client_id>"},
                {"name": "redirect_uri", "value": "<redirect_uri>"},
                {"name": "response_type", "value": "code"},
                {
                    "name": "scope",
                    "value": "admin.read admin.write",
                },
                {"name": "state", "value": "<state>"},
            ],
        },
        "token_request": {
            "method": "POST",
            "path": "/oauth/token",
            "headers": [
                {
                    "name": "Content-Type",
                    "value": "application/x-www-form-urlencoded",
                }
            ],
            "query_params": [
                {"name": "client_id", "value": "<client_id>"},
                {"name": "client_secret", "value": "<client_secret>"},
                {"name": "grant_type", "value": "authorization_code"},
                {"name": "code", "value": "<code>"},
                {"name": "redirect_uri", "value": "<redirect_uri>"},
            ],
        },
        "refresh_request": {
            "method": "POST",
            "path": "/oauth/token",
            "headers": [
                {
                    "name": "Content-Type",
                    "value": "application/x-www-form-urlencoded",
                }
            ],
            "query_params": [
                {"name": "client_id", "value": "<client_id>"},
                {"name": "client_secret", "value": "<client_secret>"},
                {"name": "redirect_uri", "value": "<redirect_uri>"},
                {"name": "grant_type", "value": "refresh_token"},
                {"name": "refresh_token", "value": "<refresh_token>"},
            ],
        },
    }


@pytest.fixture(scope="function")
def oauth2_authorization_code_connection_config(
    db: Session, oauth2_authorization_code_configuration
) -> Generator:
    secrets = {
        "domain": "localhost",
        "client_id": "client",
        "client_secret": "secret",
        "redirect_uri": "https://localhost/callback",
        "access_token": "access",
        "refresh_token": "refresh",
    }
    saas_config = {
        "fides_key": "oauth2_authorization_code_connector",
        "name": "OAuth2 Auth Code Connector",
        "type": "custom",
        "description": "Generic OAuth2 connector for testing",
        "version": "0.0.1",
        "connector_params": [{"name": item} for item in secrets.keys()],
        "client_config": {
            "protocol": "https",
            "host": secrets["domain"],
            "authentication": {
                "strategy": "oauth2_authorization_code",
                "configuration": oauth2_authorization_code_configuration,
            },
        },
        "endpoints": [],
        "test_request": {"method": "GET", "path": "/test"},
    }

    fides_key = saas_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": secrets,
            "saas_config": saas_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="session")
def saas_config() -> Dict[str, Any]:
    saas_config = {}
    try:
        saas_config = load_toml("saas_config.toml")
    except Exception:
        logger.info(
            "Unable to load saas_config.toml file, skipping loading of local secrets"
        )
    return saas_config


@pytest.fixture(scope="function")
def erasure_policy_complete_mask(
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

    user_device_ip_address_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "user_device_ip_address Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": NullMaskingStrategy.name,
                "configuration": {},
            },
        },
    )
    user_device_ip_address_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.device.ip_address").value,
            "rule_id": user_device_ip_address_rule.id,
        },
    )
    user_gender_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "user_gender Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"rewrite_value": "Masked"},
            },
        },
    )
    user_gender_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.gender").value,
            "rule_id": user_gender_rule.id,
        },
    )

    user_contact_address_city_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "user_contact_address_city Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"rewrite_value": "Masked"},
            },
        },
    )
    user_contact_address_city_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.contact.address.city").value,
            "rule_id": user_contact_address_city_rule.id,
        },
    )
    user_contact_address_country_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "user_contact_address_country Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"rewrite_value": "Masked"},
            },
        },
    )
    user_contact_address_country_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.contact.address.country").value,
            "rule_id": user_contact_address_country_rule.id,
        },
    )
    user_contact_email_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "user_contact_email Erasure Rule",
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
    user_contact_email_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.contact.email").value,
            "rule_id": user_contact_email_rule.id,
        },
    )
    user_contact_phone_number_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "user_contact_phone_number Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": NullMaskingStrategy.name,
                "configuration": {},
            },
        },
    )
    user_contact_phone_number_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.contact.phone_number").value,
            "rule_id": user_contact_phone_number_rule.id,
        },
    )
    user_contact_address_postal_code_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "user_contact_address_postal_code Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"rewrite_value": "99999"},
            },
        },
    )
    user_contact_address_postal_code_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.contact.address.postal_code").value,
            "rule_id": user_contact_address_postal_code_rule.id,
        },
    )
    user_contact_address_state_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "user_contact_address_state Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"rewrite_value": "Masked"},
            },
        },
    )
    user_contact_address_state_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.contact.address.state").value,
            "rule_id": user_contact_address_state_rule.id,
        },
    )
    user_contact_address_street_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "user_contact_address_street Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"rewrite_value": "Masked"},
            },
        },
    )
    user_contact_address_street_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.contact.address.street").value,
            "rule_id": user_contact_address_street_rule.id,
        },
    )
    user_date_of_birth_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "user_date_of_birth Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"rewrite_value": "1/1/1900"},
            },
        },
    )
    user_date_of_birth_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.date_of_birth").value,
            "rule_id": user_date_of_birth_rule.id,
        },
    )
    user_name_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "user_name Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"rewrite_value": "Masked"},
            },
        },
    )
    user_name_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.name").value,
            "rule_id": user_name_rule.id,
        },
    )

    yield erasure_policy

    try:
        user_device_ip_address_rule.delete(db)
        user_gender_rule.delete(db)
        user_contact_address_city_rule.delete(db)
        user_contact_address_country_rule.delete(db)
        user_contact_email_rule.delete(db)
        user_contact_phone_number_rule.delete(db)
        user_contact_address_postal_code_rule.delete(db)
        user_contact_address_state_rule.delete(db)
        user_contact_address_street_rule.delete(db)
        user_date_of_birth_rule.delete(db)
        user_name_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        user_device_ip_address_target.delete(db)
        user_gender_target.delete(db)
        user_contact_address_city_target.delete(db)
        user_contact_address_country_target.delete(db)
        user_contact_email_target.delete(db)
        user_contact_phone_number_target.delete(db)
        user_contact_address_postal_code_target.delete(db)
        user_contact_address_state_target.delete(db)
        user_contact_address_street_target.delete(db)
        user_date_of_birth_target.delete(db)
        user_name_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture
def custom_config() -> str:
    return load_yaml_as_string("tests/fixtures/saas/test_data/custom/custom_config.yml")


@pytest.fixture
def custom_dataset() -> str:
    return load_yaml_as_string(
        "tests/fixtures/saas/test_data/custom/custom_dataset.yml"
    )


@pytest.fixture
def custom_icon() -> str:
    return encode_file_contents("tests/fixtures/saas/test_data/custom/custom.svg")


@pytest.fixture
def custom_functions() -> str:
    return load_as_string("tests/fixtures/saas/test_data/custom/custom_functions.py")
