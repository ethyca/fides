import random

import pytest

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from fides.core.config import CONFIG
from tests.fixtures.saas.auth0_fixtures import _user_exists
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.test_helpers.saas_test_utils import poll_for_existence


@pytest.mark.integration_saas
@pytest.mark.integration_auth0
def test_auth0_connection_test(auth0_connection_config) -> None:
    get_connector(auth0_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_auth0
async def test_auth0_access_request_task(
    db,
    policy,
    auth0_connection_config,
    auth0_dataset_config,
    auth0_identity_email,
    auth0_access_data,
) -> None:
    """Full access request based on the Auth0 SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_auth0_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": auth0_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = auth0_connection_config.get_saas_config().fides_key
    merged_graph = auth0_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
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
            "last_ip",
            "last_login",
            "logins_count",
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


@pytest.mark.integration_saas
@pytest.mark.integration_auth0
async def test_auth0_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    auth0_connection_config,
    auth0_dataset_config,
    auth0_erasure_identity_email,
    auth0_erasure_data,
    auth0_token,
) -> None:
    """Full erasure request based on the Auth0 SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_auth0_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": auth0_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = auth0_connection_config.get_saas_config().fides_key
    merged_graph = auth0_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
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

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [auth0_connection_config],
        {"email": auth0_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
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
