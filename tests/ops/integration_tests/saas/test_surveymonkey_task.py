import random

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
@pytest.mark.integration_surveymonkey
def test_surveymonkey_connection_test(surveymonkey_connection_config) -> None:
    get_connector(surveymonkey_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_surveymonkey
@pytest.mark.asyncio
async def test_surveymonkey_access_request_task(
    db,
    policy,
    surveymonkey_connection_config,
    surveymonkey_dataset_config,
    surveymonkey_identity_email,
    connection_config,
    surveymonkey_postgres_dataset_config,
    surveymonkey_postgres_db,
) -> None:
    """Full access request based on the Surveymonkey SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_surveymonkey_access_request_task_{random.randint(0, 1000)}"
    )

    identity_attribute = "email"
    identity_value = surveymonkey_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)

    privacy_request.cache_identity(identity)

    dataset_name = surveymonkey_connection_config.get_saas_config().fides_key
    merged_graph = surveymonkey_dataset_config.get_graph()
    graph = DatasetGraph(
        *[merged_graph, surveymonkey_postgres_dataset_config.get_graph()]
    )

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [surveymonkey_connection_config, connection_config],
        {"email": surveymonkey_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:contacts"],
        min_size=1,
        keys=[
            "id",
            "first_name",
            "last_name",
            "email",
            "href",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:survey_collectors"],
        min_size=1,
        keys=[
            "name",
            "id",
            "href",
            "type",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:survey_responses"],
        min_size=1,
        keys=[
            "id",
            "recipient_id",
            "collection_mode",
            "response_status",
            "custom_value",
            "first_name",
            "last_name",
            "email_address",
            "ip_address",
            "logic_path",
            "page_path",
            "collector_id",
            "survey_id",
            "custom_variables",
            "edit_url",
            "analyze_url",
            "total_time",
            "date_modified",
            "date_created",
            "href",
        ],
    )


@pytest.mark.integration_saas
@pytest.mark.integration_surveymonkey
@pytest.mark.asyncio
async def test_surveymonkey_erasure_request_task(
    db,
    policy,
    surveymonkey_connection_config,
    surveymonkey_dataset_config,
    connection_config,
    surveymonkey_postgres_dataset_config,
    erasure_policy_string_rewrite,
    surveymonkey_erasure_identity_email,
    surveymonkey_erasure_data,
    surveymonkey_postgres_erasure_db,
) -> None:
    """Full erasure request based on the Surveymonkey SaaS config"""
    # contact_id = surveymonkey_erasure_data
    privacy_request = PrivacyRequest(
        id=f"test_surveymonkey_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_value = surveymonkey_erasure_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = surveymonkey_connection_config.get_saas_config().fides_key
    merged_graph = surveymonkey_dataset_config.get_graph()
    graph = DatasetGraph(
        *[merged_graph, surveymonkey_postgres_dataset_config.get_graph()]
    )

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [surveymonkey_connection_config, connection_config],
        {"email": surveymonkey_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:contacts"],
        min_size=1,
        keys=[
            "id",
            "first_name",
            "last_name",
            "email",
            "href",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:survey_collectors"],
        min_size=1,
        keys=[
            "name",
            "id",
            "href",
            "type",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:survey_responses"],
        min_size=1,
        keys=[
            "id",
            "recipient_id",
            "collection_mode",
            "response_status",
            "custom_value",
            "first_name",
            "last_name",
            "email_address",
            "ip_address",
            "logic_path",
            "page_path",
            "collector_id",
            "survey_id",
            "custom_variables",
            "edit_url",
            "analyze_url",
            "total_time",
            "date_modified",
            "date_created",
            "href",
        ],
    )

    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = True

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [surveymonkey_connection_config, connection_config],
        identity_kwargs,
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:contacts": 1,
        f"{dataset_name}:survey_collectors": 0,
        f"{dataset_name}:survey_responses": 1,
        "surveymonkey_postgres:surveymonkey_surveys": 0,
    }

    CONFIG.execution.masking_strict = temp_masking
