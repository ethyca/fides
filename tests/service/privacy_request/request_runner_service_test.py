import pytest
import time
from typing import Any, Dict, List, Set
from unittest import mock
from unittest.mock import Mock
from uuid import uuid4

import pydash
from sqlalchemy import (
    column,
    table,
    select,
)
from sqlalchemy.orm import Session
from pydantic import ValidationError

from fidesops.common_exceptions import PrivacyRequestPaused, ClientUnsuccessfulException
from fidesops.core.config import config
from fidesops.models.policy import PolicyPreWebhook, ActionType
from fidesops.models.privacy_request import PrivacyRequestStatus
from fidesops.schemas.external_https import SecondPartyResponseFormat
from fidesops.db.session import get_db_session
from fidesops.models.privacy_request import PrivacyRequest, ExecutionLog
from fidesops.schemas.masking.masking_configuration import (
    HmacMaskingConfiguration,
    MaskingConfiguration,
)
from fidesops.schemas.masking.masking_secrets import MaskingSecretCache
from fidesops.schemas.policy import Rule
from fidesops.schemas.saas.shared_schemas import SaaSRequestParams, HTTPMethod
from fidesops.service.connectors.saas_connector import SaaSConnector
from fidesops.service.connectors.sql_connector import (
    SnowflakeConnector,
    RedshiftConnector,
)
from fidesops.service.masking.strategy.masking_strategy_factory import get_strategy
from fidesops.service.masking.strategy.masking_strategy_hmac import HmacMaskingStrategy
from fidesops.service.privacy_request.request_runner_service import PrivacyRequestRunner
from fidesops.util.async_util import wait_for
from fidesops.util.data_category import DataCategory


@mock.patch("fidesops.service.privacy_request.request_runner_service.upload")
def test_policy_upload_called(
    upload_mock: Mock,
    db: Session,
    privacy_request: PrivacyRequest,
    privacy_request_runner: PrivacyRequestRunner,
) -> None:
    wait_for(privacy_request_runner.submit())
    assert upload_mock.called


def test_start_processing_sets_started_processing_at(
    db: Session,
    privacy_request: PrivacyRequest,
    privacy_request_runner: PrivacyRequestRunner,
) -> None:
    privacy_request.started_processing_at = None
    wait_for(privacy_request_runner.submit())

    _sessionmaker = get_db_session()
    db = _sessionmaker()
    privacy_request = PrivacyRequest.get(db=db, id=privacy_request.id)
    assert privacy_request.started_processing_at is not None


def test_start_processing_doesnt_overwrite_started_processing_at(
    db: Session,
    privacy_request: PrivacyRequest,
    privacy_request_runner: PrivacyRequestRunner,
) -> None:
    before = privacy_request.started_processing_at
    wait_for(privacy_request_runner.submit())
    privacy_request = PrivacyRequest.get(db=db, id=privacy_request.id)
    assert privacy_request.started_processing_at == before


def get_privacy_request_results(
    db,
    policy,
    cache,
    privacy_request_data: Dict[str, Any],
) -> PrivacyRequest:
    """Utility method to run a privacy request and return results after waiting for
    the returned future."""
    kwargs = {
        "requested_at": pydash.get(privacy_request_data, "requested_at"),
        "policy_id": policy.id,
        "status": "pending",
    }
    optional_fields = ["started_processing_at", "finished_processing_at"]
    for field in optional_fields:
        try:
            attr = getattr(privacy_request_data, field)
            if attr is not None:
                kwargs[field] = attr
        except AttributeError:
            pass
    privacy_request = PrivacyRequest.create(db=db, data=kwargs)
    privacy_request.cache_identity(privacy_request_data["identity"])
    if "encryption_key" in privacy_request_data:
        privacy_request.cache_encryption(privacy_request_data["encryption_key"])

    erasure_rules: List[Rule] = policy.get_rules_for_action(
        action_type=ActionType.erasure
    )
    unique_masking_strategies_by_name: Set[str] = set()
    for rule in erasure_rules:
        strategy_name: str = rule.masking_strategy["strategy"]
        configuration: MaskingConfiguration = rule.masking_strategy["configuration"]
        if strategy_name in unique_masking_strategies_by_name:
            continue
        unique_masking_strategies_by_name.add(strategy_name)
        masking_strategy = get_strategy(strategy_name, configuration)
        if masking_strategy.secrets_required():
            masking_secrets: List[
                MaskingSecretCache
            ] = masking_strategy.generate_secrets_for_cache()
            for masking_secret in masking_secrets:
                privacy_request.cache_masking_secret(masking_secret)

    wait_for(
        PrivacyRequestRunner(
            cache=cache,
            privacy_request=privacy_request,
        ).submit()
    )

    return PrivacyRequest.get(db=db, id=privacy_request.id)


