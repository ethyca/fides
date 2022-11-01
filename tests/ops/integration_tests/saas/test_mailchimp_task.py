import random

import pytest

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import ExecutionLog, PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from tests.ops.graph.graph_test_util import assert_rows_match, records_matching_fields


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp
def test_mailchimp_connection_test(mailchimp_connection_config) -> None:
    get_connector(mailchimp_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp
@pytest.mark.asyncio
async def test_mailchimp_access_request_task(
    db,
    policy,
    mailchimp_connection_config,
    mailchimp_dataset_config,
    mailchimp_identity_email,
) -> None:
    """Full access request based on the Mailchimp SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_mailchimp_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": mailchimp_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = mailchimp_connection_config.get_saas_config().fides_key
    merged_graph = mailchimp_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [mailchimp_connection_config],
        {"email": mailchimp_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:member"],
        min_size=1,
        keys=[
            "id",
            "list_id",
            "email_address",
            "unique_email_id",
            "web_id",
            "email_type",
            "status",
            "merge_fields",
            "ip_signup",
            "timestamp_signup",
            "ip_opt",
            "timestamp_opt",
            "language",
            "email_client",
            "location",
            "source",
            "tags",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:conversations"],
        min_size=2,
        keys=["id", "campaign_id", "list_id", "from_email", "from_label", "subject"],
    )
    assert_rows_match(
        v[f"{dataset_name}:messages"],
        min_size=3,
        keys=[
            "id",
            "conversation_id",
            "from_label",
            "from_email",
            "subject",
            "message",
            "read",
            "timestamp",
        ],
    )

    # links
    assert v[f"{dataset_name}:member"][0]["email_address"] == mailchimp_identity_email


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp
@pytest.mark.asyncio
async def test_mailchimp_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    mailchimp_connection_config,
    mailchimp_dataset_config,
    mailchimp_identity_email,
    reset_mailchimp_data,
) -> None:
    """Full erasure request based on the Mailchimp SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_mailchimp_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": mailchimp_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = mailchimp_connection_config.get_saas_config().fides_key
    merged_graph = mailchimp_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [mailchimp_connection_config],
        {"email": mailchimp_identity_email},
        db,
    )

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [mailchimp_connection_config],
        {"email": mailchimp_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:member": 1,
        f"{dataset_name}:conversations": 0,
        f"{dataset_name}:messages": 0,
    }
