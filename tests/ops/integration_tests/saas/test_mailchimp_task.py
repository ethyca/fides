import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match


@pytest.mark.integration_saas
def test_mailchimp_connection_test(mailchimp_connection_config) -> None:
    get_connector(mailchimp_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_mailchimp_access_request_task(
    db,
    policy,
    mailchimp_connection_config,
    mailchimp_dataset_config,
    mailchimp_identity_email,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Full access request based on the Mailchimp SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": mailchimp_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = mailchimp_connection_config.get_saas_config().fides_key
    merged_graph = mailchimp_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
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
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_mailchimp_erasure_request_task(
    db,
    privacy_request,
    erasure_policy_string_rewrite,
    mailchimp_connection_config,
    mailchimp_dataset_config,
    mailchimp_identity_email,
    reset_mailchimp_data,
    dsr_version,
    request,
) -> None:
    """Full erasure request based on the Mailchimp SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    identity = Identity(**{"email": mailchimp_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = mailchimp_connection_config.get_saas_config().fides_key
    merged_graph = mailchimp_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [mailchimp_connection_config],
        {"email": mailchimp_identity_email},
        db,
    )

    x = erasure_runner_tester(
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
