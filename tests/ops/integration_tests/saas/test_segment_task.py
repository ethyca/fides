import random

import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task import graph_task
from fides.api.task.filter_results import filter_data_categories
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import CONFIG
from tests.ops.graph.graph_test_util import assert_rows_match


@pytest.mark.skip(reason="Pending account resolution")
@pytest.mark.integration_saas
def test_segment_connection_test(segment_connection_config) -> None:
    get_connector(segment_connection_config).test_connection()


@pytest.mark.skip(reason="Pending account resolution")
@pytest.mark.integration_saas
@pytest.mark.asyncio
async def test_segment_access_request_task(
    db,
    policy,
    segment_connection_config,
    segment_dataset_config,
    segment_identity_email,
) -> None:
    """Full access request based on the Segment SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_segment_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": segment_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = segment_connection_config.get_saas_config().fides_key
    merged_graph = segment_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [segment_connection_config],
        {"email": segment_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:track_events"],
        min_size=1,
        keys=[
            "external_ids",
            "context",
            "type",
            "source_id",
            "message_id",
            "timestamp",
            "properties",
            "event",
            "related",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:traits"],
        min_size=1,
        keys=[
            "address",
            "age",
            "avatar",
            "description",
            "email",
            "firstName",
            "gender",
            "id",
            "industry",
            "lastName",
            "name",
            "phone",
            "subscriptionStatus",
            "title",
            "username",
            "website",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:segment_user"],
        min_size=1,
        keys=["segment_id", "metadata"],
    )

    assert_rows_match(
        v[f"{dataset_name}:external_ids"],
        min_size=2,
        keys=["id", "type", "source_id", "collection", "created_at", "encoding"],
    )

    target_categories = {"user"}
    filtered_results = filter_data_categories(
        v,
        target_categories,
        graph.data_category_field_mapping,
    )

    assert set(filtered_results.keys()) == {
        f"{dataset_name}:track_events",
        f"{dataset_name}:traits",
        f"{dataset_name}:external_ids",
        f"{dataset_name}:segment_user",
    }

    assert set(filtered_results[f"{dataset_name}:traits"][0].keys()) == {
        "address",
        "title",
        "description",
        "username",
        "gender",
        "phone",
        "id",
        "website",
        "email",
        "name",
        "age",
        "firstName",
    }
    assert (
        filtered_results[f"{dataset_name}:traits"][0]["email"] == segment_identity_email
    )

    assert (
        filtered_results[f"{dataset_name}:track_events"][0]["external_ids"][0]["id"]
        == segment_identity_email
    )
    assert len(filtered_results[f"{dataset_name}:external_ids"]) == 2
    assert (
        filtered_results[f"{dataset_name}:external_ids"][0]["id"]
        == segment_identity_email
    )

    assert filtered_results[f"{dataset_name}:segment_user"][0]["segment_id"]


@pytest.mark.skip(reason="Pending account resolution")
@pytest.mark.integration_saas
@pytest.mark.asyncio
async def test_segment_erasure_request_task(
    db,
    policy,
    segment_connection_config,
    segment_dataset_config,
    segment_erasure_identity_email,
    segment_erasure_data,
) -> None:
    """Full erasure request based on the Segment SaaS config"""

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow GDPR Delete

    # Create user for GDPR delete
    erasure_email = segment_erasure_identity_email
    privacy_request = PrivacyRequest(
        id=f"test_segment_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": erasure_email})
    privacy_request.cache_identity(identity)

    dataset_name = segment_connection_config.get_saas_config().fides_key
    merged_graph = segment_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [segment_connection_config],
        {"email": erasure_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:track_events"],
        min_size=1,
        keys=[
            "external_ids",
            "context",
            "type",
            "source_id",
            "message_id",
            "timestamp",
            "properties",
            "event",
            "related",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:traits"],
        min_size=1,
        keys=[
            "address",
            "age",
            "avatar",
            "description",
            "email",
            "firstName",
            "id",
            "industry",
            "lastName",
            "name",
            "phone",
            "subscriptionStatus",
            "title",
            "username",
            "website",
        ],
    )

    x = await graph_task.run_erasure(
        privacy_request,
        policy,
        graph,
        [segment_connection_config],
        {"email": erasure_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    # Assert erasure request made to segment_user - cannot verify success immediately as this can take
    # days, weeks to process
    assert x == {
        "segment_instance:segment_user": 1,
        "segment_instance:traits": 0,
        "segment_instance:external_ids": 0,
        "segment_instance:track_events": 0,
    }

    CONFIG.execution.masking_strict = masking_strict  # Reset