@pytest.mark.integration_postgres
@pytest.mark.integration
@mock.patch("fidesops.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
def test_create_and_process_access_request(
    trigger_webhook_mock,
    postgres_example_test_dataset_config_read_access,
    postgres_integration_db,
    db,
    cache,
    policy,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
):
    customer_email = "customer-1@example.com"
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }

    pr = get_privacy_request_results(db, policy, cache, data)

    results = pr.get_results()
    assert len(results.keys()) == 11

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = f"EN_{pr.id}__access_request__postgres_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    visit_key = result_key_prefix + "visit"
    assert results[visit_key][0]["email"] == customer_email
    log_id = pr.execution_logs[0].id
    pr_id = pr.id
    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4

    for webhook in policy_pre_execution_webhooks:
        webhook.delete(db=db)

    for webhook in policy_post_execution_webhooks:
        webhook.delete(db=db)

    policy.delete(db=db)
    pr.delete(db=db)
    assert not pr in db  # Check that `pr` has been expunged from the session
    assert ExecutionLog.get(db, id=log_id).privacy_request_id == pr_id


@pytest.mark.integration
@mock.patch("fidesops.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
def test_create_and_process_access_request_mssql(
    trigger_webhook_mock,
    mssql_example_test_dataset_config,
    mssql_integration_db,
    db,
    cache,
    policy,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
):

    customer_email = "customer-1@example.com"
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }

    pr = get_privacy_request_results(db, policy, cache, data)

    results = pr.get_results()
    assert len(results.keys()) == 11

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = f"EN_{pr.id}__access_request__mssql_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    visit_key = result_key_prefix + "visit"
    assert results[visit_key][0]["email"] == customer_email
    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4
    pr.delete(db=db)


@pytest.mark.integration
@mock.patch("fidesops.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
def test_create_and_process_access_request_mysql(
    trigger_webhook_mock,
    mysql_example_test_dataset_config,
    mysql_integration_db,
    db,
    cache,
    policy,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
):

    customer_email = "customer-1@example.com"
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }

    pr = get_privacy_request_results(db, policy, cache, data)

    results = pr.get_results()
    assert len(results.keys()) == 11

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = f"EN_{pr.id}__access_request__mysql_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    visit_key = result_key_prefix + "visit"
    assert results[visit_key][0]["email"] == customer_email
    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4
    pr.delete(db=db)


