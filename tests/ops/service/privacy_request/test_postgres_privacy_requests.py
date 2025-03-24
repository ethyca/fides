from unittest import mock
from unittest.mock import Mock

import pytest
from sqlalchemy import column, select, table

from fides.api.graph.config import CollectionAddress, FieldPath
from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.privacy_request import ExecutionLog
from fides.api.schemas.privacy_request import ExecutionLogStatus, PrivacyRequestStatus
from fides.api.util.data_category import DataCategory
from tests.ops.integration_tests.test_execution import get_sorted_execution_logs
from tests.ops.service.privacy_request.test_request_runner_service import (
    PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    get_privacy_request_results,
)


@pytest.mark.integration_postgres
@pytest.mark.integration
@mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_upload_access_results_has_data_category_field_mapping(
    upload_mock: Mock,
    postgres_example_test_dataset_config_read_access,
    postgres_integration_db,
    db,
    policy,
    dsr_version,
    request,
    run_privacy_request_task,
):
    """
    Ensure we are passing along a correctly populated data_category_field_mapping to the 'upload' function
    that publishes the access request output.
    """
    upload_mock.return_value = "http://www.data-download-url"

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

    # sanity check that acccess results returned as expected
    results = pr.get_raw_access_results()
    assert len(results.keys()) == 11

    # what we're really testing - ensure data_category_field_mapping arg is well-populated
    args, kwargs = upload_mock.call_args
    data_category_field_mapping = kwargs["data_category_field_mapping"]

    # make sure the category field mapping generally looks as we expect
    address_mapping = data_category_field_mapping[
        CollectionAddress.from_string("postgres_example_test_dataset:address")
    ]
    assert len(address_mapping) >= 5
    assert address_mapping["user.contact.address.street"] == [
        FieldPath("house"),
        FieldPath("street"),
    ]
    product_mapping = data_category_field_mapping[
        CollectionAddress.from_string("postgres_example_test_dataset:product")
    ]
    assert len(product_mapping) >= 1
    assert product_mapping["system.operations"] == [
        FieldPath(
            "id",
        ),
        FieldPath(
            "name",
        ),
        FieldPath(
            "price",
        ),
    ]


@pytest.mark.integration_postgres
@pytest.mark.integration
@mock.patch("fides.api.service.privacy_request.request_runner_service.upload")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_upload_access_results_has_data_use_map(
    upload_mock: Mock,
    postgres_example_test_dataset_config_read_access,
    postgres_integration_db,
    db,
    policy,
    dsr_version,
    request,
    run_privacy_request_task,
):
    """
    Ensure we are passing along a correctly populated data_use_map to the 'upload' function
    that publishes the access request output.
    """
    upload_mock.return_value = "http://www.data-download-url"

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

    # sanity check that access results returned as expected
    results = pr.get_raw_access_results()
    assert len(results.keys()) == 11

    # what we're really testing - ensure data_use_map arg is well-populated
    args, kwargs = upload_mock.call_args
    data_use_map = kwargs["data_use_map"]

    assert data_use_map == {
        "postgres_example_test_dataset:report": "{'marketing.advertising'}",
        "postgres_example_test_dataset:employee": "{'marketing.advertising'}",
        "postgres_example_test_dataset:customer": "{'marketing.advertising'}",
        "postgres_example_test_dataset:service_request": "{'marketing.advertising'}",
        "postgres_example_test_dataset:visit": "{'marketing.advertising'}",
        "postgres_example_test_dataset:address": "{'marketing.advertising'}",
        "postgres_example_test_dataset:login": "{'marketing.advertising'}",
        "postgres_example_test_dataset:orders": "{'marketing.advertising'}",
        "postgres_example_test_dataset:payment_card": "{'marketing.advertising'}",
        "postgres_example_test_dataset:order_item": "{'marketing.advertising'}",
        "postgres_example_test_dataset:product": "{'marketing.advertising'}",
    }


