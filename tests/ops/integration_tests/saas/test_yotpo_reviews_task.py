import random
from time import sleep

import pytest

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from fides.core.config import get_config
from tests.ops.graph.graph_test_util import assert_rows_match

CONFIG = get_config()


@pytest.mark.integration_saas
@pytest.mark.integration_yotpo
def test_yotpo_reviews_connection_test(yotpo_reviews_connection_config) -> None:
    get_connector(yotpo_reviews_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_yotpo
@pytest.mark.asyncio
async def test_yotpo_reviews_access_request_task(
    db,
    policy,
    yotpo_reviews_connection_config,
    yotpo_reviews_dataset_config,
    yotpo_reviews_identity_email,
    connection_config,
    yotpo_reviews_postgres_dataset_config,
    yotpo_reviews_postgres_db,
) -> None:
    """Full access request based on the Yotpo Reviews SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_yotpo_reviews_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": yotpo_reviews_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = yotpo_reviews_connection_config.get_saas_config().fides_key
    merged_graph = yotpo_reviews_dataset_config.get_graph()
    graph = DatasetGraph(
        *[merged_graph, yotpo_reviews_postgres_dataset_config.get_graph()]
    )

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [yotpo_reviews_connection_config, connection_config],
        {"email": yotpo_reviews_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "external_id",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "gender",
            "account_created_at",
            "account_status",
            "default_language",
            "default_currency",
            "tags",
            "address",
            "custom_properties",
            "accepts_email_marketing",
            "accepts_sms_marketing",
        ],
    )


@pytest.mark.integration_saas
@pytest.mark.integration_yotpo
@pytest.mark.asyncio
async def test_yotpo_reviews_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    yotpo_reviews_connection_config,
    yotpo_reviews_dataset_config,
    yotpo_reviews_erasure_identity_email,
    yotpo_reviews_erasure_yotpo_external_id,
    yotpo_reviews_postgres_dataset_config,
    connection_config,
    yotpo_reviews_postgres_erasure_db,
    yotpo_reviews_erasure_data,
    yotpo_reviews_test_client,
) -> None:
    """Full erasure request based on the Yotpo Reviews SaaS config"""

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = True

    privacy_request = PrivacyRequest(
        id=f"test_yotpo_reviews_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": yotpo_reviews_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = yotpo_reviews_connection_config.get_saas_config().fides_key
    merged_graph = yotpo_reviews_dataset_config.get_graph()
    graph = DatasetGraph(
        *[merged_graph, yotpo_reviews_postgres_dataset_config.get_graph()]
    )

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [yotpo_reviews_connection_config, connection_config],
        {"email": yotpo_reviews_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "external_id",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "gender",
            "account_created_at",
            "account_status",
            "default_language",
            "default_currency",
            "tags",
            "address",
            "custom_properties",
            "accepts_email_marketing",
            "accepts_sms_marketing",
        ],
    )

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [yotpo_reviews_connection_config, connection_config],
        {"email": yotpo_reviews_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        "yotpo_reviews_instance:customer": 1,
        "yotpo_reviews_postgres:yotpo_customer": 0,
    }

    sleep(120)

    response = yotpo_reviews_test_client.get_customer(
        yotpo_reviews_erasure_yotpo_external_id
    )
    assert response.ok

    customer = response.json()["customers"][0]
    assert customer["first_name"] == "MASKED"
    assert customer["last_name"] == "MASKED"

    CONFIG.execution.masking_strict = masking_strict
