import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.filter_results import filter_data_categories
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import CONFIG
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.fixtures.saas.hubspot_fixtures import HubspotTestClient, user_exists
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.test_helpers.saas_test_utils import poll_for_existence


@pytest.mark.integration_saas
def test_hubspot_connection_test(connection_config_hubspot) -> None:
    get_connector(connection_config_hubspot).test_connection()


@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_hubspot_access_request_task(
    db,
    dsr_version,
    request,
    policy,
    connection_config_hubspot,
    dataset_config_hubspot,
    hubspot_identity_email,
    privacy_request,
) -> None:
    """Full access request based on the Hubspot SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity_attribute = "email"
    identity_value = hubspot_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = connection_config_hubspot.get_saas_config().fides_key
    merged_graph = dataset_config_hubspot.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
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
        graph,
    )

    assert set(filtered_results.keys()) == {
        f"{dataset_name}:contacts",
        f"{dataset_name}:subscription_preferences",
        f"{dataset_name}:users",
        f"{dataset_name}:owners",
    }
    assert set(filtered_results[f"{dataset_name}:contacts"][0].keys()) == {
        "id",
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
        "firstName",
        "lastName",
    }
    assert (
        filtered_results[f"{dataset_name}:owners"][0]["email"] == hubspot_identity_email
    )


@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.usefixtures(
    "use_dsr_3_0"
)  # Only testing on DSR 3.0 not 2.0 - because of fixtures taking too long to settle down
async def test_hubspot_erasure_request_task(
    db,
    privacy_request,
    erasure_policy_string_rewrite_name_and_email,
    connection_config_hubspot,
    dataset_config_hubspot,
    hubspot_erasure_identity_email,
    hubspot_erasure_data,
    hubspot_test_client: HubspotTestClient,
) -> None:
    """Full erasure request based on the Hubspot SaaS config"""

    privacy_request.policy_id = erasure_policy_string_rewrite_name_and_email.id
    privacy_request.save(db)
    contact_id, user_id = hubspot_erasure_data

    identity_attribute = "email"
    identity_kwargs = {identity_attribute: (hubspot_erasure_identity_email)}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = connection_config_hubspot.get_saas_config().fides_key
    merged_graph = dataset_config_hubspot.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite_name_and_email,
        graph,
        [connection_config_hubspot],
        identity_kwargs,
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

    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow delete
    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite_name_and_email,
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
        "hubspot_instance:subscription_preferences": 2,
        "hubspot_instance:users": 1,
    }

    # Verify the user has been assigned to None
    contact_response = hubspot_test_client.get_contact(contact_id=contact_id)
    contact_body = contact_response.json()
    assert contact_body["properties"]["firstname"] == "MASKED"
    assert contact_body["properties"]["email"] == f"{privacy_request.id}@company.com"

    # verify user is unsubscribed
    email_subscription_response = hubspot_test_client.get_email_subscriptions(
        email=hubspot_erasure_identity_email
    )
    subscription_body = email_subscription_response.json()
    for subscription_status in subscription_body["subscriptionStatuses"]:
        assert subscription_status["status"] == "NOT_SUBSCRIBED"

    # verify user is deleted
    error_message = f"User with user id {user_id} could not be deleted from Hubspot"
    poll_for_existence(
        user_exists,
        (user_id, hubspot_test_client),
        error_message=error_message,
        existence_desired=False,
    )