@pytest.mark.integration_postgres
@pytest.mark.integration
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@pytest.mark.parametrize(
    "dataset_config",
    [
        "postgres_example_test_dataset_config_read_access",
        "postgres_example_test_dataset_config_read_access_without_primary_keys",
    ],
)
def test_create_and_process_access_request_postgres(
    trigger_webhook_mock,
    dataset_config,
    postgres_integration_db,
    db,
    cache,
    dsr_version,
    request,
    policy,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
    request.getfixturevalue(dataset_config)

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
    assert len(results.keys()) == 11

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = "postgres_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    visit_key = result_key_prefix + "visit"
    assert results[visit_key][0]["email"] == customer_email
    log_id = pr.execution_logs[0].id
    pr_id = pr.id

    finished_audit_log: AuditLog = AuditLog.filter(
        db=db,
        conditions=(
            (AuditLog.privacy_request_id == pr_id)
            & (AuditLog.action == AuditLogAction.finished)
        ),
    ).first()

    assert finished_audit_log is not None

    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4

    for webhook in policy_pre_execution_webhooks:
        webhook.delete(db=db)

    for webhook in policy_post_execution_webhooks:
        webhook.delete(db=db)

    policy.delete(db=db)
    pr.delete(db=db)
    assert not pr in db  # Check that `pr` has been expunged from the session
    assert ExecutionLog.get(db, object_id=log_id).privacy_request_id == pr_id


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
def test_create_and_process_access_request_with_custom_identities_postgres(
    trigger_webhook_mock,
    postgres_example_test_dataset_config_read_access,
    postgres_example_test_extended_dataset_config,
    postgres_integration_db,
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
    loyalty_id = "CH-1"
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {
            "email": customer_email,
            "loyalty_id": {"label": "Loyalty ID", "value": loyalty_id},
        },
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

    result_key_prefix = "postgres_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    visit_key = result_key_prefix + "visit"
    assert results[visit_key][0]["email"] == customer_email

    loyalty_key = "postgres_example_test_extended_dataset:loyalty"
    assert results[loyalty_key][0]["id"] == loyalty_id

    log_id = pr.execution_logs[0].id
    pr_id = pr.id

    finished_audit_log: AuditLog = AuditLog.filter(
        db=db,
        conditions=(
            (AuditLog.privacy_request_id == pr_id)
            & (AuditLog.action == AuditLogAction.finished)
        ),
    ).first()

    assert finished_audit_log is not None

    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4

    for webhook in policy_pre_execution_webhooks:
        webhook.delete(db=db)

    for webhook in policy_post_execution_webhooks:
        webhook.delete(db=db)

    policy.delete(db=db)
    pr.delete(db=db)
    assert not pr in db  # Check that `pr` has been expunged from the session
    assert ExecutionLog.get(db, object_id=log_id).privacy_request_id == pr_id


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.usefixtures(
    "postgres_example_test_dataset_config_skipped_login_collection",
    "postgres_integration_db",
    "cache",
)
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_with_valid_skipped_collection(
    db,
    policy,
    run_privacy_request_task,
    dsr_version,
    request,
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
    assert len(results.keys()) == 10

    assert "login" not in results.keys()

    result_key_prefix = "postgres_example_test_dataset:"
    customer_key = result_key_prefix + "customer"
    assert results[customer_key][0]["email"] == customer_email

    assert AuditLog.filter(
        db=db,
        conditions=(
            (AuditLog.privacy_request_id == pr.id)
            & (AuditLog.action == AuditLogAction.finished)
        ),
    ).first()


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.usefixtures(
    "postgres_example_test_dataset_config_skipped_address_collection",
    "postgres_integration_db",
    "cache",
)
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_with_invalid_skipped_collection(
    db,
    policy,
    dsr_version,
    request,
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
    assert len(results.keys()) == 0

    db.refresh(pr)

    assert pr.status == PrivacyRequestStatus.error


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_2_0", "use_dsr_3_0"],
)
def test_create_and_process_access_request_postgres_with_disabled_integration(
    postgres_integration_db,
    postgres_example_test_dataset_config,
    connection_config,
    db,
    dsr_version,
    request,
    policy,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"external_id": "ext-123"},
    }

    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )

    first, *rest = pr.execution_logs.order_by("created_at")

    assert first.dataset_name == "Dataset reference validation"
    assert first.status == ExecutionLogStatus.complete

    for execution_log in rest:
        assert execution_log.dataset_name == "Dataset traversal"
        assert execution_log.status == ExecutionLogStatus.error

    connection_config.disabled = True
    connection_config.save(db=db)

    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )

    logs = get_sorted_execution_logs(db, pr)

    if dsr_version == "use_dsr_3_0":
        assert logs == [
            ("Dataset reference validation", "complete"),
            ("Dataset traversal", "complete"),
            ("Dataset reference validation", "complete"),
        ]
    else:
        assert logs == [
            ("Dataset reference validation", "complete"),
            ("Dataset traversal", "complete"),
        ]


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_specific_category_postgres(
    postgres_integration_db,
    postgres_example_test_dataset_config,
    cache,
    db,
    generate_auth_header,
    erasure_policy,
    dsr_version,
    request,
    read_connection_config,
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

    stmt = select("*").select_from(table("customer"))
    res = postgres_integration_db.execute(stmt).all()

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
    res = postgres_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id == row.id:
            customer_found = True
            # Check that the `name` field is `None`
            assert row.name is None
    assert customer_found


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_generic_category(
    postgres_integration_db,
    postgres_example_test_dataset_config,
    cache,
    db,
    dsr_version,
    request,
    generate_auth_header,
    erasure_policy,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    # It's safe to change this here since the `erasure_policy` fixture is scoped
    # at function level
    target = erasure_policy.rules[0].targets[0]
    target.data_category = DataCategory("user.contact").value
    target.save(db=db)

    email = "customer-2@example.com"
    customer_id = 2
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy.key,
        "identity": {"email": email},
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
        column("email"),
        column("name"),
    ).select_from(table("customer"))
    res = postgres_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id == row.id:
            customer_found = True
            # Check that the `email` field is `None` and that its data category
            # ("user.contact.email") has been erased by the parent
            # category ("user.contact")
            assert row.email is None
            assert row.name is not None
        else:
            # There are two rows other rows, and they should not have been erased
            assert row.email in ["customer-1@example.com", "jane@example.com"]
    assert customer_found


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_aes_generic_category(
    postgres_integration_db,
    postgres_example_test_dataset_config,
    cache,
    db,
    dsr_version,
    request,
    generate_auth_header,
    erasure_policy_aes,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    # It's safe to change this here since the `erasure_policy` fixture is scoped
    # at function level
    target = erasure_policy_aes.rules[0].targets[0]
    target.data_category = DataCategory("user.contact").value
    target.save(db=db)

    email = "customer-2@example.com"
    customer_id = 2
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy_aes.key,
        "identity": {"email": email},
    }

    pr = get_privacy_request_results(
        db,
        erasure_policy_aes,
        run_privacy_request_task,
        data,
    )
    pr.delete(db=db)

    stmt = select(
        column("id"),
        column("email"),
        column("name"),
    ).select_from(table("customer"))
    res = postgres_integration_db.execute(stmt).all()

    customer_found = False
    for row in res:
        if customer_id == row.id:
            customer_found = True
            # Check that the `email` field is not original val and that its data category
            # ("user.contact.email") has been erased by the parent
            # category ("user.contact").
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
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_with_table_joins(
    postgres_integration_db,
    postgres_example_test_dataset_config,
    db,
    cache,
    dsr_version,
    request,
    erasure_policy,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    # It's safe to change this here since the `erasure_policy` fixture is scoped
    # at function level
    target = erasure_policy.rules[0].targets[0]
    target.data_category = DataCategory("user.financial").value
    target.save(db=db)

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
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@pytest.mark.parametrize(
    "dataset_config",
    [
        "postgres_example_test_dataset_config_read_access",
        "postgres_example_test_dataset_config_read_access_without_primary_keys",
    ],
)
def test_create_and_process_erasure_request_read_access(
    postgres_integration_db,
    dataset_config,
    db,
    cache,
    erasure_policy,
    dsr_version,
    request,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
    request.getfixturevalue(dataset_config)

    customer_email = "customer-2@example.com"
    customer_id = 2
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
    errored_execution_logs = pr.execution_logs.filter_by(status="error")
    assert errored_execution_logs.count() == 11
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
        if customer_id == row.id:
            customer_found = True
            # Check that the `name` field is NOT `None`. We couldn't erase, because the ConnectionConfig only had
            # "read" access
            assert row.name is not None
    assert customer_found
