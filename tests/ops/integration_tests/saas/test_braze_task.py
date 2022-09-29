import random
import time

import pytest
import requests

from fidesops.ops.core.config import config
from fidesops.ops.graph.graph import DatasetGraph
from fidesops.ops.models.privacy_request import PrivacyRequest
from fidesops.ops.schemas.redis_cache import Identity
from fidesops.ops.service.connectors import get_connector
from fidesops.ops.task import graph_task
from fidesops.ops.task.graph_task import get_cached_data_for_erasures
from tests.ops.graph.graph_test_util import assert_rows_match


@pytest.mark.integration_saas
@pytest.mark.integration_braze
def test_braze_connection_test(braze_connection_config) -> None:
    get_connector(braze_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_braze
@pytest.mark.asyncio
async def test_saas_access_request_task(
    db,
    policy,
    braze_connection_config,
    braze_dataset_config,
    braze_identity_email,
) -> None:
    """Full access request based on the Braze SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_braze_access_request_task_{random.randint(0, 250)}"
    )
    identity_attribute = "email"
    identity_value = braze_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = braze_connection_config.get_saas_config().fides_key
    merged_graph = braze_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [braze_connection_config],
        {identity_attribute: braze_identity_email},
        db,
    )
    key_users = f"{dataset_name}:users"
    assert_rows_match(
        v[key_users],
        min_size=1,
        keys=[
            "external_id",
            "user_aliases",
            "braze_id",
            "first_name",
            "last_name",
            identity_attribute,
            "dob",
            "country",
            "home_city",
            "language",
            "gender",
            "phone",
        ],
    )

    for entry in v[key_users]:
        assert identity_value == entry.get(identity_attribute)

    key_subscription_groups = f"{dataset_name}:subscription_groups_email"
    assert_rows_match(
        v[key_subscription_groups],
        min_size=1,
        keys=[
            identity_attribute,
            "phone",
            "external_id",
            "subscription_groups",
        ],
    )

    for entry in v[key_subscription_groups]:
        assert identity_value == entry.get(identity_attribute)


@pytest.mark.integration_saas
@pytest.mark.integration_braze
@pytest.mark.asyncio
async def test_saas_erasure_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    braze_connection_config,
    braze_dataset_config,
    braze_erasure_identity_email,
    braze_erasure_data,
) -> None:
    privacy_request = PrivacyRequest(
        id=f"test_braze_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_value = braze_erasure_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)

    privacy_request.cache_identity(identity)

    dataset_name = braze_connection_config.get_saas_config().fides_key
    merged_graph = braze_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [braze_connection_config],
        identity_kwargs,
        db,
    )
    key_users = f"{dataset_name}:users"
    assert_rows_match(
        v[key_users],
        min_size=1,
        keys=[
            "external_id",
            "user_aliases",
            "braze_id",
            "first_name",
            "last_name",
            identity_attribute,
            "dob",
            "country",
            "home_city",
            "language",
            "gender",
            "phone",
        ],
    )

    temp_masking = config.execution.masking_strict
    config.execution.masking_strict = True

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [braze_connection_config],
        identity_kwargs,
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:users": 1,
        f"{dataset_name}:subscription_groups_email": 0,
    }

    time.sleep(10)

    # Verifying field is masked
    braze_secrets = braze_connection_config.secrets
    base_url = f"https://{braze_secrets['domain']}"
    headers = {
        "Authorization": f"Bearer {braze_secrets['api_key']}",
    }
    body = {
        "email_address": braze_erasure_identity_email,
        "fields_to_export": [
            "braze_id",
            "country",
            "dob",
            "email",
            "external_id",
            "first_name",
            "gender",
            "home_city",
            "language",
            "last_name",
            "phone",
            "user_aliases",
        ],
    }

    user_response = requests.post(
        url=f"{base_url}/users/export/ids",
        json=body,
        headers=headers,
    )
    users = user_response.json().get("users")

    for user in users:
        assert user["first_name"] == "MASKED"
        assert user["last_name"] == "MASKED"

    config.execution.masking_strict = temp_masking
