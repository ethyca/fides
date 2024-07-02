from typing import Any, Dict, List, Optional

import pytest
import requests

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.filter_results import filter_data_categories
from fides.api.task.graph_task import get_cached_data_for_erasures
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.test_helpers.saas_test_utils import poll_for_existence


@pytest.mark.skip(reason="Pending account resolution")
@pytest.mark.integration_saas
def test_sentry_connection_test(sentry_connection_config) -> None:
    get_connector(sentry_connection_config).test_connection()


@pytest.mark.skip(reason="Pending account resolution")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_sentry_access_request_task(
    db,
    dsr_version,
    request,
    policy,
    privacy_request,
    sentry_connection_config,
    sentry_dataset_config,
    sentry_identity_email,
) -> None:
    """Full access request based on the Sentry SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": sentry_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = sentry_connection_config.get_saas_config().fides_key
    merged_graph = sentry_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [sentry_connection_config],
        {"email": sentry_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:organizations"],
        min_size=1,
        keys=[
            "id",
            "slug",
            "status",
            "name",
            "dateCreated",
            "isEarlyAdopter",
            "require2FA",
            "requireEmailVerification",
            "avatar",
            "features",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:employees"],
        min_size=1,
        keys=[
            "id",
            "email",
            "name",
            "user",
            "role",
            "roleName",
            "pending",
            "expired",
            "flags",
            "dateCreated",
            "inviteStatus",
            "inviterName",
            "projects",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:projects"],
        min_size=3,
        keys=[
            "id",
            "slug",
            "name",
            "isPublic",
            "isBookmarked",
            "color",
            "dateCreated",
            "firstEvent",
            "firstTransactionEvent",
            "hasSessions",
            "features",
            "status",
            "platform",
            "isInternal",
            "isMember",
            "hasAccess",
            "avatar",
            "organization",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:user_feedback"],
        min_size=1,
        keys=[
            "id",
            "eventID",
            "name",
            "email",
            "comments",
            "dateCreated",
            "user",
            "event",
            "issue",
        ],
    )

    # Person returns empty dicts
    assert_rows_match(
        v[f"{dataset_name}:person"],
        min_size=1,
        keys=[
            "id",
            "hash",
            "tagValue",
            "identifier",
            "username",
            "email",
            "name",
            "ipAddress",
            "dateCreated",
            "avatarUrl",
        ],
    )

    target_categories = {"user"}
    filtered_results = filter_data_categories(
        v,
        target_categories,
        graph,
    )

    assert set(filtered_results.keys()) == {
        f"{dataset_name}:person",
        f"{dataset_name}:employees",
        f"{dataset_name}:user_feedback",
    }

    assert set(filtered_results[f"{dataset_name}:person"][0].keys()) == {
        "email",
        "name",
        "username",
    }
    assert (
        filtered_results[f"{dataset_name}:person"][0]["email"] == sentry_identity_email
    )

    assert set(filtered_results[f"{dataset_name}:employees"][0].keys()) == {
        "email",
        "user",
        "name",
    }
    assert (
        filtered_results[f"{dataset_name}:employees"][0]["email"]
        == sentry_identity_email
    )
    assert set(filtered_results[f"{dataset_name}:employees"][0]["user"].keys()) == {
        "email",
        "name",
        "avatarUrl",
        "username",
        "emails",
    }

    assert (
        filtered_results[f"{dataset_name}:employees"][0]["user"]["email"]
        == sentry_identity_email
    )
    assert filtered_results[f"{dataset_name}:employees"][0]["user"]["emails"] == [
        {"email": sentry_identity_email}
    ]

    assert set(filtered_results[f"{dataset_name}:user_feedback"][0].keys()) == {
        "email",
        "user",
        "comments",
        "name",
    }
    assert (
        filtered_results[f"{dataset_name}:user_feedback"][0]["email"]
        == sentry_identity_email
    )

    assert set(filtered_results[f"{dataset_name}:user_feedback"][0]["user"].keys()) == {
        "email",
        "name",
        "username",
    }
    assert (
        filtered_results[f"{dataset_name}:user_feedback"][0]["user"]["email"]
        == sentry_identity_email
    )


def _get_issues(
    project: Dict[str, Any],
    secrets: Dict[str, Any],
    headers: Dict[str, Any],
) -> Optional[List[Dict[str, Any]]]:
    response = requests.get(
        f"https://{secrets['domain']}/api/0/projects/{project['organization']['slug']}/{project['slug']}/issues/",
        headers=headers,
    )
    json = response.json()
    return json if response.ok and len(json) else None


def sentry_erasure_test_prep(sentry_connection_config, db):
    sentry_secrets = sentry_connection_config.secrets
    # Set the assignedTo field on a sentry issue to a given employee
    token = sentry_secrets.get("erasure_access_token")
    issue_url = sentry_secrets.get("issue_url")
    sentry_user_id = sentry_secrets.get("user_id_erasure")
    domain = sentry_secrets.get("domain")

    if not token or not issue_url or not sentry_user_id:
        # Exit early if these haven't been set locally
        return None, None, None

    headers = {"Authorization": f"Bearer {token}"}
    data = {"assignedTo": f"user:{sentry_user_id}"}
    response = requests.put(issue_url, json=data, headers=headers)
    assert response.ok
    assert response.json().get("assignedTo", {}).get("id") == sentry_user_id

    # Get projects
    response = requests.get(f"https://{domain}/api/0/projects/", headers=headers)
    assert response.ok
    project = response.json()[0]

    # Wait until issues returns data
    error_message = "The issues endpoint did not return the required data for testing during the time limit"
    poll_for_existence(
        _get_issues, (project, sentry_secrets, headers), error_message=error_message
    )

    # Temporarily sets the access token to one that works for erasures
    sentry_connection_config.secrets["access_token"] = sentry_secrets[
        "erasure_access_token"
    ]
    sentry_connection_config.save(db)

    # Grab a separate email for erasures
    erasure_email = sentry_secrets["erasure_identity_email"]
    return erasure_email, issue_url, headers


@pytest.mark.skip(reason="Pending account resolution")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_sentry_erasure_request_task(
    db,
    dsr_version,
    request,
    erasure_policy,
    privacy_request_with_erasure_policy,
    sentry_connection_config,
    sentry_dataset_config,
) -> None:
    """
    Full erasure request based on the Sentry SaaS config.
    Also verifies issue data in access request.
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    erasure_email, issue_url, headers = sentry_erasure_test_prep(
        sentry_connection_config, db
    )

    identity = Identity(**{"email": erasure_email})
    privacy_request_with_erasure_policy.cache_identity(identity)

    dataset_name = sentry_connection_config.get_saas_config().fides_key
    merged_graph = sentry_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request_with_erasure_policy,
        erasure_policy,
        graph,
        [sentry_connection_config],
        {"email": erasure_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:organizations"],
        min_size=1,
        keys=[
            "id",
            "slug",
            "status",
            "name",
            "dateCreated",
            "isEarlyAdopter",
            "require2FA",
            "requireEmailVerification",
            "avatar",
            "features",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:employees"],
        min_size=1,
        keys=[
            "id",
            "email",
            "name",
            "user",
            "role",
            "roleName",
            "pending",
            "expired",
            "flags",
            "dateCreated",
            "inviteStatus",
            "inviterName",
            "projects",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:issues"],
        min_size=1,
        keys=[
            "id",
            "shareId",
            "shortId",
            "title",
            "culprit",
            "permalink",
            "logger",
            "level",
            "status",
            "statusDetails",
            "isPublic",
            "platform",
            "project",
            "type",
            "metadata",
            "numComments",
            "assignedTo",
            "isBookmarked",
            "isSubscribed",
            "subscriptionDetails",
            "hasSeen",
            "annotations",
            "isUnhandled",
            "count",
            "userCount",
            "firstSeen",
            "lastSeen",
            "stats",
        ],
    )

    assert v[f"{dataset_name}:issues"][0]["assignedTo"]["email"] == erasure_email

    x = erasure_runner_tester(
        privacy_request_with_erasure_policy,
        erasure_policy,
        graph,
        [sentry_connection_config],
        {"email": erasure_email},
        get_cached_data_for_erasures(privacy_request_with_erasure_policy.id),
        db,
    )

    # Masking request only issued to "issues" endpoint
    assert x == {
        "sentry_instance:projects": 0,
        "sentry_instance:person": 0,
        "sentry_instance:issues": 1,
        "sentry_instance:organizations": 0,
        "sentry_instance:user_feedback": 0,
        "sentry_instance:employees": 0,
    }

    # Verify the user has been assigned to None
    resp = requests.get(issue_url, headers=headers).json()
    assert resp["assignedTo"] is None
