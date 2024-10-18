from unittest import mock

import pytest

from fides.api.models.policy import ActionType
from fides.api.models.privacy_request import ExecutionLog, ExecutionLogStatus
from fides.api.schemas.redis_cache import Identity
from fides.api.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.service.connectors import get_connector
from fides.api.service.privacy_request.request_runner_service import (
    build_consent_dataset_graph,
)
from tests.conftest import consent_runner_tester


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
def test_google_analytics_connection_test(
    google_analytics_connection_config,
) -> None:
    get_connector(google_analytics_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_google_analytics_consent_request_task_old_workflow(
    db,
    consent_policy,
    google_analytics_connection_config,
    google_analytics_dataset_config,
    google_analytics_client_id,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Full consent request based on the Google Analytics SaaS config"""
    privacy_request.consent_preferences = [
        {"data_use": "marketing.advertising", "opt_in": False}
    ]
    privacy_request.save(db)

    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"ga_client_id": google_analytics_client_id})
    privacy_request.cache_identity(identity)

    dataset_name = "google_analytics_instance"

    v = consent_runner_tester(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([google_analytics_dataset_config]),
        [google_analytics_connection_config],
        {"ga_client_id": google_analytics_client_id},
        db,
    )

    assert v == {
        f"{dataset_name}:{dataset_name}": True
    }, "graph has one node, and request completed successfully"

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    google_analytics_logs = execution_logs.filter_by(
        collection_name=dataset_name
    ).order_by("created_at")
    assert google_analytics_logs.count() == 2

    assert [log.status for log in google_analytics_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]

    for log in google_analytics_logs:
        assert log.dataset_name == dataset_name
        assert (
            log.collection_name == dataset_name
        ), "Node-level is given the same name as the dataset name"
        assert log.action_type == ActionType.consent


@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_google_analytics_consent_prepared_requests_old_workflow(
    mocked_client_send,
    db,
    consent_policy,
    google_analytics_connection_config,
    google_analytics_dataset_config,
    google_analytics_client_id,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Assert attributes of the PreparedRequest created by the client for running the consent request"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.consent_preferences = [
        {"data_use": "marketing.advertising", "opt_in": False}
    ]
    privacy_request.save(db)

    identity = Identity(**{"ga_client_id": google_analytics_client_id})
    privacy_request.cache_identity(identity)

    consent_runner_tester(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([google_analytics_dataset_config]),
        [google_analytics_connection_config],
        {"ga_client_id": google_analytics_client_id},
        db,
    )

    assert mocked_client_send.called
    saas_request_params: SaaSRequestParams = mocked_client_send.call_args[0][0]
    assert (
        saas_request_params.path
        == "/analytics/v3/userDeletion/userDeletionRequests:upsert"
    )
    body = mocked_client_send.call_args[0][0].body

    assert google_analytics_client_id in body
    assert google_analytics_connection_config.secrets["property_id"] in body


@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_google_analytics_no_ga_client_id_old_workflow(
    mocked_client_send,
    db,
    consent_policy,
    google_analytics_connection_config,
    google_analytics_dataset_config,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Test that the google analytics connector does not fail if there is no ga_client_id
    We skip the request because it is marked as skip_missing_param_values=True.

    We won't always have this piece of identity data.
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.consent_preferences = [
        {"data_use": "marketing.advertising", "opt_in": False}
    ]
    privacy_request.save(db)

    dataset_name = "google_analytics_instance"

    v = consent_runner_tester(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([google_analytics_dataset_config]),
        [google_analytics_connection_config],
        {},
        db,
    )

    assert not mocked_client_send.called
    assert v == {
        f"{dataset_name}:{dataset_name}": False
    }, "graph has one node which succeeded (consent request was skipped)"


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_google_analytics_no_ga_client_id_new_workflow(
    mocked_client_send,
    db,
    consent_policy,
    google_analytics_connection_config_without_secrets,
    google_analytics_dataset_config_no_secrets,
    privacy_preference_history,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Test google analytics connector skips instead of fails if identity missing."""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.save(db)
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

    dataset_name = "google_analytics_instance"

    v = consent_runner_tester(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([google_analytics_dataset_config_no_secrets]),
        [google_analytics_connection_config_without_secrets],
        {},
        db,
    )

    assert not mocked_client_send.called
    assert v == {
        f"{dataset_name}:{dataset_name}": False
    }, "graph has one node which succeeded (consent request was skipped)"

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    google_analytics_logs = execution_logs.filter_by(
        collection_name=dataset_name
    ).order_by("created_at")
    assert google_analytics_logs.count() == 2

    assert [log.status for log in google_analytics_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.skipped,
    ]

    for log in google_analytics_logs:
        assert log.dataset_name == dataset_name
        assert (
            log.collection_name == dataset_name
        ), "Node-level is given the same name as the dataset name"
        assert log.action_type == ActionType.consent

    # Assert GA is marked as skipped because we don't have the correct identifier
    db.refresh(privacy_preference_history)
    assert privacy_preference_history.affected_system_status == {
        "google_analytics_instance": "skipped"
    }
    assert not privacy_preference_history.secondary_user_ids


@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_google_analytics_consent_request_task_new_workflow(
    db,
    consent_policy,
    google_analytics_connection_config,
    google_analytics_dataset_config,
    google_analytics_client_id,
    privacy_preference_history,
    privacy_preference_history_us_ca_provide,
    system,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Full consent request based on the Google Analytics SaaS config
    for the new workflow where we save preferences w.r.t. privacy notices"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    google_analytics_connection_config.system_id = system.id
    google_analytics_connection_config.save(db)

    privacy_request.save(db)
    # This preference matches on data use
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

    # This preference does not match on data use
    privacy_preference_history_us_ca_provide.privacy_request_id = privacy_request.id
    privacy_preference_history_us_ca_provide.save(db=db)

    identity = Identity(**{"ga_client_id": google_analytics_client_id})
    privacy_request.cache_identity(identity)

    dataset_name = "google_analytics_instance"

    v = consent_runner_tester(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([google_analytics_dataset_config]),
        [google_analytics_connection_config],
        {"ga_client_id": google_analytics_client_id},
        db,
    )

    assert v == {
        f"{dataset_name}:{dataset_name}": True
    }, "graph has one node, and request completed successfully"

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    google_analytics_logs = execution_logs.filter_by(
        collection_name=dataset_name
    ).order_by("created_at")
    assert google_analytics_logs.count() == 2

    assert [log.status for log in google_analytics_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]

    for log in google_analytics_logs:
        assert log.dataset_name == dataset_name
        assert (
            log.collection_name == dataset_name
        ), "Node-level is given the same name as the dataset name"
        assert log.action_type == ActionType.consent

    # Google Analytics system added as complete to relevant privacy preference
    assert privacy_preference_history.affected_system_status == {
        google_analytics_connection_config.system_key: ExecutionLogStatus.complete.value
    }
    assert privacy_preference_history.secondary_user_ids == {
        "ga_client_id": google_analytics_client_id
    }

    # Google Analytics added as skipped to privacy preference not matching data use
    assert privacy_preference_history_us_ca_provide.affected_system_status == {
        google_analytics_connection_config.system_key: ExecutionLogStatus.skipped.value
    }
    assert not privacy_preference_history_us_ca_provide.secondary_user_ids


@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_google_analytics_consent_request_task_new_errored_workflow(
    mocked_client_send,
    db,
    consent_policy,
    google_analytics_connection_config,
    google_analytics_dataset_config,
    google_analytics_client_id,
    privacy_preference_history,
    privacy_preference_history_us_ca_provide,
    system,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Testing errored Google Analytics SaaS config
    for the new workflow where we save preferences w.r.t. privacy notices

    Assert logging created appropriately
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    mocked_client_send.side_effect = Exception("KeyError")

    google_analytics_connection_config.system_id = system.id
    google_analytics_connection_config.save(db)

    # This preference matches on data use
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

    # This preference does not match on data use
    privacy_preference_history_us_ca_provide.privacy_request_id = privacy_request.id
    privacy_preference_history_us_ca_provide.save(db=db)

    identity = Identity(**{"ga_client_id": google_analytics_client_id})
    privacy_request.cache_identity(identity)

    with pytest.raises(Exception):
        consent_runner_tester(
            privacy_request,
            consent_policy,
            build_consent_dataset_graph([google_analytics_dataset_config]),
            [google_analytics_connection_config],
            {"ga_client_id": google_analytics_client_id},
            db,
        )

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    google_analytics_logs = execution_logs.filter_by(
        collection_name=google_analytics_dataset_config.fides_key
    ).order_by("created_at")
    assert google_analytics_logs.count() == 2

    assert [log.status for log in google_analytics_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.error,
    ]

    # Google Analytics system added as errored to relevant privacy preference
    assert privacy_preference_history.affected_system_status == {
        google_analytics_connection_config.system_key: ExecutionLogStatus.error.value
    }
    assert privacy_preference_history.secondary_user_ids == {
        "ga_client_id": google_analytics_client_id
    }

    # Google Analytics added as skipped to privacy preference not matching data use
    assert privacy_preference_history_us_ca_provide.affected_system_status == {
        google_analytics_connection_config.system_key: ExecutionLogStatus.skipped.value
    }
    assert not privacy_preference_history_us_ca_provide.secondary_user_ids


@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_google_analytics_consent_prepared_requests_new_workflow(
    mocked_client_send,
    db,
    consent_policy,
    google_analytics_connection_config,
    google_analytics_dataset_config,
    google_analytics_client_id,
    privacy_preference_history,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Assert attributes of the PreparedRequest created by the client for running the consent request
    for the new workflow
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.save(db)
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

    identity = Identity(**{"ga_client_id": google_analytics_client_id})
    privacy_request.cache_identity(identity)

    consent_runner_tester(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([google_analytics_dataset_config]),
        [google_analytics_connection_config],
        {"ga_client_id": google_analytics_client_id},
        db,
    )

    assert mocked_client_send.called
    saas_request_params: SaaSRequestParams = mocked_client_send.call_args[0][0]
    assert (
        saas_request_params.path
        == "/analytics/v3/userDeletion/userDeletionRequests:upsert"
    )
    body = mocked_client_send.call_args[0][0].body

    assert google_analytics_client_id in body
    assert google_analytics_connection_config.secrets["property_id"] in body
