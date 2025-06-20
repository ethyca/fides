from typing import Any, Dict, List, Optional
from unittest import mock

import pytest

from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.privacy_request import ExecutionLog, PrivacyRequest
from fides.api.util.collection_util import Row
from tests.ops.service.privacy_request.test_request_runner_service import (
    get_privacy_request_results,
)

PRIVACY_REQUEST_TASK_TIMEOUT = 5
# External services take much longer to return
PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL = 150


pytest.skip(
    "Skipping entire test file as BQ project has been disabled for now due to costs. Follow-up with enabling these tests on only merges to main.",
    allow_module_level=True,
)


def validate_privacy_request(
    pr: PrivacyRequest,
    user_id: int,
    bigquery_enterprise_test_dataset_collections: List[str],
    access: bool = True,
) -> Dict[str, Optional[List[Row]]]:
    """
    Validates the results of a privacy request with assertions.
    - Checks that all collections have been queried
    - Checks that all keys have a non-empty value
    - Checks that only results for the user_id are returned
    - Checks that the expected number of records are returned for each collection

    Note: The access boolean determines if we are looking at the access or erasure result counts.

    """
    results = pr.get_raw_access_results()

    assert len(results.keys()) == len(bigquery_enterprise_test_dataset_collections)

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    users = results["enterprise_dsr_testing:users"]
    assert len(users) == 1
    user_details = users[0]
    assert user_details["id"] == user_id

    assert (
        len(
            [
                comment["user_id"]
                for comment in results["enterprise_dsr_testing:comments"]
            ]
        )
        == 16
        if access
        else 1
    )
    assert (
        len(
            [post["user_id"] for post in results["enterprise_dsr_testing:post_history"]]
        )
        == 39
        if access
        else 1
    )
    assert (
        len(
            [
                post["title"]
                for post in results[
                    "enterprise_dsr_testing:stackoverflow_posts_partitioned"
                ]
            ]
        )
        == 30
        if access
        else 1
    )

    return results


def validate_erasure_privacy_request(
    bigquery_enterprise_resources: dict[str, Any], user_id: int
) -> None:
    """Validates the results of an erasure request with assertions."""
    bigquery_client = bigquery_enterprise_resources["client"]
    post_history_id = bigquery_enterprise_resources["post_history_id"]
    comment_id = bigquery_enterprise_resources["comment_id"]
    post_id = bigquery_enterprise_resources["post_id"]
    with bigquery_client.connect() as connection:
        stmt = f"select text from enterprise_dsr_testing.post_history where id = {post_history_id};"
        res = connection.execute(stmt).all()
        assert len(res) == 1
        for row in res:
            assert row.text is None

        stmt = f"select user_display_name, text from enterprise_dsr_testing.comments where id = {comment_id};"
        res = connection.execute(stmt).all()
        assert len(res) == 1
        for row in res:
            assert row.user_display_name is None
            assert row.text is None

        stmt = f"select owner_user_id, owner_display_name, body from enterprise_dsr_testing.stackoverflow_posts_partitioned where id = {post_id};"
        res = connection.execute(stmt).all()
        assert len(res) == 1
        for row in res:
            assert (
                row.owner_user_id == bigquery_enterprise_resources["user_id"]
            )  # not targeted by policy
            assert row.owner_display_name is None
            assert row.body is None

        stmt = f"select display_name, about_me, location, account_internal from enterprise_dsr_testing.users where id = {user_id};"
        res = connection.execute(stmt).all()
        assert len(res) == 1
        for row in res:
            assert row.about_me is None
            assert row.display_name is None
            assert row.location is None
            # assert nested fields are appropriately handled
            for item in row.account_internal:
                assert item["tags"] == []
                assert item["account_type"] is not None  # not targeted by policy


