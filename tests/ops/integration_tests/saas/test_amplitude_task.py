import pytest

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import get_config
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match

CONFIG = get_config()


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
def test_amplitude_connection_test(amplitude_connection_config) -> None:
    get_connector(amplitude_connection_config).test_connection()


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_amplitude_access_request_task(
    db,
    policy,
    dsr_version,
    request,
    privacy_request,
    amplitude_connection_config,
    amplitude_dataset_config,
    amplitude_identity_email,
) -> None:
    """Full access request based on the Amplitude SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": amplitude_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = amplitude_connection_config.get_saas_config().fides_key
    merged_graph = amplitude_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [amplitude_connection_config],
        {"email": amplitude_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:user"],
        min_size=1,
        keys=[
            "user_id",
            "amplitude_id",
            "last_device_id",
            "last_seen",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:user_details"],
        min_size=1,
        keys=[
            "revenue",
            "purchases",
            "user_id",
            "last_device_id",
            "canonical_amplitude_id",
            "merged_amplitude_ids",
            "merge_times",
            "properties",
            "aliasing_user_ids",
            "aliased_user_id",
            "aliasing_profiles",
            "num_events",
            "num_sessions",
            "usage_time",
            "device_ids",
            "first_used",
            "last_used",
            "last_location",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:events"],
        min_size=1,
        keys=[
            "app",
            "device_id",
            "user_id",
            "client_event_time",
            "event_id",
            "session_id",
            "event_type",
            "amplitude_event_type",
            "version_name",
            "platform",
            "os_name",
            "os_version",
            "data_type",
            "device_brand",
            "device_manufacturer",
            "device_model",
            "device_family",
            "device_type",
            "device_carrier",
            "location_lat",
            "location_lng",
            "ip_address",
            "country",
            "language",
            "library",
            "city",
            "region",
            "dma",
            "event_properties",
            "user_properties",
            "global_user_properties",
            "group_properties",
            "event_time",
            "client_upload_time",
            "server_upload_time",
            "server_received_time",
            "amplitude_id",
            "idfa",
            "adid",
            "data",
            "paying",
            "start_version",
            "user_creation_time",
            "uuid",
            "groups",
            "sample_rate",
            "$insert_id",
            "$insert_key",
            "is_attribution_event",
            "amplitude_attribution_ids",
            "plan",
            "partner_id",
            "source_id",
            "$schema",
            "raw_event_type",
            "os",
        ],
    )

    # verify we only returned data for our identity email
    assert v[f"{dataset_name}:user"][0]["user_id"] == amplitude_identity_email

    assert v[f"{dataset_name}:user_details"][0]["user_id"] == amplitude_identity_email


@pytest.mark.skip(reason="Temporarily disabled test")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_amplitude_erasure_request_task(
    db,
    dsr_version,
    request,
    privacy_request,
    erasure_policy_string_rewrite,
    amplitude_connection_config,
    amplitude_dataset_config,
    amplitude_erasure_identity_email,
    amplitude_create_erasure_data,
) -> None:
    """Full erasure request based on the Amplitude SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False  # Allow Delete

    identity = Identity(**{"email": amplitude_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = amplitude_connection_config.get_saas_config().fides_key
    merged_graph = amplitude_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [amplitude_connection_config],
        {"email": amplitude_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:user"],
        min_size=1,
        keys=[
            "user_id",
            "amplitude_id",
            "last_device_id",
            "last_seen",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:user_details"],
        min_size=1,
        keys=[
            "revenue",
            "purchases",
            "user_id",
            "last_device_id",
            "canonical_amplitude_id",
            "merged_amplitude_ids",
            "merge_times",
            "version",
            "country",
            "language",
            "library",
            "ip_address",
            "platform",
            "os",
            "device",
            "device_type",
            "carrier",
            "start_version",
            "paying",
            "city",
            "region",
            "dma",
            "properties",
            "aliasing_user_ids",
            "aliased_user_id",
            "aliasing_profiles",
            "num_events",
            "num_sessions",
            "usage_time",
            "device_ids",
            "last_location",
        ],
    )

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [amplitude_connection_config],
        {"email": amplitude_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:user": 1,
        f"{dataset_name}:user_details": 0,
        f"{dataset_name}:events": 0,
    }

    CONFIG.execution.masking_strict = masking_strict
