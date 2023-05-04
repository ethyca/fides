from unittest import mock
from uuid import uuid4

import pytest

from fides.api.ops.models.policy import ActionType
from fides.api.ops.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
    PrivacyRequestStatus,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.service.privacy_request.request_runner_service import (
    build_consent_dataset_graph,
)
from fides.api.ops.task import graph_task


@pytest.mark.integration_saas
@pytest.mark.integration_universal_analytics
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
def test_universal_analytics_connection_test(
    universal_analytics_connection_config,
) -> None:
    get_connector(universal_analytics_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_universal_analytics
@pytest.mark.asyncio
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
async def test_universal_analytics_consent_request_task_old_workflow(
    db,
    consent_policy,
    universal_analytics_connection_config,
    universal_analytics_dataset_config,
    universal_analytics_client_id,
) -> None:
    """Full consent request based on the Google Analytics SaaS config"""

    privacy_request = PrivacyRequest(
        id=str(uuid4()),
        consent_preferences=[{"data_use": "advertising", "opt_in": False}],
    )

    identity = Identity(**{"ga_client_id": universal_analytics_client_id})
    privacy_request.cache_identity(identity)

    dataset_name = "universal_analytics_instance"

    v = await graph_task.run_consent_request(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([universal_analytics_dataset_config]),
        [universal_analytics_connection_config],
        {"ga_client_id": universal_analytics_client_id},
        db,
    )

    assert v == {
        f"{dataset_name}:{dataset_name}": True
    }, "graph has one node, and request completed successfully"

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    universal_analytics_logs = execution_logs.filter_by(
        collection_name=dataset_name
    ).order_by("created_at")
    assert universal_analytics_logs.count() == 2

    assert [log.status for log in universal_analytics_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]

    for log in universal_analytics_logs:
        assert log.dataset_name == dataset_name
        assert (
            log.collection_name == dataset_name
        ), "Node-level is given the same name as the dataset name"
        assert log.action_type == ActionType.consent


@pytest.mark.integration_saas
@pytest.mark.integration_universal_analytics
@pytest.mark.asyncio
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@mock.patch("fides.api.ops.service.connectors.saas_connector.AuthenticatedClient.send")
async def test_universal_analytics_consent_prepared_requests_old_workflow(
    mocked_client_send,
    db,
    consent_policy,
    universal_analytics_connection_config,
    universal_analytics_dataset_config,
    universal_analytics_client_id,
) -> None:
    """Assert attributes of the PreparedRequest created by the client for running the consent request"""

    privacy_request = PrivacyRequest(
        id=str(uuid4()),
        consent_preferences=[{"data_use": "advertising", "opt_in": False}],
    )

    identity = Identity(**{"ga_client_id": universal_analytics_client_id})
    privacy_request.cache_identity(identity)

    await graph_task.run_consent_request(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([universal_analytics_dataset_config]),
        [universal_analytics_connection_config],
        {"ga_client_id": universal_analytics_client_id},
        db,
    )

    assert mocked_client_send.called
    saas_request_params: SaaSRequestParams = mocked_client_send.call_args[0][0]
    assert (
        saas_request_params.path
        == "/analytics/v3/userDeletion/userDeletionRequests:upsert"
    )
    body = mocked_client_send.call_args[0][0].body

    assert universal_analytics_client_id in body
    assert universal_analytics_connection_config.secrets["web_property_id"] in body


@pytest.mark.integration_saas
@pytest.mark.integration_universal_analytics
@pytest.mark.asyncio
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@mock.patch("fides.api.ops.service.connectors.saas_connector.AuthenticatedClient.send")
async def test_universal_analytics_no_ga_client_id_old_workflow(
    mocked_client_send,
    db,
    consent_policy,
    universal_analytics_connection_config,
    universal_analytics_dataset_config,
) -> None:
    """Test that the universal analytics connector does not fail if there is no ga_client_id
    We skip the request because it is marked as skip_missing_param_values=True.

    We won't always have this piece of identity data.
    """

    privacy_request = PrivacyRequest(
        id=str(uuid4()),
        consent_preferences=[{"data_use": "advertising", "opt_in": False}],
    )
    dataset_name = "universal_analytics_instance"

    v = await graph_task.run_consent_request(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([universal_analytics_dataset_config]),
        [universal_analytics_connection_config],
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


@pytest.mark.integration_saas
@pytest.mark.integration_universal_analytics
@pytest.mark.asyncio
@mock.patch("fides.api.ops.service.connectors.saas_connector.AuthenticatedClient.send")
async def test_universal_analytics_no_ga_client_id_new_workflow(
    mocked_client_send,
    db,
    consent_policy,
    universal_analytics_connection_config_without_secrets,
    universal_analytics_dataset_config_without_secrets,
    privacy_preference_history,
) -> None:
    """Test universal analytics connector skips instead of fails if identity missing."""
    privacy_request = PrivacyRequest(
        id=str(uuid4()), status=PrivacyRequestStatus.pending
    )
    privacy_request.save(db)
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

    dataset_name = "universal_analytics_instance"

    v = await graph_task.run_consent_request(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph(
            [universal_analytics_dataset_config_without_secrets]
        ),
        [universal_analytics_connection_config_without_secrets],
        {},
        db,
    )
    assert not mocked_client_send.called
    assert v == {
        f"{dataset_name}:{dataset_name}": False
    }, "graph has one node which skipped (consent request was skipped)"

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    universal_analytics_logs = execution_logs.filter_by(
        collection_name=dataset_name
    ).order_by("created_at")
    assert universal_analytics_logs.count() == 2

    assert [log.status for log in universal_analytics_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.skipped,
    ]

    for log in universal_analytics_logs:
        assert log.dataset_name == dataset_name
        assert (
            log.collection_name == dataset_name
        ), "Node-level is given the same name as the dataset name"
        assert log.action_type == ActionType.consent

    assert privacy_preference_history.affected_system_status == {
        universal_analytics_connection_config_without_secrets.system_key: ExecutionLogStatus.skipped.value
    }
    assert not privacy_preference_history.secondary_user_ids


@pytest.mark.integration_saas
@pytest.mark.integration_universal_analytics
@pytest.mark.asyncio
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
async def test_universal_analytics_consent_request_task_new_workflow(
    db,
    consent_policy,
    universal_analytics_connection_config,
    universal_analytics_dataset_config,
    universal_analytics_client_id,
    privacy_preference_history,
    privacy_preference_history_us_ca_provide,
    system,
) -> None:
    """Full consent request based on the Google Analytics SaaS config
    for the new workflow where we save consent with respect to privacy preferences
    """
    universal_analytics_connection_config.system_id = system.id
    universal_analytics_connection_config.save(db)

    privacy_request = PrivacyRequest(
        id=str(uuid4()), status=PrivacyRequestStatus.pending
    )
    privacy_request.save(db)
    # This preference matches on data use
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

    # This preference does not match on data use
    privacy_preference_history_us_ca_provide.privacy_request_id = privacy_request.id
    privacy_preference_history_us_ca_provide.save(db=db)

    identity = Identity(**{"ga_client_id": universal_analytics_client_id})
    privacy_request.cache_identity(identity)

    dataset_name = "universal_analytics_instance"

    v = await graph_task.run_consent_request(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([universal_analytics_dataset_config]),
        [universal_analytics_connection_config],
        {"ga_client_id": universal_analytics_client_id},
        db,
    )

    assert v == {
        f"{dataset_name}:{dataset_name}": True
    }, "graph has one node, and request completed successfully"

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    universal_analytics_logs = execution_logs.filter_by(
        collection_name=dataset_name
    ).order_by("created_at")
    assert universal_analytics_logs.count() == 2

    assert [log.status for log in universal_analytics_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]

    for log in universal_analytics_logs:
        assert log.dataset_name == dataset_name
        assert (
            log.collection_name == dataset_name
        ), "Node-level is given the same name as the dataset name"
        assert log.action_type == ActionType.consent

    # Universal Analytics system added as complete to relevant privacy preference
    assert privacy_preference_history.affected_system_status == {
        universal_analytics_connection_config.system_key: ExecutionLogStatus.complete.value
    }
    assert privacy_preference_history.secondary_user_ids == {
        "ga_client_id": universal_analytics_client_id
    }

    # Universal Analytics added as skipped to privacy preference not matching data use
    assert privacy_preference_history_us_ca_provide.affected_system_status == {
        universal_analytics_connection_config.system_key: ExecutionLogStatus.skipped.value
    }
    assert not privacy_preference_history_us_ca_provide.secondary_user_ids


@pytest.mark.integration_saas
@pytest.mark.integration_universal_analytics
@pytest.mark.asyncio
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@mock.patch("fides.api.ops.service.connectors.saas_connector.AuthenticatedClient.send")
async def test_universal_analytics_consent_request_task_new_errored_workflow(
    mocked_client_send,
    db,
    consent_policy,
    universal_analytics_connection_config,
    universal_analytics_dataset_config,
    universal_analytics_client_id,
    privacy_preference_history,
    privacy_preference_history_us_ca_provide,
    system,
) -> None:
    """Testing errored Universal Analytics SaaS config
    for the new workflow where we save preferences w.r.t. privacy notices

    Assert logging created appropriately
    """
    mocked_client_send.side_effect = Exception("KeyError")

    universal_analytics_connection_config.system_id = system.id
    universal_analytics_connection_config.save(db)

    privacy_request = PrivacyRequest(
        id=str(uuid4()), status=PrivacyRequestStatus.pending
    )
    privacy_request.save(db)
    # This preference matches on data use
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

    # This preference does not match on data use
    privacy_preference_history_us_ca_provide.privacy_request_id = privacy_request.id
    privacy_preference_history_us_ca_provide.save(db=db)

    identity = Identity(**{"ga_client_id": universal_analytics_client_id})
    privacy_request.cache_identity(identity)

    dataset_name = "universal_analytics_instance"

    with pytest.raises(Exception):
        await graph_task.run_consent_request(
            privacy_request,
            consent_policy,
            build_consent_dataset_graph([universal_analytics_dataset_config]),
            [universal_analytics_connection_config],
            {"ga_client_id": universal_analytics_client_id},
            db,
        )

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    universal_analytics_logs = execution_logs.filter_by(
        collection_name=dataset_name
    ).order_by("created_at")
    assert universal_analytics_logs.count() == 2

    assert [log.status for log in universal_analytics_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.error,
    ]

    # Universal Analytics system added as complete to relevant privacy preference
    assert privacy_preference_history.affected_system_status == {
        universal_analytics_connection_config.system_key: ExecutionLogStatus.error.value
    }
    assert privacy_preference_history.secondary_user_ids == {
        "ga_client_id": universal_analytics_client_id
    }

    # Universal Analytics added as skipped to privacy preference not matching data use
    assert privacy_preference_history_us_ca_provide.affected_system_status == {
        universal_analytics_connection_config.system_key: ExecutionLogStatus.skipped.value
    }
    assert not privacy_preference_history_us_ca_provide.secondary_user_ids


@pytest.mark.integration_saas
@pytest.mark.integration_universal_analytics
@pytest.mark.asyncio
@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@mock.patch("fides.api.ops.service.connectors.saas_connector.AuthenticatedClient.send")
async def test_universal_analytics_consent_prepared_requests_new_workflow(
    mocked_client_send,
    db,
    consent_policy,
    universal_analytics_connection_config,
    universal_analytics_dataset_config,
    universal_analytics_client_id,
    privacy_preference_history,
) -> None:
    """Assert attributes of the PreparedRequest created by the client for running the consent request"""

    privacy_request = PrivacyRequest(
        id=str(uuid4()), status=PrivacyRequestStatus.pending
    )
    privacy_request.save(db)
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

    identity = Identity(**{"ga_client_id": universal_analytics_client_id})
    privacy_request.cache_identity(identity)

    await graph_task.run_consent_request(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([universal_analytics_dataset_config]),
        [universal_analytics_connection_config],
        {"ga_client_id": universal_analytics_client_id},
        db,
    )

    assert mocked_client_send.called
    saas_request_params: SaaSRequestParams = mocked_client_send.call_args[0][0]
    assert (
        saas_request_params.path
        == "/analytics/v3/userDeletion/userDeletionRequests:upsert"
    )
    body = mocked_client_send.call_args[0][0].body

    assert universal_analytics_client_id in body
    assert universal_analytics_connection_config.secrets["web_property_id"] in body
