import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import CONFIG
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.fixtures.saas.sendgrid_fixtures import contact_exists
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.test_helpers.saas_test_utils import poll_for_existence


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
def test_sendgrid_connection_test(sendgrid_connection_config) -> None:
    get_connector(sendgrid_connection_config).test_connection()


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_sendgrid_access_request_task(
    db,
    policy,
    privacy_request,
    sendgrid_connection_config,
    sendgrid_dataset_config,
    sendgrid_identity_email,
    request,
    dsr_version,
) -> None:
    """Full access request based on the Sendgrid SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": sendgrid_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = sendgrid_connection_config.get_saas_config().fides_key
    merged_graph = sendgrid_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [sendgrid_connection_config],
        {"email": sendgrid_identity_email},
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
            "alternate_emails",
            "address_line_1",
            "address_line_2",
            "city",
            "state_province_region",
            "country",
            "postal_code",
            "phone_number",
            "whatsapp",
            "list_ids",
            "segment_ids",
            "created_at",
            "updated_at",
        ],
    )


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_sendgrid_erasure_request_task(
    db,
    privacy_request,
    dsr_version,
    request,
    erasure_policy_string_rewrite,
    sendgrid_secrets,
    sendgrid_connection_config,
    sendgrid_dataset_config,
    sendgrid_erasure_identity_email,
    sendgrid_erasure_data,
) -> None:
    """Full erasure request based on the Sendgrid SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    identity = Identity(**{"email": sendgrid_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = sendgrid_connection_config.get_saas_config().fides_key
    merged_graph = sendgrid_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    # access our erasure identity
    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [sendgrid_connection_config],
        {"email": sendgrid_erasure_identity_email},
        db,
    )

    # make sure erasure contact has expected fields
    assert_rows_match(
        v[f"{dataset_name}:contacts"],
        min_size=1,
        keys=[
            "id",
            "first_name",
            "last_name",
            "email",
            "alternate_emails",
            "address_line_1",
            "address_line_2",
            "city",
            "state_province_region",
            "country",
            "postal_code",
            "phone_number",
            "whatsapp",
            "list_ids",
            "segment_ids",
            "created_at",
            "updated_at",
        ],
    )
    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow delete
    erasure = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [sendgrid_connection_config],
        {"email": sendgrid_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )
    assert erasure == {"sendgrid_instance:contacts": 1}
    error_message = f"Contact with email {sendgrid_erasure_identity_email} could not be deleted in Sendgrid"
    poll_for_existence(
        contact_exists,
        (sendgrid_erasure_identity_email, sendgrid_secrets),
        error_message=error_message,
        existence_desired=False,
    )

    CONFIG.execution.masking_strict = temp_masking
