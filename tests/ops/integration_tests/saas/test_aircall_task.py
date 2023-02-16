import random
import time

import pytest
import requests

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
@pytest.mark.integration_aircall
def test_aircall_connection_test(aircall_connection_config) -> None:
    get_connector(aircall_connection_config).test_connection()

@pytest.mark.integration_saas
@pytest.mark.integration_aircall
@pytest.mark.asyncio
async def test_aircall_access_request_task(
    db,
    policy,
    aircall_connection_config,
    aircall_dataset_config,
    aircall_identity_email,
) -> None:
    """Full access request based on the aircall SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_aircall_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": aircall_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = aircall_connection_config.get_saas_config().fides_key
    merged_graph = aircall_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [aircall_connection_config],
        {"email": aircall_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:contact"],
        min_size=1,
        keys=[
            "id",
            "first_name",
            "last_name",
            "company_name",
            "information",
            "is_shared",
            "direct_link",
            "created_at",
            "updated_at",
            "phone_numbers",
            "emails"
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:calls"],
        min_size=1,
        keys=[
            "calls",
            "meta",
        ],
    )

    # verify we only returned data for our identity email
    assert v[f"{dataset_name}:contact"][0]["emails"][0]["value"] == aircall_identity_email

@pytest.mark.integration_saas
@pytest.mark.integration_aircall
@pytest.mark.asyncio
async def test_aircall_access_request_task_by_phone_number(
    db,
    policy,
    aircall_connection_config,
    aircall_dataset_config,
    aircall_identity_email,
    aircall_identity_phone_number,
) -> None:
    """Full access request based on the aircall SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_aircall_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"phone_number": aircall_identity_phone_number})
    privacy_request.cache_identity(identity)

    dataset_name = aircall_connection_config.get_saas_config().fides_key
    merged_graph = aircall_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [aircall_connection_config],
        {"phone_number": aircall_identity_phone_number},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:contact"],
        min_size=1,
        keys=[
            "id",
            "first_name",
            "last_name",
            "company_name",
            "information",
            "is_shared",
            "direct_link",
            "created_at",
            "updated_at",
            "phone_numbers",
            "emails",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:calls"],
        min_size=1,
        keys=[
            "calls",
            "meta",
        ],
    )
    # verify we only returned data for our identity phone number
    for customer in v[f"{dataset_name}:contact"]:
        assert customer["phone_numbers"][0]["value"] == aircall_identity_phone_number
