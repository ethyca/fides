import pytest

from tests.ops.service.privacy_request.test_request_runner_service import (
    PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    get_privacy_request_results,
)


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_2_0", "use_dsr_3_0"],
)
@pytest.mark.parametrize(
    "bigquery_fixtures",
    ["bigquery_resources", "bigquery_resources_with_namespace_meta"],
)
def test_create_and_process_access_request_bigquery(
    db,
    policy,
    dsr_version,
    request,
    bigquery_fixtures,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
    bigquery_resources = request.getfixturevalue(bigquery_fixtures)

    customer_email = bigquery_resources["email"]
    customer_name = bigquery_resources["name"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }
    bigquery_client = bigquery_resources["client"]
    with bigquery_client.connect() as connection:
        stmt = f"select * from fidesopstest.employee where address_id = {bigquery_resources['address_id']};"
        res = connection.execute(stmt).all()
        for row in res:
            assert row.address_id == bigquery_resources["address_id"]
            assert row.id == bigquery_resources["employee_id"]
            assert row.email == bigquery_resources["employee_email"]

    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    results = pr.get_raw_access_results()
    customer_table_key = "bigquery_example_test_dataset:customer"
    assert len(results[customer_table_key]) == 1
    assert results[customer_table_key][0]["email"] == customer_email
    assert results[customer_table_key][0]["name"] == customer_name

    address_table_key = "bigquery_example_test_dataset:address"

    city = bigquery_resources["city"]
    state = bigquery_resources["state"]
    assert len(results[address_table_key]) == 1
    assert results[address_table_key][0]["city"] == city
    assert results[address_table_key][0]["state"] == state

    employee_table_key = "bigquery_example_test_dataset:employee"
    assert len(results[employee_table_key]) == 1
    assert results["bigquery_example_test_dataset:employee"] != []
    assert (
        results[employee_table_key][0]["address_id"] == bigquery_resources["address_id"]
    )
    assert (
        results[employee_table_key][0]["email"] == bigquery_resources["employee_email"]
    )
    assert results[employee_table_key][0]["id"] == bigquery_resources["employee_id"]

    # this covers access requests against a partitioned table
    visit_partitioned_table_key = "bigquery_example_test_dataset:visit_partitioned"
    assert len(results[visit_partitioned_table_key]) == 1
    assert (
        results[visit_partitioned_table_key][0]["email"] == bigquery_resources["email"]
    )

    pr.delete(db=db)


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_2_0", "use_dsr_3_0"],
)
@pytest.mark.parametrize(
    "bigquery_fixtures",
    ["bigquery_resources", "bigquery_resources_with_namespace_meta"],
)
def test_create_and_process_erasure_request_bigquery(
    db,
    dsr_version,
    request,
    bigquery_fixtures,
    erasure_policy,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
    bigquery_resources = request.getfixturevalue(bigquery_fixtures)

    bigquery_client = bigquery_resources["client"]
    # Verifying that employee info exists in db
    with bigquery_client.connect() as connection:
        stmt = f"select * from fidesopstest.employee where address_id = {bigquery_resources['address_id']};"
        res = connection.execute(stmt).all()
        for row in res:
            assert row.address_id == bigquery_resources["address_id"]
            assert row.id == bigquery_resources["employee_id"]
            assert row.email == bigquery_resources["employee_email"]

    customer_email = bigquery_resources["email"]
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": customer_email},
    }

    # Should erase customer name
    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    pr.delete(db=db)

    bigquery_client = bigquery_resources["client"]
    with bigquery_client.connect() as connection:
        stmt = (
            f"select name from fidesopstest.customer where email = '{customer_email}';"
        )
        res = connection.execute(stmt).all()
        for row in res:
            assert row.name is None

        address_id = bigquery_resources["address_id"]
        stmt = f"select 'id', city, state from fidesopstest.address where id = {address_id};"
        res = connection.execute(stmt).all()
        for row in res:
            # Not yet masked because these fields aren't targeted by erasure policy
            assert row.city == bigquery_resources["city"]
            assert row.state == bigquery_resources["state"]

    target = erasure_policy.rules[0].targets[0]
    target.data_category = "user.contact.address.state"
    target.save(db=db)

    # Should erase state fields on address table
    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )

    bigquery_client = bigquery_resources["client"]
    with bigquery_client.connect() as connection:
        address_id = bigquery_resources["address_id"]
        stmt = f"select 'id', city, state from fidesopstest.address where id = {address_id};"
        res = connection.execute(stmt).all()
        for row in res:
            # State field was targeted by erasure policy but city was not
            assert row.city is not None
            assert row.state is None

        stmt = f"select 'id', city, state from fidesopstest.address where id = {address_id};"
        res = connection.execute(stmt).all()
        for row in res:
            # State field was targeted by erasure policy but city was not
            assert row.city is not None
            assert row.state is None

        stmt = f"select * from fidesopstest.employee where address_id = {bigquery_resources['address_id']};"
        res = connection.execute(stmt).all()

        # Employee records deleted entirely due to collection-level masking strategy override
        assert res == []

    pr.delete(db=db)
