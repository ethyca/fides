from time import sleep
from unittest import mock

import pytest
from loguru import logger

from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.privacy_request import ExecutionLog
from tests.ops.service.privacy_request.test_request_runner_service import (
    get_privacy_request_results,
)
from tests.ops.test_helpers.saas_test_utils import poll_for_existence

PRIVACY_REQUEST_TASK_TIMEOUT = 5
# External services take much longer to return
PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL = 150


@pytest.mark.skip
@pytest.mark.integration_bigquery
@pytest.mark.integration_external
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_2_0", "use_dsr_3_0"],
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
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
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

    results = pr.get_raw_access_results()
    assert len(results.keys()) == 5

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
    )
    assert (
        len(
            [post["user_id"] for post in results["enterprise_dsr_testing:post_history"]]
        )
        == 39
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
    )

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
    ["use_dsr_3_0", "use_dsr_2_0"],
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
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
    bigquery_enterprise_resources = request.getfixturevalue(bigquery_fixtures)
    bigquery_client = bigquery_enterprise_resources["client"]

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

    results = pr.get_raw_access_results()
    assert len(results.keys()) == 5

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
        == 1
    )
    assert (
        len(
            [post["user_id"] for post in results["enterprise_dsr_testing:post_history"]]
        )
        == 1
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
        == 1
    )

    data = {
        "requested_at": "2024-08-30T16:09:37.359Z",
        "policy_key": bigquery_enterprise_erasure_policy.key,
        "identity": {
            "email": customer_email,
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

    bigquery_client = bigquery_enterprise_resources["client"]
    post_history_id = bigquery_enterprise_resources["post_history_id"]
    comment_id = bigquery_enterprise_resources["comment_id"]
    post_id = bigquery_enterprise_resources["post_id"]

    def bigquery_data_present(
        bigquery_client, post_history_id, comment_id, post_id
    ) -> bool:
        with bigquery_client.connect() as connection:
            stmt = f"select text from enterprise_dsr_testing.post_history where id = {post_history_id};"
            res = connection.execute(stmt).all()
            for row in res:
                if row.text is not None:
                    logger.info(f"row.text {row.text}")
                    return True

            stmt = f"select user_display_name, text from enterprise_dsr_testing.comments where id = {comment_id};"
            res = connection.execute(stmt).all()
            for row in res:
                if row.user_display_name is not None or row.text is not None:
                    return True

            stmt = f"select owner_user_id, owner_display_name, body from enterprise_dsr_testing.stackoverflow_posts_partitioned where id = {post_id};"
            res = connection.execute(stmt).all()
            for row in res:
                assert (
                    row.owner_user_id == bigquery_enterprise_resources["user_id"]
                )  # not targeted by policy
                if row.owner_display_name is not None or row.body is not None:
                    return True

            stmt = f"select display_name, location from enterprise_dsr_testing.users where id = {user_id};"
            res = connection.execute(stmt).all()
            for row in res:
                if row.display_name is not None or row.location is not None:
                    return True

        return False

    poll_for_existence(
        bigquery_data_present,
        (bigquery_client, post_history_id, comment_id, post_id),
        existence_desired=False,
    )


@pytest.mark.skip
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

    results = pr.get_raw_access_results()
    assert len(results.keys()) == 5

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
    )
    assert (
        len(
            [post["user_id"] for post in results["enterprise_dsr_testing:post_history"]]
        )
        == 39
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
    )

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


@pytest.mark.skip
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
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
    bigquery_enterprise_resources = request.getfixturevalue(bigquery_fixtures)
    bigquery_client = bigquery_enterprise_resources["client"]

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

    results = pr.get_raw_access_results()
    assert len(results.keys()) == 5

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
        == 1
    )
    assert (
        len(
            [post["user_id"] for post in results["enterprise_dsr_testing:post_history"]]
        )
        == 1
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
        == 1
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

    bigquery_client = bigquery_enterprise_resources["client"]
    post_history_id = bigquery_enterprise_resources["post_history_id"]
    comment_id = bigquery_enterprise_resources["comment_id"]
    post_id = bigquery_enterprise_resources["post_id"]
    with bigquery_client.connect() as connection:
        stmt = f"select text from enterprise_dsr_testing.post_history where id = {post_history_id};"
        res = connection.execute(stmt).all()
        for row in res:
            assert row.text is None

        stmt = f"select user_display_name, text from enterprise_dsr_testing.comments where id = {comment_id};"
        res = connection.execute(stmt).all()
        for row in res:
            assert row.user_display_name is None
            assert row.text is None

        stmt = f"select owner_user_id, owner_display_name, body from enterprise_dsr_testing.stackoverflow_posts_partitioned where id = {post_id};"
        res = connection.execute(stmt).all()
        for row in res:
            assert (
                row.owner_user_id == bigquery_enterprise_resources["user_id"]
            )  # not targeted by policy
            assert row.owner_display_name is None
            assert row.body is None

        stmt = f"select display_name, location from enterprise_dsr_testing.users where id = {user_id};"
        res = connection.execute(stmt).all()
        for row in res:
            assert row.display_name is None
            assert row.location is None
