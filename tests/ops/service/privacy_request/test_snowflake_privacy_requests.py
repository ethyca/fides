import json
from uuid import uuid4

import pytest

from fides.api.service.connectors.snowflake_connector import SnowflakeConnector
from tests.ops.service.privacy_request.test_request_runner_service import (
    PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    get_privacy_request_results,
)


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


@pytest.fixture(scope="function")
def snowflake_resources_with_namespace_meta(
    snowflake_example_test_dataset_config_with_namespace_meta,
):
    snowflake_connection_config = (
        snowflake_example_test_dataset_config_with_namespace_meta.connection_config
    )
    snowflake_client = SnowflakeConnector(snowflake_connection_config).client()
    uuid = str(uuid4())
    customer_email = f"customer-{uuid}@example.com"
    formatted_customer_email = f"'{customer_email}'"
    customer_name = f"{uuid}"
    formatted_customer_name = f"'{customer_name}'"

    stmt = 'select max("id") from "FIDESOPS_TEST"."TEST"."customer";'
    res = snowflake_client.execute(stmt).all()
    customer_id = res[0][0] + 1

    stmt = f"""
    insert into "FIDESOPS_TEST"."TEST"."customer" ("id", "email", "name", "variant_eg")
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
    stmt = f'delete from "FIDESOPS_TEST"."TEST"."customer" where "email" = {formatted_customer_email};'
    res = snowflake_client.execute(stmt).all()
    assert res[0][0] == 1


@pytest.fixture(scope="function")
def snowflake_resources_with_json_variant(
    snowflake_example_test_dataset_config,
):
    """Fixture that inserts actual nested JSON into the VARIANT column."""
    snowflake_connection_config = (
        snowflake_example_test_dataset_config.connection_config
    )
    snowflake_client = SnowflakeConnector(snowflake_connection_config).client()
    uuid = str(uuid4())
    customer_email = f"customer-{uuid}@example.com"
    formatted_customer_email = f"'{customer_email}'"
    customer_name = f"{uuid}"
    formatted_customer_name = f"'{customer_name}'"

    variant_data = {
        "first_name": customer_name,
        "address": {"city": "Example City", "zip": "12345"},
        "tags": ["vip", "active"],
    }
    variant_json_str = json.dumps(variant_data)
    formatted_variant_json = f"'{variant_json_str}'"

    stmt = 'select max("id") from "customer";'
    res = snowflake_client.execute(stmt).all()
    customer_id = res[0][0] + 1

    stmt = f"""
    insert into "customer" ("id", "email", "name", "variant_eg")
    select {customer_id}, {formatted_customer_email}, {formatted_customer_name}, parse_json({formatted_variant_json});
    """
    res = snowflake_client.execute(stmt).all()
    assert res[0][0] == 1
    yield {
        "email": customer_email,
        "formatted_email": formatted_customer_email,
        "name": customer_name,
        "id": customer_id,
        "variant_data": variant_data,
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
    policy,
    run_privacy_request_task,
):
    customer_email = snowflake_resources["email"]
    customer_name = snowflake_resources["name"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }
    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    results = pr.get_raw_access_results()
    customer_table_key = "snowflake_example_test_dataset:customer"
    assert len(results[customer_table_key]) == 1
    assert results[customer_table_key][0]["email"] == customer_email
    assert results[customer_table_key][0]["name"] == customer_name

    pr.delete(db=db)


@pytest.mark.integration_external
@pytest.mark.integration_snowflake
def test_create_and_process_erasure_request_snowflake(
    snowflake_resources,
    db,
    erasure_policy,
    run_privacy_request_task,
):
    customer_email = snowflake_resources["email"]
    snowflake_client = snowflake_resources["client"]
    formatted_customer_email = snowflake_resources["formatted_email"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }
    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    pr.delete(db=db)

    stmt = f'select "name", "variant_eg" from "customer" where "email" = {formatted_customer_email};'
    res = snowflake_client.execute(stmt).all()
    for row in res:
        assert row.name is None
        assert row.variant_eg is None


@pytest.mark.integration_external
@pytest.mark.integration_snowflake
def test_create_and_process_access_request_snowflake_with_namespace_meta(
    snowflake_resources_with_namespace_meta,
    db,
    policy,
    run_privacy_request_task,
):
    customer_email = snowflake_resources_with_namespace_meta["email"]
    customer_name = snowflake_resources_with_namespace_meta["name"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }
    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    results = pr.get_raw_access_results()
    customer_table_key = "snowflake_example_test_dataset:customer"
    assert len(results[customer_table_key]) == 1
    assert results[customer_table_key][0]["email"] == customer_email
    assert results[customer_table_key][0]["name"] == customer_name

    pr.delete(db=db)


@pytest.mark.integration_external
@pytest.mark.integration_snowflake
def test_create_and_process_erasure_request_snowflake_with_namespace_meta(
    snowflake_resources_with_namespace_meta,
    db,
    erasure_policy,
    run_privacy_request_task,
):
    customer_email = snowflake_resources_with_namespace_meta["email"]
    snowflake_client = snowflake_resources_with_namespace_meta["client"]
    formatted_customer_email = snowflake_resources_with_namespace_meta[
        "formatted_email"
    ]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }
    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    pr.delete(db=db)

    stmt = f'select "name", "variant_eg" from "FIDESOPS_TEST"."TEST"."customer" where "email" = {formatted_customer_email};'
    res = snowflake_client.execute(stmt).all()
    for row in res:
        assert row.name is None
        assert row.variant_eg is None


@pytest.mark.integration_external
@pytest.mark.integration_snowflake
def test_access_request_snowflake_with_json_variant(
    snowflake_resources_with_json_variant,
    db,
    policy,
    run_privacy_request_task,
):
    """Verify that nested JSON stored in a VARIANT column is returned in the access package."""
    customer_email = snowflake_resources_with_json_variant["email"]
    customer_name = snowflake_resources_with_json_variant["name"]
    variant_data = snowflake_resources_with_json_variant["variant_data"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }
    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    results = pr.get_raw_access_results()
    customer_table_key = "snowflake_example_test_dataset:customer"
    assert len(results[customer_table_key]) == 1

    row = results[customer_table_key][0]
    assert row["email"] == customer_email
    assert row["name"] == customer_name

    # Verify the VARIANT column contains the full JSON structure
    returned_variant = row["variant_eg"]
    if isinstance(returned_variant, str):
        returned_variant = json.loads(returned_variant)
    assert returned_variant["first_name"] == customer_name
    assert returned_variant["address"]["city"] == "Example City"
    assert returned_variant["address"]["zip"] == "12345"
    assert returned_variant["tags"] == ["vip", "active"]

    pr.delete(db=db)


@pytest.mark.integration_external
@pytest.mark.integration_snowflake
def test_erasure_request_snowflake_with_json_variant(
    snowflake_resources_with_json_variant,
    db,
    erasure_policy,
    run_privacy_request_task,
):
    """Verify that a VARIANT column containing nested JSON is erased (nullified) by an erasure request."""
    customer_email = snowflake_resources_with_json_variant["email"]
    snowflake_client = snowflake_resources_with_json_variant["client"]
    formatted_customer_email = snowflake_resources_with_json_variant["formatted_email"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }
    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    pr.delete(db=db)

    stmt = f'select "name", "variant_eg" from "customer" where "email" = {formatted_customer_email};'
    res = snowflake_client.execute(stmt).all()
    for row in res:
        assert row.name is None
        assert row.variant_eg is None
