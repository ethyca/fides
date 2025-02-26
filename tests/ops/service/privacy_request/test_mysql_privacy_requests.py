from unittest import mock

import pytest
from sqlalchemy import column, select, table

from tests.ops.service.privacy_request.test_request_runner_service import (
    get_privacy_request_results,
)


@pytest.mark.integration
@pytest.mark.integration_mysql
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_mysql(
    trigger_webhook_mock,
    mysql_example_test_dataset_config,
    mysql_integration_db,
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
    assert len(results.keys()) == 12

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = f"mysql_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    visit_key = result_key_prefix + "visit"
    assert results[visit_key][0]["email"] == customer_email
    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4
    pr.delete(db=db)


@pytest.mark.integration_mysql
@pytest.mark.integration
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_specific_category_mysql(
    mysql_integration_db,
    mysql_example_test_dataset_config,
    cache,
    db,
    dsr_version,
    request,
    generate_auth_header,
    erasure_policy,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = "customer-1@example.com"
    customer_id = 1
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
    )
    pr.delete(db=db)

    stmt = select(
        column("id"),
        column("name"),
    ).select_from(table("customer"))
    res = mysql_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id == row.id:
            customer_found = True
            # Check that the `name` field is `None`
            assert row.name is None
    assert customer_found
