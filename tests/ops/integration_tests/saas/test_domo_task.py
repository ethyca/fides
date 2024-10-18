import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import CONFIG
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.skip(reason="Pending account resolution")
@pytest.mark.integration_saas
def test_domo_connection_test(domo_connection_config) -> None:
    get_connector(domo_connection_config).test_connection()


@pytest.mark.skip(reason="Pending account resolution")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_domo_access_request_task(
    policy,
    dsr_version,
    request,
    privacy_request,
    domo_identity_email,
    domo_connection_config,
    domo_dataset_config,
    db,
) -> None:
    """Full access request based on the Domo SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity_kwargs = {"email": domo_identity_email}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = domo_connection_config.get_saas_config().fides_key
    merged_graph = domo_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [domo_connection_config],
        identity_kwargs,
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:user"],
        min_size=1,
        keys=[
            "id",
            "title",
            "email",
            "role",
            "name",
            "department",
            "roleId",
            "createdAt",
            "updatedAt",
        ],
    )

    # verify we only returned data for our identity
    assert v[f"{dataset_name}:user"][0]["email"] == domo_identity_email


@pytest.mark.skip(reason="Pending account resolution")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_domo_erasure_request_task(
    db,
    dsr_version,
    request,
    privacy_request,
    erasure_policy_string_rewrite_name_and_email,
    domo_erasure_identity_email,
    domo_create_erasure_data,
    domo_test_client,
    domo_connection_config,
    domo_dataset_config,
) -> None:
    """Full access request based on the Domo SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    user_id = domo_create_erasure_data
    privacy_request.policy_id = erasure_policy_string_rewrite_name_and_email.id
    privacy_request.save(db)

    identity_kwargs = {"email": domo_erasure_identity_email}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = domo_connection_config.get_saas_config().fides_key
    merged_graph = domo_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite_name_and_email,
        graph,
        [domo_connection_config],
        identity_kwargs,
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:user"],
        min_size=1,
        keys=[
            "id",
            "title",
            "email",
            "alternateEmail",
            "role",
            "phone",
            "name",
            "roleId",
            "createdAt",
            "updatedAt",
        ],
    )

    # verify we only returned data for our identity
    assert v[f"{dataset_name}:user"][0]["email"] == domo_erasure_identity_email

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = True

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite_name_and_email,
        graph,
        [domo_connection_config],
        identity_kwargs,
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )
    assert x == {f"{dataset_name}:user": 1}
    user_response = domo_test_client.get_user(user_id)
    user = user_response.json()
    assert user["title"] == "MASKED"
    assert user["name"] == "MASKED"
    assert user["email"] == f"{privacy_request.id}@company.com"
    assert user["alternateEmail"] == f"{privacy_request.id}@company.com"

    # reset
    CONFIG.execution.masking_strict = masking_strict
