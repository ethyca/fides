import random

import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task import graph_task
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import CONFIG
from tests.fixtures.saas.fullstory_fixtures import FullstoryTestClient, user_updated
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.test_helpers.saas_test_utils import poll_for_existence


@pytest.mark.skip(reason="API keys are temporary for free accounts")
@pytest.mark.integration_saas
def test_fullstory_connection_test(
    fullstory_connection_config,
) -> None:
    get_connector(fullstory_connection_config).test_connection()


@pytest.mark.skip(reason="API keys are temporary for free accounts")
@pytest.mark.integration_saas
@pytest.mark.asyncio
async def test_fullstory_access_request_task(
    db,
    policy,
    fullstory_connection_config,
    fullstory_dataset_config,
    fullstory_identity_email,
    connection_config,
    fullstory_postgres_dataset_config,
    fullstory_postgres_db,
) -> None:
    """Full access request based on the Fullstory SaaS config"""
    privacy_request = PrivacyRequest(
        id=f"test_fullstory_access_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_value = fullstory_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)

    privacy_request.cache_identity(identity)

    dataset_name = fullstory_connection_config.get_saas_config().fides_key
    merged_graph = fullstory_dataset_config.get_graph()
    graph = DatasetGraph(*[merged_graph, fullstory_postgres_dataset_config.get_graph()])

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [fullstory_connection_config, connection_config],
        {"email": fullstory_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:user"],
        min_size=1,
        keys=[
            "uid",
            "displayName",
            "email",
            "numSessions",
            "firstSeen",
            "lastSeen",
            "existingOperation",
        ],
    )


@pytest.mark.skip(reason="API keys are temporary for free accounts")
@pytest.mark.integration_saas
@pytest.mark.asyncio
async def test_fullstory_erasure_request_task(
    db,
    policy,
    fullstory_connection_config,
    fullstory_dataset_config,
    connection_config,
    fullstory_postgres_erasure_db,
    fullstory_postgres_dataset_config,
    erasure_policy_string_rewrite,
    fullstory_erasure_identity_email,
    fullstory_erasure_identity_id,
    fullstory_erasure_data,
    fullstory_test_client: FullstoryTestClient,
) -> None:
    """Full erasure request based on the Fullstory SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_fullstory_access_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_value = fullstory_erasure_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = fullstory_connection_config.get_saas_config().fides_key
    merged_graph = fullstory_dataset_config.get_graph()
    graph = DatasetGraph(*[merged_graph, fullstory_postgres_dataset_config.get_graph()])

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [fullstory_connection_config, connection_config],
        {"email": fullstory_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:user"],
        min_size=1,
        keys=[
            "uid",
            "displayName",
            "email",
            "numSessions",
            "firstSeen",
            "lastSeen",
            "existingOperation",
        ],
    )

    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = True

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [fullstory_connection_config, connection_config],
        identity_kwargs,
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )
    # Verify masking request was issued for endpoints with update actions
    assert x == {
        "fullstory_instance:user": 1,
        "fullstory_postgres:fullstory_users": 0,
    }
    user_id = v[f"{dataset_name}:user"][0]["uid"]
    # Verifying field is masked but it is delayed for 60 seconds

    error_message = (
        f"User with email {fullstory_erasure_identity_email} was not updated to default"
    )
    poll_for_existence(
        user_updated,
        (user_id, fullstory_erasure_identity_email, fullstory_test_client),
        error_message=error_message,
    )

    CONFIG.execution.masking_strict = temp_masking
