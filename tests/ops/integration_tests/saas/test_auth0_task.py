import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import CONFIG
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.fixtures.saas.auth0_fixtures import _user_exists
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.test_helpers.saas_test_utils import poll_for_existence


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
def test_auth0_connection_test(auth0_connection_config) -> None:
    get_connector(auth0_connection_config).test_connection()


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_auth0_access_request_task(
    db,
    policy,
    auth0_connection_config,
    auth0_dataset_config,
    auth0_identity_email,
    auth0_access_data,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Full access request based on the Auth0 SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": auth0_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = auth0_connection_config.get_saas_config().fides_key
    merged_graph = auth0_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [auth0_connection_config],
        {"email": auth0_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:users"],
        min_size=1,
        keys=[
            "created_at",
            "email",
            "email_verified",
            "identities",
            "name",
            "nickname",
            "picture",
            "updated_at",
            "user_id",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:user_logs"],
        min_size=1,
        keys=[
            "date",
            "type",
            "description",
            "connection_id",
            "client_name",
            "ip",
            "user_agent",
            "details",
            "user_id",
            "user_name",
            "log_id",
            "_id",
            "isMobile",
            "location_info",
        ],
    )


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_auth0_erasure_request_task(
    db,
    erasure_policy_string_rewrite,
    auth0_connection_config,
    auth0_dataset_config,
    auth0_erasure_identity_email,
    auth0_erasure_data,
    auth0_token,
    privacy_request_with_erasure_policy,
    dsr_version,
    request,
) -> None:
    """Full erasure request based on the Auth0 SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request_with_erasure_policy.policy_id = erasure_policy_string_rewrite.id
    privacy_request_with_erasure_policy.save(db)

    identity = Identity(**{"email": auth0_erasure_identity_email})
    privacy_request_with_erasure_policy.cache_identity(identity)

    dataset_name = auth0_connection_config.get_saas_config().fides_key
    merged_graph = auth0_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False

    v = access_runner_tester(
        privacy_request_with_erasure_policy,
        erasure_policy_string_rewrite,
        graph,
        [auth0_connection_config],
        {"email": auth0_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:users"],
        min_size=1,
        keys=[
            "created_at",
            "email",
            "email_verified",
            "family_name",
            "given_name",
            "identities",
            "name",
            "nickname",
            "picture",
            "updated_at",
            "user_id",
        ],
    )

    x = erasure_runner_tester(
        privacy_request_with_erasure_policy,
        erasure_policy_string_rewrite,
        graph,
        [auth0_connection_config],
        {"email": auth0_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request_with_erasure_policy.id),
        db,
    )
    assert x == {
        f"{dataset_name}:users": 1,
        f"{dataset_name}:user_logs": 0,
    }

    # Verifying user is deleted
    poll_for_existence(
        _user_exists,
        (auth0_erasure_identity_email, auth0_connection_config.secrets, auth0_token),
        existence_desired=False,
    )

    CONFIG.execution.masking_strict = temp_masking