@pytest.mark.integration_mariadb
@pytest.mark.integration
@mock.patch("fidesops.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
def test_create_and_process_access_request_mariadb(
    trigger_webhook_mock,
    mariadb_example_test_dataset_config,
    mariadb_integration_db,
    db,
    cache,
    policy,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
):

    customer_email = "customer-1@example.com"
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }

    pr = get_privacy_request_results(db, policy, cache, data)

    results = pr.get_results()
    assert len(results.keys()) == 11

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = f"EN_{pr.id}__access_request__mariadb_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    visit_key = result_key_prefix + "visit"
    assert results[visit_key][0]["email"] == customer_email
    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4
    pr.delete(db=db)


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp
@mock.patch("fidesops.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
def test_create_and_process_access_request_saas_mailchimp(
    trigger_webhook_mock,
    mailchimp_connection_config,
    mailchimp_dataset_config,
    db,
    cache,
    policy,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    mailchimp_identity_email,
):
    customer_email = mailchimp_identity_email
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }

    pr = get_privacy_request_results(db, policy, cache, data)
    results = pr.get_results()
    assert len(results.keys()) == 3

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = f"EN_{pr.id}__access_request__mailchimp_connector_example:"
    member_key = result_key_prefix + "member"
    assert results[member_key][0]["email_address"] == customer_email

    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4

    pr.delete(db=db)


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp
@mock.patch("fidesops.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
def test_create_and_process_erasure_request_saas(
    _,
    mailchimp_connection_config,
    mailchimp_dataset_config,
    db,
    cache,
    erasure_policy_hmac,
    generate_auth_header,
    mailchimp_identity_email,
    reset_mailchimp_data,
):
    customer_email = mailchimp_identity_email
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy_hmac.key,
        "identity": {"email": customer_email},
    }

    pr = get_privacy_request_results(db, erasure_policy_hmac, cache, data)

    connector = SaaSConnector(mailchimp_connection_config)
    request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/3.0/search-members",
        query_params={"query": mailchimp_identity_email},
    )
    resp = connector.create_client().send(request)
    body = resp.json()
    merge_fields = body["exact_matches"]["members"][0]["merge_fields"]

    masking_configuration = HmacMaskingConfiguration()
    masking_strategy = HmacMaskingStrategy(masking_configuration)

    assert (
        merge_fields["FNAME"]
        == masking_strategy.mask(
            [reset_mailchimp_data["merge_fields"]["FNAME"]], pr.id
        )[0]
    )
    assert (
        merge_fields["LNAME"]
        == masking_strategy.mask(
            [reset_mailchimp_data["merge_fields"]["LNAME"]], pr.id
        )[0]
    )

    pr.delete(db=db)


@pytest.mark.integration_saas
@pytest.mark.integration_hubspot
@mock.patch("fidesops.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
def test_create_and_process_access_request_saas_hubspot(
    trigger_webhook_mock,
    connection_config_hubspot,
    dataset_config_hubspot,
    db,
    cache,
    policy,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    hubspot_identity_email,
):
    customer_email = hubspot_identity_email
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }

    pr = get_privacy_request_results(db, policy, cache, data)
    results = pr.get_results()
    assert len(results.keys()) == 3

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = f"EN_{pr.id}__access_request__hubspot_connector_example:"
    contacts_key = result_key_prefix + "contacts"
    assert results[contacts_key][0]["properties"]["email"] == customer_email

    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4

    pr.delete(db=db)


@pytest.mark.integration_postgres
@pytest.mark.integration
def test_create_and_process_erasure_request_specific_category_postgres(
    postgres_integration_db,
    postgres_example_test_dataset_config,
    cache,
    db,
    generate_auth_header,
    erasure_policy,
    read_connection_config,
):
    customer_email = "customer-1@example.com"
    customer_id = 1
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }

    stmt = select("*").select_from(table("customer"))
    res = postgres_integration_db.execute(stmt).all()

    pr = get_privacy_request_results(db, erasure_policy, cache, data)
    pr.delete(db=db)

    stmt = select(
        column("id"),
        column("name"),
    ).select_from(table("customer"))
    res = postgres_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id in row:
            customer_found = True
            # Check that the `name` field is `None`
            assert row.name is None
    assert customer_found


@pytest.mark.integration_mssql
@pytest.mark.integration
def test_create_and_process_erasure_request_specific_category_mssql(
    mssql_integration_db,
    mssql_example_test_dataset_config,
    cache,
    db,
    generate_auth_header,
    erasure_policy,
):
    customer_email = "customer-1@example.com"
    customer_id = 1
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }

    pr = get_privacy_request_results(db, erasure_policy, cache, data)
    pr.delete(db=db)

    stmt = select(
        column("id"),
        column("name"),
    ).select_from(table("customer"))
    res = mssql_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id in row:
            customer_found = True
            # Check that the `name` field is `None`
            assert row.name is None
    assert customer_found


