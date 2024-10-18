import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import get_config
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.test_helpers.saas_test_utils import poll_for_existence

CONFIG = get_config()


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
def test_aircall_connection_test(aircall_connection_config) -> None:
    get_connector(aircall_connection_config).test_connection()


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_aircall_access_request_task_with_phone_number(
    db,
    policy,
    dsr_version,
    request,
    privacy_request,
    aircall_connection_config,
    aircall_dataset_config,
    aircall_identity_phone_number,
) -> None:
    """Full access request based on the Aircall SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"phone_number": aircall_identity_phone_number})
    privacy_request.cache_identity(identity)

    dataset_name = aircall_connection_config.get_saas_config().fides_key
    merged_graph = aircall_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [aircall_connection_config],
        {"phone_number": aircall_identity_phone_number},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:contact"],
        min_size=1,
        keys=[
            "id",
            "first_name",
            "last_name",
            "company_name",
            "information",
            "is_shared",
            "direct_link",
            "created_at",
            "updated_at",
            "phone_numbers",
            "emails",
        ],
    )

    # verify we only returned data for our identity email
    assert (
        v[f"{dataset_name}:contact"][0]["phone_numbers"][0]["value"]
        == aircall_identity_phone_number
    )


@pytest.mark.skip(reason="Temporarily disabled test")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_aircall_erasure_request_task(
    db,
    privacy_request,
    dsr_version,
    request,
    erasure_policy_string_rewrite,
    aircall_connection_config,
    aircall_dataset_config,
    aircall_erasure_identity_phone_number,
    aircall_erasure_identity_email,
    aircall_create_erasure_data,
    aircall_test_client,
) -> None:
    """Full erasure request based on the Aircall SaaS config"""
    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow Delete

    identity = Identity(**{"phone_number": aircall_erasure_identity_phone_number})
    privacy_request.cache_identity(identity)

    dataset_name = aircall_connection_config.get_saas_config().fides_key
    merged_graph = aircall_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [aircall_connection_config],
        {"phone_number": aircall_erasure_identity_phone_number},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:contact"],
        min_size=1,
        keys=[
            "id",
            "first_name",
            "last_name",
            "company_name",
            "information",
            "is_shared",
            "direct_link",
            "created_at",
            "updated_at",
            "phone_numbers",
            "emails",
        ],
    )

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [aircall_connection_config],
        {"phone_number": aircall_erasure_identity_phone_number},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:contact": 1,
        f"{dataset_name}:calls": 0,
    }

    poll_for_existence(
        aircall_test_client.get_contact,
        (aircall_erasure_identity_phone_number,),
        existence_desired=False,
    )

    CONFIG.execution.masking_strict = masking_strict