@pytest.mark.integration_bigquery
@pytest.mark.integration_external
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0"],
)
@pytest.mark.parametrize(
    "bigquery_fixtures",
    [
        "bigquery_enterprise_test_dataset_config",
    ],
)
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
def test_access_request(
    trigger_webhook_mock,
    db,
    cache,
    policy,
    dsr_version,
    bigquery_fixtures,
    request,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    run_privacy_request_task,
    bigquery_enterprise_test_dataset_collections,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test DSR 3.0
    request.getfixturevalue(
        bigquery_fixtures
    )  # required to test partitioning and non-partitioned tables

    customer_email = "customer-1@example.com"
    user_id = (
        1754  # this is a real (not generated) user id in the Stack Overflow dataset
    )
    data = {
        "requested_at": "2024-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {
            "email": customer_email,
            "stackoverflow_user_id": {
                "label": "Stackoverflow User Id",
                "value": user_id,
            },
        },
    }

    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
        PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )

    validate_privacy_request(pr, user_id, bigquery_enterprise_test_dataset_collections)

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


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0"],
)
@pytest.mark.parametrize(
    "bigquery_fixtures",
    [
        "bigquery_enterprise_resources",
        "bigquery_enterprise_resources_with_partitioning",
    ],
)
def test_erasure_request(
    db,
    request,
    policy,
    cache,
    dsr_version,
    bigquery_fixtures,
    bigquery_enterprise_erasure_policy,
    run_privacy_request_task,
    bigquery_enterprise_test_dataset_collections,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test DSR 3.0
    bigquery_enterprise_resources = request.getfixturevalue(bigquery_fixtures)

    # first test access request against manually added data
    user_id = bigquery_enterprise_resources["user_id"]
    customer_email = "customer-1@example.com"
    data = {
        "requested_at": "2024-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {
            "email": customer_email,
            "stackoverflow_user_id": {
                "label": "Stackoverflow User Id",
                "value": user_id,
            },
        },
    }

    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
        PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )

    validate_privacy_request(
        pr, user_id, bigquery_enterprise_test_dataset_collections, False
    )

    data = {
        "requested_at": "2024-08-30T16:09:37.359Z",
        "policy_key": bigquery_enterprise_erasure_policy.key,
        "identity": {
            "email": customer_email,
            "stackoverflow_user_id": {
                "label": "Stackoverflow User Id",
                "value": user_id,
            },
        },
    }

    # Should erase all user data
    pr = get_privacy_request_results(
        db,
        bigquery_enterprise_erasure_policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    pr.delete(db=db)

    validate_erasure_privacy_request(bigquery_enterprise_resources, user_id)


@pytest.mark.integration_bigquery
@pytest.mark.integration_external
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0"],
)
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
def test_access_request_multiple_custom_identities(
    trigger_webhook_mock,
    bigquery_enterprise_test_dataset_config,
    db,
    cache,
    policy,
    dsr_version,
    request,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    run_privacy_request_task,
    bigquery_enterprise_test_dataset_collections,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    user_id = (
        1754  # this is a real (not generated) user id in the Stackoverflow dataset
    )
    data = {
        "requested_at": "2024-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {
            "loyalty_id": {"label": "Loyalty ID", "value": "CH-1"},
            "stackoverflow_user_id": {
                "label": "Stackoverflow User Id",
                "value": user_id,
            },
        },
    }

    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
        PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )

    validate_privacy_request(pr, user_id, bigquery_enterprise_test_dataset_collections)

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


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0"],
)
@pytest.mark.parametrize(
    "bigquery_fixtures",
    [
        "bigquery_enterprise_resources",
        "bigquery_enterprise_resources_with_partitioning",
    ],
)
def test_erasure_request_multiple_custom_identities(
    db,
    request,
    policy,
    cache,
    dsr_version,
    bigquery_fixtures,
    bigquery_enterprise_erasure_policy,
    run_privacy_request_task,
    bigquery_enterprise_test_dataset_collections,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
    bigquery_enterprise_resources = request.getfixturevalue(bigquery_fixtures)

    # first test access request against manually added data
    user_id = bigquery_enterprise_resources["user_id"]
    data = {
        "requested_at": "2024-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {
            "loyalty_id": {"label": "Loyalty ID", "value": "CH-1"},
            "stackoverflow_user_id": {
                "label": "Stackoverflow User Id",
                "value": user_id,
            },
        },
    }

    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
        PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )

    validate_privacy_request(
        pr, user_id, bigquery_enterprise_test_dataset_collections, False
    )

    data = {
        "requested_at": "2024-08-30T16:09:37.359Z",
        "policy_key": bigquery_enterprise_erasure_policy.key,
        "identity": {
            "stackoverflow_user_id": {
                "label": "Stackoverflow User Id",
                "value": bigquery_enterprise_resources["user_id"],
            },
        },
    }

    # Should erase all user data
    pr = get_privacy_request_results(
        db,
        bigquery_enterprise_erasure_policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    pr.delete(db=db)

    validate_erasure_privacy_request(bigquery_enterprise_resources, user_id)
