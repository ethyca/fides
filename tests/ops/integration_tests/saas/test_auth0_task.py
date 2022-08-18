import random

import pytest
import requests
from fidesops.ops.core.config import config
from fidesops.ops.graph.graph import DatasetGraph
from fidesops.ops.models.privacy_request import PrivacyRequest
from fidesops.ops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.ops.task import graph_task
from fidesops.ops.task.graph_task import get_cached_data_for_erasures

from tests.ops.graph.graph_test_util import assert_rows_match


@pytest.mark.skip(reason="Pending development of OAuth2 JWT Bearer authentication")
@pytest.mark.integration_saas
@pytest.mark.integration_auth0
def test_auth0_access_request_task(
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
    identity = PrivacyRequestIdentity(**{"email": auth0_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = auth0_connection_config.get_saas_config().fides_key
    merged_graph = auth0_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
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


@pytest.mark.skip(reason="Pending development of OAuth2 JWT Bearer authentication")
@pytest.mark.integration_saas
@pytest.mark.integration_auth0
def test_auth0_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    auth0_connection_config,
    auth0_dataset_config,
    auth0_erasure_identity_email,
    auth0_erasure_data,
) -> None:
    """Full erasure request based on the auth0 SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_auth0_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": auth0_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = auth0_connection_config.get_saas_config().fides_key
    merged_graph = auth0_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    temp_masking = config.execution.masking_strict
    config.execution.masking_strict = True
    v = graph_task.run_access_request(
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

    x = graph_task.run_erasure(
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

    # Verifying field is masked
    auth0_secrets = auth0_connection_config.secrets
    base_url = f"https://{auth0_secrets['domain']}"
    headers = {
        "Authorization": f"Bearer {auth0_secrets['access_token']}",
    }
    user_response = requests.get(
        url=f"{base_url}/api/v2/users-by-email?email={auth0_erasure_identity_email}",
        headers=headers,
    )
    user = user_response.json()
    assert user[0]["name"] == "MASKED"

    config.execution.masking_strict = temp_masking
