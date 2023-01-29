import random

import pytest

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.api.ops.task.filter_results import filter_data_categories
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from fides.core.config import get_config
from tests.fixtures.saas.hubspot_fixtures import HubspotTestClient, user_exists
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.test_helpers.saas_test_utils import poll_for_existence

CONFIG = get_config()


@pytest.mark.integration_saas
@pytest.mark.integration_hubspot
def test_hubspot_connection_test(connection_config_hubspot) -> None:
    get_connector(connection_config_hubspot).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_hubspot
@pytest.mark.asyncio
async def test_hubspot_access_request_task(
    db,
    policy,
    connection_config_hubspot,
    dataset_config_hubspot,
    hubspot_identity_email,
) -> None:
    """Full access request based on the Hubspot SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_hubspot_access_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_value = hubspot_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = connection_config_hubspot.get_saas_config().fides_key
    merged_graph = dataset_config_hubspot.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [connection_config_hubspot],
        {"email": hubspot_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:contacts"],
        min_size=1,
        keys=["archived", "createdAt", "id", "properties"],
    )
    assert_rows_match(
        v[f"{dataset_name}:subscription_preferences"],
        min_size=1,
        keys=["recipient", "subscriptionStatuses"],
    )
    assert_rows_match(
        v[f"{dataset_name}:users"],
        min_size=1,
        keys=["id", "email"],
    )
    assert_rows_match(
        v[f"{dataset_name}:owners"],
        min_size=1,
        keys=["id", "email", "lastName", "updatedAt", "firstName", "userId"],
    )

    target_categories = {"user"}
    filtered_results = filter_data_categories(
        v,
        target_categories,
        graph.data_category_field_mapping,
    )

    assert set(filtered_results.keys()) == {
        f"{dataset_name}:contacts",
        f"{dataset_name}:subscription_preferences",
        f"{dataset_name}:users",
        f"{dataset_name}:owners",
    }
    assert set(filtered_results[f"{dataset_name}:contacts"][0].keys()) == {
        "id",
        "createdAt",
        "updatedAt",
        "properties",
    }

    results_set = set(
        filtered_results[f"{dataset_name}:contacts"][0]["properties"].keys()
    )
    assert "lastname" in results_set
    assert "firstname" in results_set
    assert "email" in results_set

    assert set(
        filtered_results[f"{dataset_name}:subscription_preferences"][0].keys()
    ) == {"recipient"}
    assert (
        filtered_results[f"{dataset_name}:subscription_preferences"][0]["recipient"]
        == hubspot_identity_email
    )
    assert set(filtered_results[f"{dataset_name}:users"][0].keys()) == {"email", "id"}
    assert (
        filtered_results[f"{dataset_name}:users"][0]["email"] == hubspot_identity_email
    )
    assert set(filtered_results[f"{dataset_name}:owners"][0].keys()) == {
        "email",
        "id",
        "userId",
        "updatedAt",
        "firstName",
        "lastName",
    }
    assert (
        filtered_results[f"{dataset_name}:owners"][0]["email"] == hubspot_identity_email
    )


@pytest.mark.integration_saas
@pytest.mark.integration_hubspot
@pytest.mark.asyncio
async def test_hubspot_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    connection_config_hubspot,
    dataset_config_hubspot,
    hubspot_erasure_identity_email,
    hubspot_erasure_data,
    hubspot_test_client: HubspotTestClient,
) -> None:
    """Full erasure request based on the Hubspot SaaS config"""
    contact_id, user_id = hubspot_erasure_data
    privacy_request = PrivacyRequest(
        id=f"test_hubspot_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_kwargs = {identity_attribute: (hubspot_erasure_identity_email)}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = connection_config_hubspot.get_saas_config().fides_key
    merged_graph = dataset_config_hubspot.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request, policy, graph, [connection_config_hubspot], identity_kwargs, db
    )

    assert_rows_match(
        v[f"{dataset_name}:contacts"],
        min_size=1,
        keys=["archived", "createdAt", "id", "properties"],
    )
    assert_rows_match(
        v[f"{dataset_name}:subscription_preferences"],
        min_size=1,
        keys=["recipient", "subscriptionStatuses"],
    )

    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow delete
    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [connection_config_hubspot],
        identity_kwargs,
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )
    CONFIG.execution.masking_strict = temp_masking

    # Masking request only issued to "contacts", "subscription_preferences", and "users" endpoints
    assert x == {
        "hubspot_instance:contacts": 1,
        "hubspot_instance:owners": 0,
        "hubspot_instance:subscription_preferences": 1,
        "hubspot_instance:users": 1,
    }

    # Verify the user has been assigned to None
    contact_response = hubspot_test_client.get_contact(contact_id=contact_id)
    contact_body = contact_response.json()
    assert contact_body["properties"]["firstname"] == "MASKED"

    # verify user is unsubscribed
    email_subscription_response = hubspot_test_client.get_email_subscriptions(
        email=hubspot_erasure_identity_email
    )
    subscription_body = email_subscription_response.json()
    assert subscription_body["subscriptionStatuses"][0]["status"] == "NOT_SUBSCRIBED"

    # verify user is deleted
    error_message = f"User with user id {user_id} could not be deleted from Hubspot"
    poll_for_existence(
        user_exists,
        (user_id, hubspot_test_client),
        error_message=error_message,
        existence_desired=False,
    )
