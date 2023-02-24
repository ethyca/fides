import random
from time import sleep

import pytest

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from fides.core.config import CONFIG
from tests.ops.graph.graph_test_util import assert_rows_match


@pytest.mark.integration_saas
@pytest.mark.integration_square
def test_square_connection_test(square_connection_config) -> None:
    get_connector(square_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_square
@pytest.mark.asyncio
async def test_square_access_request_task_by_email(
    db,
    policy,
    square_connection_config,
    square_dataset_config,
    square_identity_email,
) -> None:
    """Full access request based on the Square SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_square_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": square_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = square_connection_config.get_saas_config().fides_key
    merged_graph = square_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [square_connection_config],
        {"email": square_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "id",
            "created_at",
            "updated_at",
            "given_name",
            "family_name",
            "nickname",
            "email_address",
            "address",
            "phone_number",
            "company_name",
            "preferences",
            "creation_source",
            "birthday",
            "segment_ids",
            "version",
        ],
    )
    # verify we only returned data for our identity email
    for customer in v[f"{dataset_name}:customer"]:
        assert customer["email_address"] == square_identity_email

    assert_rows_match(
        v[f"{dataset_name}:locations"],
        min_size=1,
        keys=[
            "id",
            "name",
            "address",
            "timezone",
            "capabilities",
            "status",
            "created_at",
            "merchant_id",
            "country",
            "language_code",
            "currency",
            "business_name",
            "type",
            "business_hours",
            "mcc",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:orders"],
        min_size=1,
        keys=["id", "location_id", "customer_id", "state"],
    )


@pytest.mark.integration_saas
@pytest.mark.integration_square
@pytest.mark.asyncio
async def test_square_access_request_task_by_phone_number(
    db,
    policy,
    square_connection_config,
    square_dataset_config,
    square_identity_email,
    square_identity_phone_number,
) -> None:
    """Full access request based on the Square SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_square_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"phone_number": square_identity_phone_number})
    privacy_request.cache_identity(identity)

    dataset_name = square_connection_config.get_saas_config().fides_key
    merged_graph = square_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [square_connection_config],
        {"phone_number": square_identity_phone_number},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "id",
            "created_at",
            "updated_at",
            "given_name",
            "family_name",
            "nickname",
            "email_address",
            "address",
            "phone_number",
            "company_name",
            "preferences",
            "creation_source",
            "birthday",
            "segment_ids",
            "version",
        ],
    )
    # verify we only returned data for our identity phone number
    for customer in v[f"{dataset_name}:customer"]:
        assert customer["phone_number"] == square_identity_phone_number
        assert customer["email_address"] == square_identity_email


@pytest.mark.integration_saas
@pytest.mark.integration_square
@pytest.mark.asyncio
async def test_square_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    square_connection_config,
    square_dataset_config,
    square_erasure_identity_email,
    square_erasure_data,
    square_test_client,
) -> None:
    """Full erasure request based on the Square SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_square_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity_kwargs = {"email": square_erasure_identity_email}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = square_connection_config.get_saas_config().fides_key
    merged_graph = square_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)
    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [square_connection_config],
        identity_kwargs,
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "id",
            "created_at",
            "updated_at",
            "given_name",
            "family_name",
            "nickname",
            "email_address",
            "address",
            "company_name",
            "preferences",
            "creation_source",
            "birthday",
            "segment_ids",
            "version",
        ],
    )
    # verify we only returned data for our identity email
    for customer in v[f"{dataset_name}:customer"]:
        assert customer["email_address"] == square_erasure_identity_email

    assert_rows_match(
        v[f"{dataset_name}:locations"],
        min_size=1,
        keys=[
            "id",
            "name",
            "address",
            "timezone",
            "capabilities",
            "status",
            "created_at",
            "merchant_id",
            "country",
            "language_code",
            "currency",
            "business_name",
            "type",
            "business_hours",
            "mcc",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:orders"],
        min_size=1,
        keys=["id", "location_id", "customer_id", "state"],
    )
    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = True

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [square_connection_config],
        identity_kwargs,
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )
    assert x == {
        f"{dataset_name}:customer": 1,
        f"{dataset_name}:orders": 0,
        f"{dataset_name}:locations": 0,
    }

    sleep(30)  # wait for update to propagate on Square's side

    customer_response = square_test_client.get_customer(square_erasure_identity_email)
    customer = customer_response.json()
    customer = customer["customers"][0]
    assert customer["given_name"] == "MASKED"
    assert customer["family_name"] == "MASKED"
    assert customer["nickname"] == "MASKED"

    CONFIG.execution.masking_strict = temp_masking
