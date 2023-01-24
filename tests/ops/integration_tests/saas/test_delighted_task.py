import random
from typing import List

import pytest
import requests

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.api.ops.task.filter_results import filter_data_categories
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from fides.core.config import get_config
from tests.ops.graph.graph_test_util import assert_rows_match

CONFIG = get_config()


@pytest.mark.integration_saas
@pytest.mark.integration_delighted
def test_delighted_connection_test(delighted_connection_config) -> None:
    get_connector(delighted_connection_config).test_connection()

async def test_delighted_access_request_task(
    db,
    policy,
    delighted_connection_config,
    delighted_dataset_config,
    delighted_identity_email,
) -> None:
    """Full access request based on the Delighted SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_delighted_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": delighted_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = delighted_connection_config.get_saas_config().fides_key
    merged_graph = delighted_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [delighted_connection_config],
        {"email": delighted_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:people"],
        min_size=1,
        keys=[
            "id",
            "name",
            "email",
            "created_at",
            "last_sent_at",
            "last_responded_at",
            "next_survey_scheduled_at"
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:survey_response"],
        min_size=1,
        keys=[
            "id",
            "person",
            "survey_type",
            "score",
            "comment",
            "permalink",
            "created_at",
            "updated_at",
            "person_properties",
            "notes",
            "tags",
            "additional_answers"
        ],
    )

    # # verify we only returned data for our identity email
    print({dataset_name})

    assert v[f"{dataset_name}:people"][0]["email"] == delighted_identity_email
    people_id = v[f"{dataset_name}:people"][0]["id"]

    assert v[f"{dataset_name}:survey_response"][0]["person"] == people_id

@pytest.mark.integration_saas
@pytest.mark.integration_delighted
@pytest.mark.asyncio
async def test_delighted_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    delighted_connection_config,
    delighted_dataset_config,
    delighted_erasure_identity_email,
    delighted_create_erasure_data,
) -> None:
    """Full erasure request based on the Delighted SaaS config"""

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow Delete

    privacy_request = PrivacyRequest(
        id=f"test_delighted_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": delighted_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = delighted_connection_config.get_saas_config().fides_key
    merged_graph = delighted_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [delighted_connection_config],
        {"email": delighted_erasure_identity_email},
        db,
    )


    assert_rows_match(
        v[f"{dataset_name}:people"],
        min_size=1,
        keys=[
            "id",
            "name",
            "email",
            "created_at",
            "last_sent_at",
            "last_responded_at",
            "next_survey_scheduled_at"
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:survey_response"],
        min_size=1,
        keys=[
            "id",
            "person",
            "survey_type",
            "score",
            "comment",
            "permalink",
            "created_at",
            "updated_at",
            "person_properties",
            "notes",
            "tags",
            "additional_answers"
        ],
    )

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [delighted_connection_config],
        {"email": delighted_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:people": 1,
        f"{dataset_name}:survey_response": 0,
    }

    delighted_secrets = delighted_connection_config.secrets
    auth = delighted_secrets["username"], delighted_secrets["api_key"]
    base_url = f"https://{delighted_secrets['domain']}"

    # people
    response = requests.get(
        url=f"{base_url}/v1/people.json",
        auth=auth,
        params={"email": delighted_erasure_identity_email},
    )
    # Delighted returns an empty object when a user is not found 
    response_body = response.json()
    assert response_body == []
    
    # #survey reponse
    # response = requests.get(
    #     url=f"{base_url}/v1/surevey_responses/{survey_response_id}",
    #     auth=auth,
    # )
    # # Since surevey_response is deleted, it won't be available so response is 404
    # assert response.status_code == 404
   
    # reset
    CONFIG.execution.masking_strict = masking_strict
