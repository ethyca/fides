import json

import pytest
import random

from fidesops.graph.graph import DatasetGraph
from fidesops.models.privacy_request import ExecutionLog, PrivacyRequest
from fidesops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.schemas.saas.shared_schemas import SaaSRequestParams, HTTPMethod
from fidesops.service.connectors import SaaSConnector

from fidesops.task import graph_task
from tests.graph.graph_test_util import assert_rows_match, records_matching_fields

from fidesops.task.filter_results import filter_data_categories
from fidesops.task.graph_task import get_cached_data_for_erasures
from fidesops.util.saas_util import format_body


@pytest.mark.integration_saas
@pytest.mark.integration_hubspot
def test_saas_access_request_task(
        db,
        policy,
        connection_config_hubspot,
        dataset_config_hubspot,
        hubspot_identity_email,
) -> None:
    """Full access request based on the Hubspot SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_saas_access_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_value = hubspot_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = PrivacyRequestIdentity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = connection_config_hubspot.get_saas_config().fides_key
    merged_graph = dataset_config_hubspot.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [connection_config_hubspot],
        {"email": hubspot_identity_email},
    )

    assert_rows_match(
        v[f"{dataset_name}:contacts"],
        min_size=1,
        keys=[
            "archived",
            "createdAt",
            "id",
            "properties"
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:subscription_preferences"],
        min_size=1,
        keys=[
            "recipient",
            "subscriptionStatuses"
        ],
    )

    target_categories = {"user.provided"}
    filtered_results = filter_data_categories(
        v,
        target_categories,
        graph.data_category_field_mapping,
    )

    assert set(filtered_results.keys()) == {
        f"{dataset_name}:contacts",
        f"{dataset_name}:subscription_preferences",
    }
    assert set(filtered_results[f"{dataset_name}:contacts"][0].keys()) == {
        "properties"
    }

    assert set(filtered_results[f"{dataset_name}:contacts"][0]["properties"].keys()) == {
        "lastname",
        "firstname",
        "email",
    }
    assert set(filtered_results[f"{dataset_name}:subscription_preferences"][0].keys()) == {
        "recipient"
    }
    assert filtered_results[f"{dataset_name}:subscription_preferences"][0]["recipient"] == hubspot_identity_email

    logs = (
        ExecutionLog.query(db=db)
            .filter(ExecutionLog.privacy_request_id == privacy_request.id)
            .all()
    )

    logs = [log.__dict__ for log in logs]
    assert (
            len(
                records_matching_fields(
                    logs, dataset_name=dataset_name, collection_name="contacts"
                )
            )
            > 0
    )
    assert (
            len(
                records_matching_fields(
                    logs,
                    dataset_name=dataset_name,
                    collection_name="owners",
                )
            )
            > 0
    )
    assert (
            len(
                records_matching_fields(
                    logs, dataset_name=dataset_name, collection_name="subscription_preferences"
                )
            )
            > 0
    )


@pytest.mark.integration_saas
@pytest.mark.integration_hubspot
def test_saas_erasure_request_task(
        db,
        policy,
        erasure_policy_string_rewrite,
        connection_config_hubspot,
        dataset_config_hubspot,
        hubspot_erasure_identity_email,
        hubspot_erasure_data,
) -> None:
    """Full erasure request based on the Hubspot SaaS config"""
    privacy_request = PrivacyRequest(
        id=f"test_saas_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_kwargs = {identity_attribute: (hubspot_erasure_identity_email)}
    identity = PrivacyRequestIdentity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = connection_config_hubspot.get_saas_config().fides_key
    merged_graph = dataset_config_hubspot.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [connection_config_hubspot],
        identity_kwargs,
    )

    assert_rows_match(
        v[f"{dataset_name}:contacts"],
        min_size=1,
        keys=[
            "archived",
            "createdAt",
            "id",
            "properties"
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:subscription_preferences"],
        min_size=1,
        keys=[
            "recipient",
            "subscriptionStatuses"
        ],
    )

    erasure = graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [connection_config_hubspot],
        identity_kwargs,
        get_cached_data_for_erasures(privacy_request.id),
    )

    # Masking request only issued to "contacts" and "subscription_preferences" endpoints
    assert erasure == {
        "hubspot_connector_example:contacts": 1,
        "hubspot_connector_example:owners": 0,
        "hubspot_connector_example:subscription_preferences": 1
    }

    connector = SaaSConnector(connection_config_hubspot)

    body = json.dumps({
        "filterGroups": [{
            "filters": [{
                "value": hubspot_erasure_identity_email,
                "propertyName": "email",
                "operator": "EQ"
            }]
        }]
    })

    updated_headers, formatted_body = format_body({}, body)

    # Verify the user has been assigned to None
    contact_request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.POST,
        path="/crm/v3/objects/contacts/search",
        headers=updated_headers,
        body=formatted_body,
    )
    contact_response = connector.create_client().send(contact_request)
    contact_body = contact_response.json()
    assert contact_body["results"][0]["properties"]["firstname"] == "MASKED"

    # verify user is unsubscribed
    subscription_request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path=f'/communication-preferences/v3/status/email/{hubspot_erasure_identity_email}'
    )
    subscription_response = connector.create_client().send(subscription_request)
    subscription_body = subscription_response.json()
    assert subscription_body["subscriptionStatuses"][0]["status"] == "NOT_SUBSCRIBED"
