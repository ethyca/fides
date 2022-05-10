import time
import random
import requests
import pytest
from faker import Faker

from fidesops.core.config import config
from fidesops.task.filter_results import filter_data_categories


from fidesops.graph.graph import DatasetGraph
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.redis_cache import PrivacyRequestIdentity

from fidesops.task import graph_task
from fidesops.task.graph_task import get_cached_data_for_erasures
from tests.graph.graph_test_util import assert_rows_match


@pytest.mark.integration_saas
@pytest.mark.integration_segment
def test_segment_saas_access_request_task(
    db,
    policy,
    segment_connection_config,
    segment_dataset_config,
    segment_identity_email,
) -> None:
    """Full access request based on the Segment SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_saas_access_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": segment_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = segment_connection_config.get_saas_config().fides_key
    merged_graph = segment_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [segment_connection_config],
        {"email": segment_identity_email},
    )

    assert_rows_match(
        v[f"{dataset_name}:track_events"],
        min_size=1,
        keys=[
            "external_ids",
            "context",
            "type",
            "source_id",
            "message_id",
            "timestamp",
            "properties",
            "event",
            "related",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:traits"],
        min_size=1,
        keys=[
            "address",
            "age",
            "avatar",
            "description",
            "email",
            "firstName",
            "gender",
            "id",
            "industry",
            "lastName",
            "name",
            "phone",
            "subscriptionStatus",
            "title",
            "username",
            "website",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:segment_user"],
        min_size=1,
        keys=["segment_id", "metadata"],
    )

    assert_rows_match(
        v[f"{dataset_name}:external_ids"],
        min_size=2,
        keys=["id", "type", "source_id", "collection", "created_at", "encoding"],
    )

    target_categories = {"user"}
    filtered_results = filter_data_categories(
        v,
        target_categories,
        graph.data_category_field_mapping,
    )

    assert set(filtered_results.keys()) == {
        f"{dataset_name}:track_events",
        f"{dataset_name}:traits",
        f"{dataset_name}:external_ids",
        f"{dataset_name}:segment_user",
    }

    assert set(filtered_results[f"{dataset_name}:traits"][0].keys()) == {
        "address",
        "title",
        "description",
        "username",
        "gender",
        "phone",
        "id",
        "website",
        "email",
        "name",
        "age",
        "firstName",
    }
    assert (
        filtered_results[f"{dataset_name}:traits"][0]["email"] == segment_identity_email
    )

    assert (
        filtered_results[f"{dataset_name}:track_events"][0]["external_ids"][0]["id"]
        == segment_identity_email
    )
    assert len(filtered_results[f"{dataset_name}:external_ids"]) == 2
    assert (
        filtered_results[f"{dataset_name}:external_ids"][0]["id"]
        == segment_identity_email
    )

    assert filtered_results[f"{dataset_name}:segment_user"][0]["segment_id"]


def _create_test_segment_email(base_email: str, timestamp: int) -> str:
    at_index: int = base_email.find("@")
    email = f"{base_email[0:at_index]}{timestamp}{base_email[at_index:]}"
    return email


def create_segment_test_data(segment_connection_config, segment_identity_email: str):
    """Seeds a segment user and event"""
    segment_secrets = segment_connection_config.secrets
    if not segment_identity_email:  # Don't run unnecessarily locally
        return

    faker = Faker()

    ts = int(time.time())
    email = _create_test_segment_email(segment_identity_email, ts)
    first_name = faker.first_name()
    last_name = faker.last_name()

    # Create user
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {segment_secrets['user_token']}",
    }
    body = {
        "userId": email,
        "traits": {
            "subscriptionStatus": "active",
            "address": {
                "city": faker.city(),
                "country": faker.country(),
                "postalCode": faker.postcode(),
                "state": "NY",
            },
            "age": random.randrange(18, 99),
            "avatar": "",
            "industry": "data",
            "description": faker.job(),
            "email": email,
            "firstName": first_name,
            "id": ts,
            "lastName": last_name,
            "name": f"{first_name} {last_name}",
            "phone": faker.phone_number(),
            "title": faker.prefix(),
            "username": f"test_fidesops_user_{ts}",
            "website": "www.example.com",
        },
    }
    resp = requests.post(
        f"https://{segment_secrets['api_domain']}identify", headers=headers, json=body
    )
    assert resp.status_code == 200

    # Create event
    body = {
        "userId": email,
        "type": "track",
        "event": "User Registered",
        "properties": {"plan": "Free", "accountType": faker.company()},
        "context": {"ip": faker.ipv4()},
    }

    resp = requests.post(
        f"https://{segment_secrets['api_domain']}track", headers=headers, json=body
    )
    assert resp.status_code == 200
    return email


@pytest.mark.integration_saas
@pytest.mark.integration_segment
def test_segment_saas_erasure_request_task(
    db,
    policy,
    segment_connection_config,
    segment_dataset_config,
    segment_identity_email,
) -> None:
    """Full erasure request based on the Segment SaaS config"""
    config.execution.MASKING_STRICT = False  # Allow GDPR Delete

    # Create user for GDPR delete
    erasure_email = create_segment_test_data(
        segment_connection_config, segment_identity_email
    )
    time.sleep(8)  # Pause before making access/erasure requests
    privacy_request = PrivacyRequest(
        id=f"test_saas_access_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": erasure_email})
    privacy_request.cache_identity(identity)

    dataset_name = segment_connection_config.get_saas_config().fides_key
    merged_graph = segment_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [segment_connection_config],
        {"email": erasure_email},
    )

    assert_rows_match(
        v[f"{dataset_name}:track_events"],
        min_size=1,
        keys=[
            "external_ids",
            "context",
            "type",
            "source_id",
            "message_id",
            "timestamp",
            "properties",
            "event",
            "related",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:traits"],
        min_size=1,
        keys=[
            "address",
            "age",
            "avatar",
            "description",
            "email",
            "firstName",
            "id",
            "industry",
            "lastName",
            "name",
            "phone",
            "subscriptionStatus",
            "title",
            "username",
            "website",
        ],
    )

    x = graph_task.run_erasure(
        privacy_request,
        policy,
        graph,
        [segment_connection_config],
        {"email": erasure_email},
        get_cached_data_for_erasures(privacy_request.id),
    )

    # Assert erasure request made to segment_user - cannot verify success immediately as this can take
    # days, weeks to process
    assert x == {
        "segment_connector_example:segment_user": 1,
        "segment_connector_example:traits": 0,
        "segment_connector_example:external_ids": 0,
        "segment_connector_example:track_events": 0,
    }

    config.execution.MASKING_STRICT = True  # Reset
