import pytest
import random

from fidesops.graph.graph import DatasetGraph
from fidesops.models.privacy_request import ExecutionLog, PrivacyRequest
from fidesops.schemas.redis_cache import PrivacyRequestIdentity

from fidesops.task import graph_task
from tests.graph.graph_test_util import assert_rows_match, records_matching_fields

from fidesops.task.filter_results import filter_data_categories


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