@pytest.mark.integration_mysql
@pytest.mark.integration
def test_create_and_process_erasure_request_specific_category_mysql(
    mysql_integration_db,
    mysql_example_test_dataset_config,
    cache,
    db,
    generate_auth_header,
    erasure_policy,
):
    customer_email = "customer-1@example.com"
    customer_id = 1
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }

    pr = get_privacy_request_results(db, erasure_policy, cache, data)
    pr.delete(db=db)

    stmt = select(
        column("id"),
        column("name"),
    ).select_from(table("customer"))
    res = mysql_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id in row:
            customer_found = True
            # Check that the `name` field is `None`
            assert row.name is None
    assert customer_found


@pytest.mark.integration_mariadb
@pytest.mark.integration
def test_create_and_process_erasure_request_specific_category_mariadb(
    mariadb_example_test_dataset_config,
    mariadb_integration_db,
    cache,
    db,
    generate_auth_header,
    erasure_policy,
):
    customer_email = "customer-1@example.com"
    customer_id = 1
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }

    pr = get_privacy_request_results(db, erasure_policy, cache, data)
    pr.delete(db=db)

    stmt = select(
        column("id"),
        column("name"),
    ).select_from(table("customer"))
    res = mariadb_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id in row:
            customer_found = True
            # Check that the `name` field is `None`
            assert row.name is None
    assert customer_found


@pytest.mark.integration_postgres
@pytest.mark.integration
def test_create_and_process_erasure_request_generic_category(
    postgres_integration_db,
    postgres_example_test_dataset_config,
    cache,
    db,
    generate_auth_header,
    erasure_policy,
):
    # It's safe to change this here since the `erasure_policy` fixture is scoped
    # at function level
    target = erasure_policy.rules[0].targets[0]
    target.data_category = DataCategory("user.provided.identifiable.contact").value
    target.save(db=db)

    email = "customer-2@example.com"
    customer_id = 2
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": email},
    }

    pr = get_privacy_request_results(db, erasure_policy, cache, data)
    pr.delete(db=db)

    stmt = select(
        column("id"),
        column("email"),
        column("name"),
    ).select_from(table("customer"))
    res = postgres_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id in row:
            customer_found = True
            # Check that the `email` field is `None` and that its data category
            # ("user.provided.identifiable.contact.email") has been erased by the parent
            # category ("user.provided.identifiable.contact")
            assert row.email is None
            assert row.name is not None
        else:
            # There are two rows other rows, and they should not have been erased
            assert row.email in ["customer-1@example.com", "jane@example.com"]
    assert customer_found


@pytest.mark.integration_postgres
@pytest.mark.integration
def test_create_and_process_erasure_request_aes_generic_category(
    postgres_integration_db,
    postgres_example_test_dataset_config,
    cache,
    db,
    generate_auth_header,
    erasure_policy_aes,
):
    # It's safe to change this here since the `erasure_policy` fixture is scoped
    # at function level
    target = erasure_policy_aes.rules[0].targets[0]
    target.data_category = DataCategory("user.provided.identifiable.contact").value
    target.save(db=db)

    email = "customer-2@example.com"
    customer_id = 2
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy_aes.key,
        "identity": {"email": email},
    }

    pr = get_privacy_request_results(db, erasure_policy_aes, cache, data)
    pr.delete(db=db)

    stmt = select(
        column("id"),
        column("email"),
        column("name"),
    ).select_from(table("customer"))
    res = postgres_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id in row:
            customer_found = True
            # Check that the `email` field is not original val and that its data category
            # ("user.provided.identifiable.contact.email") has been erased by the parent
            # category ("user.provided.identifiable.contact").
            # masked val for `email` field will change per new privacy request, so the best
            # we can do here is test that the original val has been changed
            assert row[1] != "customer-2@example.com"
            assert row[2] is not None
        else:
            # There are two rows other rows, and they should not have been erased
            assert row[1] in ["customer-1@example.com", "jane@example.com"]
    assert customer_found


