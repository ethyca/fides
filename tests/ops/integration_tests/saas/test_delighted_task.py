import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import get_config
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.test_helpers.saas_test_utils import poll_for_existence

CONFIG = get_config()


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
def test_delighted_connection_test(delighted_connection_config) -> None:
    get_connector(delighted_connection_config).test_connection()


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_delighted_access_request_task(
    db,
    dsr_version,
    request,
    policy,
    privacy_request,
    delighted_connection_config,
    delighted_dataset_config,
    delighted_identity_email,
) -> None:
    """Full access request based on the Delighted SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": delighted_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = delighted_connection_config.get_saas_config().fides_key
    merged_graph = delighted_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [delighted_connection_config],
        {"email": delighted_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:person"],
        min_size=1,
        keys=[
            "id",
            "name",
            "email",
            "created_at",
            "last_sent_at",
            "last_responded_at",
            "next_survey_scheduled_at",
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
            "additional_answers",
        ],
    )

    # verify we only returned data for our identity email
    assert v[f"{dataset_name}:person"][0]["email"] == delighted_identity_email
    person_id = v[f"{dataset_name}:person"][0]["id"]

    assert v[f"{dataset_name}:survey_response"][0]["person"] == person_id


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_delighted_erasure_request_task(
    db,
    policy,
    dsr_version,
    request,
    privacy_request,
    erasure_policy_string_rewrite,
    delighted_connection_config,
    delighted_dataset_config,
    delighted_erasure_identity_email,
    delighted_create_erasure_data,
    delighted_test_client,
) -> None:
    """Full erasure request based on the Delighted SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    person = delighted_create_erasure_data

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow Delete

    identity = Identity(**{"email": delighted_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = delighted_connection_config.get_saas_config().fides_key
    merged_graph = delighted_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [delighted_connection_config],
        {"email": delighted_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:person"],
        min_size=1,
        keys=[
            "id",
            "name",
            "email",
            "created_at",
            "last_sent_at",
            "last_responded_at",
            "next_survey_scheduled_at",
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
            "additional_answers",
        ],
    )

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [delighted_connection_config],
        {"email": delighted_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:person": 1,
        f"{dataset_name}:survey_response": 0,
    }

    # person
    poll_for_existence(
        delighted_test_client.get_person,
        (delighted_erasure_identity_email,),
        existence_desired=False,
    )

    # survey response
    poll_for_existence(
        delighted_test_client.get_survey_responses,
        (person["id"],),
        existence_desired=False,
    )

    # reset
    CONFIG.execution.masking_strict = masking_strict
