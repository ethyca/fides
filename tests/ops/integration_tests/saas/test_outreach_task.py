import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.filter_results import filter_data_categories
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import CONFIG
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match


@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@pytest.mark.integration_saas
def test_outreach_connection_test(outreach_connection_config) -> None:
    get_connector(outreach_connection_config).test_connection()


@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_outreach_access_request_task(
    db,
    dsr_version,
    request,
    policy,
    privacy_request,
    outreach_connection_config,
    outreach_dataset_config,
    outreach_identity_email,
) -> None:
    """Full access request based on the Outreach SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": outreach_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = outreach_connection_config.get_saas_config().fides_key
    merged_graph = outreach_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [outreach_connection_config],
        {"email": outreach_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:prospects"],
        min_size=1,
        keys=["type", "id", "attributes", "relationships", "links"],
    )
    assert_rows_match(
        v[f"{dataset_name}:recipients"],
        min_size=1,
        keys=["type", "id", "attributes", "links"],
    )

    # verify we only returned data for our identity email
    assert (
        outreach_identity_email
        in v[f"{dataset_name}:prospects"][0]["attributes"]["emails"]
    )

    assert (
        v[f"{dataset_name}:recipients"][0]["attributes"]["value"]
        == outreach_identity_email
    )

    # verify we keep the expected fields after filtering by the user data category
    target_categories = {"user"}
    filtered_results = filter_data_categories(v, target_categories, graph)

    assert set(filtered_results.keys()) == {
        f"{dataset_name}:prospects",
        f"{dataset_name}:recipients",
    }

    assert set(filtered_results[f"{dataset_name}:prospects"][0].keys()) == {
        "attributes",
    }

    assert set(filtered_results[f"{dataset_name}:recipients"][0].keys()) == {
        "attributes",
    }


@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_outreach_erasure_request_task(
    db,
    dsr_version,
    request,
    privacy_request,
    erasure_policy_string_rewrite,
    outreach_connection_config,
    outreach_dataset_config,
    outreach_erasure_identity_email,
    outreach_create_erasure_data,
) -> None:
    """Full erasure request based on the Outreach SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow Delete

    identity = Identity(**{"email": outreach_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = outreach_connection_config.get_saas_config().fides_key
    merged_graph = outreach_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [outreach_connection_config],
        {"email": outreach_erasure_identity_email},
        db,
    )

    # verify staged data is available for erasure
    assert_rows_match(
        v[f"{dataset_name}:prospects"],
        min_size=1,
        keys=["type", "id", "attributes", "relationships", "links"],
    )
    assert_rows_match(
        v[f"{dataset_name}:recipients"],
        min_size=1,
        keys=["type", "id", "attributes", "links"],
    )

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [outreach_connection_config],
        {"email": outreach_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    # Assert erasure request made to prospects and recipients
    # cannot verify success immediately as this can take days, weeks to process
    assert x == {f"{dataset_name}:prospects": 1, f"{dataset_name}:recipients": 1}

    CONFIG.execution.masking_strict = masking_strict