@pytest.mark.integration_postgres
@pytest.mark.integration
def test_create_and_process_erasure_request_with_table_joins(
    postgres_integration_db,
    postgres_example_test_dataset_config,
    db,
    cache,
    erasure_policy,
):
    # It's safe to change this here since the `erasure_policy` fixture is scoped
    # at function level
    target = erasure_policy.rules[0].targets[0]
    target.data_category = DataCategory("user.provided.identifiable.financial").value
    target.save(db=db)

    customer_email = "customer-1@example.com"
    customer_id = 1
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }

    pr = get_privacy_request_results(db, erasure_policy, cache, data)
    pr.delete(db=db)

    stmt = select(
        column("customer_id"),
        column("id"),
        column("ccn"),
        column("code"),
        column("name"),
    ).select_from(table("payment_card"))
    res = postgres_integration_db.execute(stmt).all()

    card_found = False
    for row in res:
        if row.customer_id == customer_id:
            card_found = True
            assert row.ccn is None
            assert row.code is None
            assert row.name is None

    assert card_found is True


@pytest.mark.integration_postgres
@pytest.mark.integration
def test_create_and_process_erasure_request_read_access(
    postgres_integration_db,
    postgres_example_test_dataset_config_read_access,
    db,
    cache,
    erasure_policy,
):
    customer_email = "customer-2@example.com"
    customer_id = 2
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }

    pr = get_privacy_request_results(db, erasure_policy, cache, data)
    errored_execution_logs = pr.execution_logs.filter_by(status="error")
    assert errored_execution_logs.count() == 9
    assert (
        errored_execution_logs[0].message
        == "No values were erased since this connection "
        "my_postgres_db_1_read_config has not been given write access"
    )
    pr.delete(db=db)

    stmt = select(
        column("id"),
        column("name"),
    ).select_from(table("customer"))
    res = postgres_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id in row:
            customer_found = True
            # Check that the `name` field is NOT `None`. We couldn't erase, because the ConnectionConfig only had
            # "read" access
            assert row.name is not None
    assert customer_found


@pytest.fixture(scope="function")
def snowflake_resources(
    snowflake_example_test_dataset_config,
):
    snowflake_connection_config = (
        snowflake_example_test_dataset_config.connection_config
    )
    snowflake_client = SnowflakeConnector(snowflake_connection_config).client()
    uuid = str(uuid4())
    customer_email = f"customer-{uuid}@example.com"
    formatted_customer_email = f"'{customer_email}'"
    customer_name = f"{uuid}"
    formatted_customer_name = f"'{customer_name}'"

    stmt = 'select max("id") from "customer";'
    res = snowflake_client.execute(stmt).all()
    customer_id = res[0][0] + 1

    stmt = f"""
    insert into "customer" ("id", "email", "name", "variant_eg")
    select {customer_id}, {formatted_customer_email}, {formatted_customer_name}, to_variant({formatted_customer_name});
    """
    res = snowflake_client.execute(stmt).all()
    assert res[0][0] == 1
    yield {
        "email": customer_email,
        "formatted_email": formatted_customer_email,
        "name": customer_name,
        "id": customer_id,
        "client": snowflake_client,
    }
    # Remove test data and close Snowflake connection in teardown
    stmt = f'delete from "customer" where "email" = {formatted_customer_email};'
    res = snowflake_client.execute(stmt).all()
    assert res[0][0] == 1


@pytest.mark.integration_external
@pytest.mark.integration_snowflake
def test_create_and_process_access_request_snowflake(
    snowflake_resources,
    db,
    cache,
    policy,
):
    customer_email = snowflake_resources["email"]
    customer_name = snowflake_resources["name"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }
    pr = get_privacy_request_results(db, policy, cache, data)
    results = pr.get_results()
    customer_table_key = (
        f"EN_{pr.id}__access_request__snowflake_example_test_dataset:customer"
    )
    assert len(results[customer_table_key]) == 1
    assert results[customer_table_key][0]["email"] == customer_email
    assert results[customer_table_key][0]["name"] == customer_name

    pr.delete(db=db)


