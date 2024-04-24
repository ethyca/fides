import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import CONFIG
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match


@pytest.mark.skip(reason="Pending account resolution")
@pytest.mark.integration_saas
def test_rollbar_connection_test(rollbar_connection_config) -> None:
    get_connector(rollbar_connection_config).test_connection()


@pytest.mark.skip(reason="Pending account resolution")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_rollbar_access_request_task(
    db,
    policy,
    rollbar_connection_config,
    rollbar_dataset_config,
    rollbar_identity_email,
    dsr_version,
    request,
    privacy_request,
) -> None:
    """Full access request based on the Rollbar SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": rollbar_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = rollbar_connection_config.get_saas_config().fides_key
    merged_graph = rollbar_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [rollbar_connection_config],
        {"email": rollbar_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:projects"],
        min_size=1,
        keys=["id", "account_id", "status", "date_created", "date_modified", "name"],
    )

    assert_rows_match(
        v[f"{dataset_name}:project_access_tokens"],
        min_size=1,
        keys=[
            "project_id",
            "name",
            "status",
            "date_created",
            "date_modified",
            "scopes",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:instances"],
        min_size=1,
        keys=[
            "id",
            "project_id",
            "timestamp",
            "version",
            "data",
            "billable",
            "item_id",
        ],
    )

    # verify we only returned data for our identity email
    for instance in v[f"{dataset_name}:instances"]:
        assert instance["data"]["person"]["email"] == rollbar_identity_email


@pytest.mark.skip(reason="Pending account resolution")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_rollbar_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    rollbar_connection_config,
    rollbar_dataset_config,
    rollbar_erasure_identity_email,
    rollbar_erasure_data,
    rollbar_test_client,
    dsr_version,
    request,
    privacy_request,
) -> None:
    """Full erasure request based on the Rollbar SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity_kwargs = {"email": rollbar_erasure_identity_email}

    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = rollbar_connection_config.get_saas_config().fides_key
    merged_graph = rollbar_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)
    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [rollbar_connection_config],
        identity_kwargs,
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:projects"],
        min_size=1,
        keys=[
            "id",
            "account_id",
            "name",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:project_access_tokens"],
        min_size=1,
        keys=[
            "project_id",
            "name",
            "access_token",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:instances"],
        min_size=1,
        keys=[
            "id",
            "timestamp",
            "data",
        ],
    )

    # verify we only returned data for our identity email
    for instance in v[f"{dataset_name}:instances"]:
        assert instance["data"]["person"]["email"] == rollbar_erasure_identity_email

    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [rollbar_connection_config],
        identity_kwargs,
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    # verify masking request was issued for endpoints with delete actions
    assert x == {
        f"{dataset_name}:projects": 0,
        f"{dataset_name}:project_access_tokens": 0,
        f"{dataset_name}:instances": 0,
        f"{dataset_name}:people": 1,
    }

    CONFIG.execution.masking_strict = temp_masking
