import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import get_config
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match

CONFIG = get_config()


@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@pytest.mark.integration_saas
def test_unbounce_connection_test(unbounce_connection_config) -> None:
    get_connector(unbounce_connection_config).test_connection()


@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_unbounce_access_request_task(
    db,
    dsr_version,
    request,
    policy,
    privacy_request,
    unbounce_connection_config,
    unbounce_dataset_config,
    unbounce_identity_email,
) -> None:
    """Full access request based on the Unbounce SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": unbounce_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = unbounce_connection_config.get_saas_config().fides_key
    merged_graph = unbounce_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [unbounce_connection_config],
        {"email": unbounce_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:pages"],
        min_size=1,
        keys=[
            "subAccountId",
            "integrations",
            "integrationsCount",
            "integrationsErrorsCount",
            "id",
            "url",
            "metadata",
            "createdAt",
            "name",
            "state",
            "lastPublishedAt",
            "variantsCount",
            "domain",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:leads"],
        min_size=1,
        keys=[
            "created_at",
            "id",
            "extra_data",
            "form_data",
            "page_id",
            "variant_id",
            "metadata",
        ],
    )

    # verify we only returned data for our identity email
    for leads in v[f"{dataset_name}:leads"]:
        assert unbounce_identity_email in leads["form_data"]["email"]


@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_unbounce_erasure_request_task(
    db,
    dsr_version,
    request,
    privacy_request,
    erasure_policy_string_rewrite,
    unbounce_connection_config,
    unbounce_dataset_config,
    unbounce_erasure_identity_email,
    unbounce_create_erasure_data,
) -> None:
    """Full erasure request based on the Unbounce SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow Delete

    identity = Identity(**{"email": unbounce_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = unbounce_connection_config.get_saas_config().fides_key
    merged_graph = unbounce_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [unbounce_connection_config],
        {"email": unbounce_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:pages"],
        min_size=1,
        keys=[
            "subAccountId",
            "integrations",
            "integrationsCount",
            "integrationsErrorsCount",
            "id",
            "url",
            "metadata",
            "createdAt",
            "name",
            "state",
            "lastPublishedAt",
            "variantsCount",
            "domain",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:leads"],
        min_size=1,
        keys=[
            "created_at",
            "id",
            "extra_data",
            "form_data",
            "page_id",
            "variant_id",
            "metadata",
        ],
    )

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [unbounce_connection_config],
        {"email": unbounce_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:pages": 0,
        f"{dataset_name}:leads": 1,
    }

    CONFIG.execution.masking_strict = masking_strict
