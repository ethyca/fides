from unittest import mock

import pytest

from fides.api.schemas.privacy_request import ExecutionLogStatus
from tests.ops.service.privacy_request.test_request_runner_service import (
    get_privacy_request_results,
)


@pytest.mark.integration
@pytest.mark.integration_scylladb
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_scylladb(
    trigger_webhook_mock,
    scylladb_test_dataset_config,
    scylla_reset_db,
    db,
    cache,
    policy,
    dsr_version,
    request,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = "customer-1@example.com"
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
    )

    results = pr.get_raw_access_results()
    assert len(results.keys()) == 4

    assert "scylladb_example_test_dataset:users" in results
    assert len(results["scylladb_example_test_dataset:users"]) == 1
    assert results["scylladb_example_test_dataset:users"][0]["email"] == customer_email
    assert results["scylladb_example_test_dataset:users"][0]["age"] == 41
    assert results["scylladb_example_test_dataset:users"][0][
        "alternative_contacts"
    ] == {"phone": "+1 (531) 988-5905", "work_email": "customer-1@example.com"}

    assert "scylladb_example_test_dataset:user_activity" in results
    assert len(results["scylladb_example_test_dataset:user_activity"]) == 3

    for activity in results["scylladb_example_test_dataset:user_activity"]:
        assert activity["user_id"]
        assert activity["timestamp"]
        assert activity["activity_type"]
        assert activity["user_agent"]

    assert "scylladb_example_test_dataset:payment_methods" in results
    assert len(results["scylladb_example_test_dataset:payment_methods"]) == 2
    for payment_method in results["scylladb_example_test_dataset:payment_methods"]:
        assert payment_method["payment_method_id"]
        assert payment_method["card_number"]
        assert payment_method["expiration_date"]

    assert "scylladb_example_test_dataset:orders" in results
    assert len(results["scylladb_example_test_dataset:orders"]) == 2
    for payment_method in results["scylladb_example_test_dataset:orders"]:
        assert payment_method["order_amount"]
        assert payment_method["order_date"]
        assert payment_method["order_description"]

    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4
    pr.delete(db=db)


@pytest.mark.integration
@pytest.mark.integration_scylladb
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0"],
)
def test_create_and_process_access_request_scylladb_no_keyspace(
    trigger_webhook_mock,
    scylladb_test_dataset_config_no_keyspace,
    scylla_reset_db,
    db,
    cache,
    policy,
    dsr_version,
    request,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = "customer-1@example.com"
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
    )

    assert (
        pr.access_tasks.count() == 6
    )  # There's 4 tables plus the root and terminal "dummy" tasks

    # Root task should be completed
    assert pr.access_tasks.first().collection_name == "__ROOT__"
    assert pr.access_tasks.first().status == ExecutionLogStatus.complete

    # All other tasks should be error
    for access_task in pr.access_tasks.offset(1):
        assert access_task.status == ExecutionLogStatus.error

    results = pr.get_raw_access_results()
    assert results == {}
