import random
import time
from typing import Any, Dict, List, Optional

import pytest
import requests

from fidesops.graph.graph import DatasetGraph
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.task import graph_task
from fidesops.task.filter_results import filter_data_categories
from fidesops.task.graph_task import get_cached_data_for_erasures
from tests.graph.graph_test_util import assert_rows_match


@pytest.mark.integration_saas
@pytest.mark.integration_sentry
def test_sentry_access_request_task(
    db,
    policy,
    sentry_connection_config,
    sentry_dataset_config,
    sentry_identity_email,
) -> None:
    """Full access request based on the Sentry SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_saas_access_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": sentry_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = sentry_connection_config.get_saas_config().fides_key
    merged_graph = sentry_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [sentry_connection_config],
        {"email": sentry_identity_email},
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

    target_categories = {"user.provided"}
    filtered_results = filter_data_categories(
        v,
        target_categories,
        graph.data_category_field_mapping,
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
        f"https://{secrets['host']}/api/0/projects/{project['organization']['slug']}/{project['slug']}/issues/",
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
    host = sentry_secrets.get("host")

    if not token or not issue_url or not sentry_user_id:
        # Exit early if these haven't been set locally
        return None, None, None

    headers = {"Authorization": f"Bearer {token}"}
    data = {"assignedTo": f"user:{sentry_user_id}"}
    response = requests.put(issue_url, json=data, headers=headers)
    assert response.ok
    assert response.json().get("assignedTo", {}).get("id") == sentry_user_id

    # Get projects
    response = requests.get(f"https://{host}/api/0/projects/", headers=headers)
    assert response.ok
    project = response.json()[0]

    # Wait until issues returns data
    retries = 10
    while _get_issues(project, sentry_secrets, headers) is None:
        if not retries:
            raise Exception(
                "The issues endpoint did not return the required data for testing during the time limit"
            )
        retries -= 1
        time.sleep(5)

    # Temporarily sets the access token to one that works for erasures
    sentry_connection_config.secrets["access_token"] = sentry_secrets[
        "erasure_access_token"
    ]
    sentry_connection_config.save(db)

    # Grab a separate email for erasures
    erasure_email = sentry_secrets["erasure_identity_email"]
    return erasure_email, issue_url, headers


@pytest.mark.integration_saas
@pytest.mark.integration_sentry
def test_sentry_erasure_request_task(
    db, policy, sentry_connection_config, sentry_dataset_config
) -> None:
    """Full erasure request based on the Sentry SaaS config. Also verifies issue data in access request"""
    erasure_email, issue_url, headers = sentry_erasure_test_prep(
        sentry_connection_config, db
    )

    privacy_request = PrivacyRequest(
        id=f"test_saas_access_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": erasure_email})
    privacy_request.cache_identity(identity)

    dataset_name = sentry_connection_config.get_saas_config().fides_key
    merged_graph = sentry_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [sentry_connection_config],
        {"email": erasure_email},
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

    x = graph_task.run_erasure(
        privacy_request,
        policy,
        graph,
        [sentry_connection_config],
        {"email": erasure_email},
        get_cached_data_for_erasures(privacy_request.id),
    )

    # Masking request only issued to "issues" endpoint
    assert x == {
        "sentry_connector:projects": 0,
        "sentry_connector:person": 0,
        "sentry_connector:issues": 1,
        "sentry_connector:organizations": 0,
        "sentry_connector:user_feedback": 0,
        "sentry_connector:employees": 0,
    }

    # Verify the user has been assigned to None
    resp = requests.get(issue_url, headers=headers).json()
    assert resp["assignedTo"] is None