@pytest.mark.integration_external
@pytest.mark.integration_snowflake
def test_create_and_process_erasure_request_snowflake(
    snowflake_example_test_dataset_config,
    snowflake_resources,
    integration_config: Dict[str, str],
    db,
    cache,
    erasure_policy,
):
    customer_email = snowflake_resources["email"]
    snowflake_client = snowflake_resources["client"]
    formatted_customer_email = snowflake_resources["formatted_email"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }
    pr = get_privacy_request_results(db, erasure_policy, cache, data)
    pr.delete(db=db)

    stmt = f'select "name", "variant_eg" from "customer" where "email" = {formatted_customer_email};'
    res = snowflake_client.execute(stmt).all()
    for row in res:
        assert row.name is None
        assert row.variant_eg is None


@pytest.fixture(scope="function")
def redshift_resources(
    redshift_example_test_dataset_config,
):
    redshift_connection_config = redshift_example_test_dataset_config.connection_config
    connector = RedshiftConnector(redshift_connection_config)
    redshift_client = connector.client()
    with redshift_client.connect() as connection:
        connector.set_schema(connection)
        uuid = str(uuid4())
        customer_email = f"customer-{uuid}@example.com"
        customer_name = f"{uuid}"

        stmt = "select max(id) from customer;"
        res = connection.execute(stmt)
        customer_id = res.all()[0][0] + 1

        stmt = "select max(id) from address;"
        res = connection.execute(stmt)
        address_id = res.all()[0][0] + 1

        city = "Test City"
        state = "TX"
        stmt = f"""
        insert into address (id, house, street, city, state, zip)
        values ({address_id}, '{111}', 'Test Street', '{city}', '{state}', '55555');
        """
        connection.execute(stmt)

        stmt = f"""
            insert into customer (id, email, name, address_id)
            values ({customer_id}, '{customer_email}', '{customer_name}', '{address_id}');
        """
        connection.execute(stmt)

        yield {
            "email": customer_email,
            "name": customer_name,
            "id": customer_id,
            "client": redshift_client,
            "address_id": address_id,
            "city": city,
            "state": state,
            "connector": connector,
        }
        # Remove test data and close Redshift connection in teardown
        stmt = f"delete from customer where email = '{customer_email}';"
        connection.execute(stmt)

        stmt = f'delete from address where "id" = {address_id};'
        connection.execute(stmt)


@pytest.mark.integration_external
@pytest.mark.integration_redshift
def test_create_and_process_access_request_redshift(
    redshift_resources,
    db,
    cache,
    policy,
):
    customer_email = redshift_resources["email"]
    customer_name = redshift_resources["name"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }
    pr = get_privacy_request_results(db, policy, cache, data)
    results = pr.get_results()
    customer_table_key = (
        f"EN_{pr.id}__access_request__redshift_example_test_dataset:customer"
    )
    assert len(results[customer_table_key]) == 1
    assert results[customer_table_key][0]["email"] == customer_email
    assert results[customer_table_key][0]["name"] == customer_name

    address_table_key = (
        f"EN_{pr.id}__access_request__redshift_example_test_dataset:address"
    )

    city = redshift_resources["city"]
    state = redshift_resources["state"]
    assert len(results[address_table_key]) == 1
    assert results[address_table_key][0]["city"] == city
    assert results[address_table_key][0]["state"] == state

    pr.delete(db=db)


