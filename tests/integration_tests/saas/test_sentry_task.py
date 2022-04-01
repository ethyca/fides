from fidesops.task.filter_results import filter_data_categories
import pytest
import random

from fidesops.graph.graph import DatasetGraph
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.redis_cache import PrivacyRequestIdentity

from fidesops.task import graph_task
from tests.graph.graph_test_util import assert_rows_match

@pytest.mark.integration_saas
@pytest.mark.integration_sentry
def test_sentry_saas_access_request_task(
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

    # TODO add test for issues once data is populated

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

    assert set(
        filtered_results[f"{dataset_name}:user_feedback"][0]["user"].keys()
    ) == {
        "email",
        "name",
        "username",
    }
    assert (
        filtered_results[f"{dataset_name}:user_feedback"][0]["user"]["email"]
        == sentry_identity_email
    )
