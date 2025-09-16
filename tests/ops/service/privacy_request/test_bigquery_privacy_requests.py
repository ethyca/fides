import pytest

from fides.api.models.privacy_request import ExecutionLog
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from tests.ops.service.privacy_request.test_request_runner_service import (
    PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    get_privacy_request_results,
)


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
@pytest.mark.serial
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_2_0", "use_dsr_3_0"],
)
@pytest.mark.parametrize(
    "bigquery_fixtures",
    ["bigquery_resources", "bigquery_resources_with_namespace_meta"],
)
@pytest.mark.xfail(reason="Flaky Test - BigQuery table not found error")
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
    assert results[visit_partitioned_table_key][0]["email"] == customer_email

    customer_profile_table_key = "bigquery_example_test_dataset:customer_profile"
    assert len(results[customer_profile_table_key]) == 1
    assert (
        results[customer_profile_table_key][0]["contact_info"]["primary_email"]
        == customer_email
    )

    pr.delete(db=db)


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
@pytest.mark.serial
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


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
@pytest.mark.serial
@pytest.mark.parametrize("dsr_version", ["use_dsr_2_0", "use_dsr_3_0"])
@pytest.mark.parametrize(
    "scenario,expected_status",
    [
        ("customer_profile", ExecutionLogStatus.skipped),  # Leaf collection
        ("customer", ExecutionLogStatus.error),  # Has dependencies
    ],
)
def test_bigquery_missing_tables_handling(
    db,
    policy,
    dsr_version,
    request,
    scenario,
    expected_status,
    bigquery_missing_table_resources,
    run_privacy_request_task,
):
    """
    Test BigQuery missing table handling:
    - Missing leaf collections should be skipped gracefully
    - Missing collections with dependencies should cause errors
    """
    request.getfixturevalue(dsr_version)

    # Get dataset config and collection key
    dataset_config = request.getfixturevalue(f"bigquery_missing_{scenario}_config")
    missing_collection_key = f"{dataset_config.fides_key}:{scenario}_missing"

    # Create privacy request
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": bigquery_missing_table_resources["email"]},
    }

    # Execute request (allow errors for dependency failures)
    try:
        pr = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            data,
            task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
        )
    except Exception:
        # For dependency errors, get the most recent privacy request
        pr = db.query(PrivacyRequest).order_by(PrivacyRequest.created_at.desc()).first()

    # Verify execution logs
    execution_logs = db.query(ExecutionLog).filter_by(privacy_request_id=pr.id).all()

    # Find logs for the missing collection
    missing_collection_logs = [
        log
        for log in execution_logs
        if f"{log.dataset_name}:{log.collection_name}" == missing_collection_key
    ]

    # Verify expected status
    assert missing_collection_logs, f"No logs found for {missing_collection_key}"

    status_logs = [
        log for log in missing_collection_logs if log.status == expected_status
    ]
    assert status_logs, f"Expected status {expected_status} not found"

    # Verify error/skip message mentions missing table
    log = status_logs[0]
    assert log.message and any(
        keyword in log.message.lower() for keyword in ["not found", "missing", scenario]
    ), f"Expected message about missing table, got: {log.message}"


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
@pytest.mark.serial
@pytest.mark.parametrize("dsr_version", ["use_dsr_2_0", "use_dsr_3_0"])
def test_bigquery_missing_tables_handling_erasure_leaf_collection(
    db,
    erasure_policy,
    dsr_version,
    request,
    bigquery_missing_table_resources,
    run_privacy_request_task,
):
    """
    Test BigQuery missing table handling during erasure operations for leaf collections:
    - Missing leaf collections complete successfully during access (skipped gracefully)
    - Erasure then runs normally and completes successfully
    """
    request.getfixturevalue(dsr_version)

    # Get dataset config for customer_profile (leaf collection)
    dataset_config = request.getfixturevalue("bigquery_missing_customer_profile_config")
    missing_collection_key = f"{dataset_config.fides_key}:customer_profile_missing"

    # Create privacy request with erasure policy
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": bigquery_missing_table_resources["email"]},
    }

    # Execute request - should complete successfully
    pr = get_privacy_request_results(
        db,
        erasure_policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )

    # Verify execution logs for erasure operations only
    execution_logs = (
        db.query(ExecutionLog)
        .filter_by(privacy_request_id=pr.id, action_type=ActionType.erasure)
        .all()
    )

    # Find logs for the missing collection
    missing_collection_logs = [
        log
        for log in execution_logs
        if f"{log.dataset_name}:{log.collection_name}" == missing_collection_key
    ]

    # Verify erasure completed successfully for the leaf collection
    assert (
        missing_collection_logs
    ), f"No erasure logs found for {missing_collection_key}"

    complete_logs = [
        log
        for log in missing_collection_logs
        if log.status == ExecutionLogStatus.complete
    ]
    assert (
        complete_logs
    ), f"Expected erasure to complete successfully for leaf collection"


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
@pytest.mark.serial
@pytest.mark.parametrize("dsr_version", ["use_dsr_2_0", "use_dsr_3_0"])
def test_bigquery_missing_tables_handling_erasure_dependency_collection(
    db,
    erasure_policy,
    dsr_version,
    request,
    bigquery_missing_table_resources,
    run_privacy_request_task,
):
    """
    Test BigQuery missing table handling during erasure operations for collections with dependencies:
    - Missing collections with dependencies fail during access (hard error)
    - Erasure phase never runs for these collections
    """
    request.getfixturevalue(dsr_version)

    # Get dataset config for customer (collection with dependencies)
    dataset_config = request.getfixturevalue("bigquery_missing_customer_config")
    missing_collection_key = f"{dataset_config.fides_key}:customer_missing"

    # Create privacy request with erasure policy
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": bigquery_missing_table_resources["email"]},
    }

    # Execute request - should fail due to missing dependency collection
    try:
        pr = get_privacy_request_results(
            db,
            erasure_policy,
            run_privacy_request_task,
            data,
            task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
        )
    except Exception:
        # For dependency errors, get the most recent privacy request
        pr = db.query(PrivacyRequest).order_by(PrivacyRequest.created_at.desc()).first()

    # Verify execution logs for erasure operations only
    execution_logs = (
        db.query(ExecutionLog)
        .filter_by(privacy_request_id=pr.id, action_type=ActionType.erasure)
        .all()
    )

    # Find logs for the missing collection
    missing_collection_logs = [
        log
        for log in execution_logs
        if f"{log.dataset_name}:{log.collection_name}" == missing_collection_key
    ]

    # Verify that erasure never ran for the collection with dependencies
    # Since access failed, erasure phase should not have been attempted
    assert (
        not missing_collection_logs
    ), f"Erasure should not have run for collection with failed dependencies, but found logs: {missing_collection_logs}"