@pytest.mark.integration_external
@pytest.mark.integration_redshift
def test_create_and_process_erasure_request_redshift(
    redshift_example_test_dataset_config,
    redshift_resources,
    integration_config: Dict[str, str],
    db,
    cache,
    erasure_policy,
):
    customer_email = redshift_resources["email"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }

    # Should erase customer name
    pr = get_privacy_request_results(db, erasure_policy, cache, data)
    pr.delete(db=db)

    connector = redshift_resources["connector"]
    redshift_client = redshift_resources["client"]
    with redshift_client.connect() as connection:
        connector.set_schema(connection)
        stmt = f"select name from customer where email = '{customer_email}';"
        res = connection.execute(stmt).all()
        for row in res:
            assert row.name is None

        address_id = redshift_resources["address_id"]
        stmt = f"select 'id', city, state from address where id = {address_id};"
        res = connection.execute(stmt).all()
        for row in res:
            # Not yet masked because these fields aren't targeted by erasure policy
            assert row.city == redshift_resources["city"]
            assert row.state == redshift_resources["state"]

    target = erasure_policy.rules[0].targets[0]
    target.data_category = "user.provided.identifiable.contact.state"
    target.save(db=db)

    # Should erase state fields on address table
    pr = get_privacy_request_results(db, erasure_policy, cache, data)
    pr.delete(db=db)

    connector = redshift_resources["connector"]
    redshift_client = redshift_resources["client"]
    with redshift_client.connect() as connection:
        connector.set_schema(connection)

        address_id = redshift_resources["address_id"]
        stmt = f"select 'id', city, state from address where id = {address_id};"
        res = connection.execute(stmt).all()
        for row in res:
            # State field was targeted by erasure policy but city was not
            assert row.city is not None
            assert row.state is None


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
def test_create_and_process_access_request_bigquery(
    bigquery_resources,
    db,
    cache,
    policy,
):
    customer_email = bigquery_resources["email"]
    customer_name = bigquery_resources["name"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }
    pr = get_privacy_request_results(db, policy, cache, data)
    results = pr.get_results()
    customer_table_key = (
        f"EN_{pr.id}__access_request__bigquery_example_test_dataset:customer"
    )
    assert len(results[customer_table_key]) == 1
    assert results[customer_table_key][0]["email"] == customer_email
    assert results[customer_table_key][0]["name"] == customer_name

    address_table_key = (
        f"EN_{pr.id}__access_request__bigquery_example_test_dataset:address"
    )

    city = bigquery_resources["city"]
    state = bigquery_resources["state"]
    assert len(results[address_table_key]) == 1
    assert results[address_table_key][0]["city"] == city
    assert results[address_table_key][0]["state"] == state

    pr.delete(db=db)


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
def test_create_and_process_erasure_request_bigquery(
    bigquery_example_test_dataset_config,
    bigquery_resources,
    integration_config: Dict[str, str],
    db,
    cache,
    erasure_policy,
):
    customer_email = bigquery_resources["email"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }

    # Should erase customer name
    pr = get_privacy_request_results(db, erasure_policy, cache, data)
    pr.delete(db=db)

    bigquery_client = bigquery_resources["client"]
    with bigquery_client.connect() as connection:
        stmt = f"select name from customer where email = '{customer_email}';"
        res = connection.execute(stmt).all()
        for row in res:
            assert row.name is None

        address_id = bigquery_resources["address_id"]
        stmt = f"select 'id', city, state from address where id = {address_id};"
        res = connection.execute(stmt).all()
        for row in res:
            # Not yet masked because these fields aren't targeted by erasure policy
            assert row.city == bigquery_resources["city"]
            assert row.state == bigquery_resources["state"]

    target = erasure_policy.rules[0].targets[0]
    target.data_category = "user.provided.identifiable.contact.state"
    target.save(db=db)

    # Should erase state fields on address table
    pr = get_privacy_request_results(db, erasure_policy, cache, data)
    pr.delete(db=db)

    bigquery_client = bigquery_resources["client"]
    with bigquery_client.connect() as connection:

        address_id = bigquery_resources["address_id"]
        stmt = f"select 'id', city, state from address where id = {address_id};"
        res = connection.execute(stmt).all()
        for row in res:
            # State field was targeted by erasure policy but city was not
            assert row.city is not None
            assert row.state is None


class TestPrivacyRequestRunnerRunWebhooks:
    @mock.patch("fidesops.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
    def test_run_webhooks_halt_received(
        self,
        mock_trigger_policy_webhook,
        db,
        privacy_request,
        privacy_request_runner,
        policy_pre_execution_webhooks,
    ):
        mock_trigger_policy_webhook.side_effect = PrivacyRequestPaused(
            "Request received to halt"
        )

        proceed = privacy_request_runner.run_webhooks_and_report_status(
            db, privacy_request, PolicyPreWebhook
        )
        assert not proceed
        assert privacy_request.finished_processing_at is None
        assert privacy_request.status == PrivacyRequestStatus.paused

    @mock.patch("fidesops.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
    def test_run_webhooks_ap_scheduler_cleanup(
        self,
        mock_trigger_policy_webhook,
        db,
        privacy_request,
        privacy_request_runner,
        policy_pre_execution_webhooks,
    ):
        config.redis.DEFAULT_TTL_SECONDS = (
            1  # Set redis cache to expire very quickly for testing purposes
        )
        mock_trigger_policy_webhook.side_effect = PrivacyRequestPaused(
            "Request received to halt"
        )

        proceed = privacy_request_runner.run_webhooks_and_report_status(
            db, privacy_request, PolicyPreWebhook
        )
        assert not proceed
        time.sleep(3)

        db.refresh(privacy_request)
        # Privacy request has been set to errored by ap scheduler, because it took too long for webhook to report back
        assert privacy_request.status == PrivacyRequestStatus.error
        assert privacy_request.finished_processing_at is not None

    @mock.patch("fidesops.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
    def test_run_webhooks_client_error(
        self,
        mock_trigger_policy_webhook,
        db,
        privacy_request,
        privacy_request_runner,
        policy_pre_execution_webhooks,
    ):
        mock_trigger_policy_webhook.side_effect = ClientUnsuccessfulException(
            status_code=500
        )

        proceed = privacy_request_runner.run_webhooks_and_report_status(
            db, privacy_request, PolicyPreWebhook
        )
        assert not proceed
        assert privacy_request.status == PrivacyRequestStatus.error

    @mock.patch("fidesops.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
    def test_run_webhooks_validation_error(
        self,
        mock_trigger_policy_webhook,
        db,
        privacy_request,
        privacy_request_runner,
        policy_pre_execution_webhooks,
    ):
        mock_trigger_policy_webhook.side_effect = ValidationError(
            errors={}, model=SecondPartyResponseFormat
        )

        proceed = privacy_request_runner.run_webhooks_and_report_status(
            db, privacy_request, PolicyPreWebhook
        )
        assert not proceed
        assert privacy_request.finished_processing_at is not None
        assert privacy_request.status == PrivacyRequestStatus.error

    @mock.patch("fidesops.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
    def test_run_webhooks(
        self,
        mock_trigger_policy_webhook,
        db,
        privacy_request,
        privacy_request_runner,
        policy_pre_execution_webhooks,
    ):

        proceed = privacy_request_runner.run_webhooks_and_report_status(
            db, privacy_request, PolicyPreWebhook
        )
        assert proceed
        assert privacy_request.status == PrivacyRequestStatus.in_processing
        assert privacy_request.finished_processing_at is None
        assert mock_trigger_policy_webhook.call_count == 2

    @mock.patch("fidesops.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
    def test_run_webhooks_after_webhook(
        self,
        mock_trigger_policy_webhook,
        db,
        privacy_request,
        privacy_request_runner,
        policy_pre_execution_webhooks,
    ):
        """Test running webhooks after specific webhook - for when we're resuming privacy request execution"""
        proceed = privacy_request_runner.run_webhooks_and_report_status(
            db, privacy_request, PolicyPreWebhook, policy_pre_execution_webhooks[0].id
        )
        assert proceed
        assert privacy_request.status == PrivacyRequestStatus.in_processing
        assert privacy_request.finished_processing_at is None
        assert mock_trigger_policy_webhook.call_count == 1
