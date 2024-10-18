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
def test_wunderkind_connection_test(
    wunderkind_connection_config,
) -> None:
    get_connector(wunderkind_connection_config).test_connection()

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_wunderkind_consent_request_task_old_workflow(
    db,
    consent_policy,
    wunderkind_connection_config,
    wunderkind_dataset_config,
    wunderkind_identity_email,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Full consent request based on the Wunderkind SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.consent_preferences = [
        {"data_use": "marketing.advertising", "opt_in": False}
    ]
    privacy_request.save(db)

    identity = Identity(**{"email": wunderkind_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = "wunderkind_instance"

    v = consent_runner_tester(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([wunderkind_dataset_config]),
        [wunderkind_connection_config],
        {"email": wunderkind_identity_email},
        db,
    )

    assert v == {
        f"{dataset_name}:{dataset_name}": True
    }, "graph has one node, and request completed successfully"

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    wunderkind_logs = execution_logs.filter_by(collection_name=dataset_name).order_by(
        "created_at"
    )
    assert wunderkind_logs.count() == 2

    assert [log.status for log in wunderkind_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]

    for log in wunderkind_logs:
        assert log.dataset_name == dataset_name
        assert (
            log.collection_name == dataset_name
        ), "Node-level is given the same name as the dataset name"
        assert log.action_type == ActionType.consent

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_wunderkind_consent_prepared_requests_old_workflow(
    mocked_client_send,
    db,
    consent_policy,
    wunderkind_connection_config,
    wunderkind_dataset_config,
    wunderkind_identity_email,
    dsr_version,
    request,
    privacy_request,
) -> None:
    """Assert attributes of the PreparedRequest created by the client for running the consent request"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.consent_preferences = [
        {"data_use": "marketing.advertising", "opt_in": False}
    ]
    privacy_request.save(db)

    identity = Identity(**{"email": wunderkind_identity_email})
    privacy_request.cache_identity(identity)

    consent_runner_tester(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([wunderkind_dataset_config]),
        [wunderkind_connection_config],
        {"email": wunderkind_identity_email},
        db,
    )

    assert mocked_client_send.called
    saas_request_params: SaaSRequestParams = mocked_client_send.call_args[0][0]
    assert saas_request_params.path == "/ccpa"
    query_params = mocked_client_send.call_args[0][0].query_params
    assert query_params["id_type"] == "email"
    assert query_params["id_value"] == wunderkind_identity_email
    assert query_params["consent"] == "1YY"
    assert (
        query_params["website_id"] == wunderkind_connection_config.secrets["website_id"]
    )

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_wunderkind_consent_request_task_new_workflow(
    db,
    consent_policy,
    wunderkind_connection_config,
    wunderkind_dataset_config,
    wunderkind_identity_email,
    privacy_preference_history,
    privacy_preference_history_us_ca_provide,
    system,
    dsr_version,
    request,
    privacy_request,
) -> None:
    """Full consent request based on the Wunderkind SaaS config and new workflow"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    wunderkind_connection_config.system_id = system.id
    wunderkind_connection_config.save(db)

    # This preference matches on data use
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

    # This preference does not match on data use
    privacy_preference_history_us_ca_provide.privacy_request_id = privacy_request.id
    privacy_preference_history_us_ca_provide.save(db=db)

    identity = Identity(**{"email": wunderkind_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = "wunderkind_instance"

    v = consent_runner_tester(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([wunderkind_dataset_config]),
        [wunderkind_connection_config],
        {"email": wunderkind_identity_email},
        db,
    )

    assert v == {
        f"{dataset_name}:{dataset_name}": True
    }, "graph has one node, and request completed successfully"

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    wunderkind_logs = execution_logs.filter_by(collection_name=dataset_name).order_by(
        "created_at"
    )
    assert wunderkind_logs.count() == 2

    assert [log.status for log in wunderkind_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]

    for log in wunderkind_logs:
        assert log.dataset_name == dataset_name
        assert (
            log.collection_name == dataset_name
        ), "Node-level is given the same name as the dataset name"
        assert log.action_type == ActionType.consent

    # Wunderkind added as completed to relevant privacy preference
    assert privacy_preference_history.affected_system_status == {
        wunderkind_connection_config.system_key: ExecutionLogStatus.complete.value
    }
    assert privacy_preference_history.secondary_user_ids == {
        "email": wunderkind_identity_email
    }

    # Wunderkind added as skipped to privacy preference not matching data use
    assert privacy_preference_history_us_ca_provide.affected_system_status == {
        wunderkind_connection_config.system_key: ExecutionLogStatus.skipped.value
    }
    assert not privacy_preference_history_us_ca_provide.secondary_user_ids

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_wunderkind_errored_logging_new_workflow(
    mocked_client_send,
    db,
    consent_policy,
    wunderkind_connection_config,
    wunderkind_dataset_config,
    wunderkind_identity_email,
    privacy_preference_history,
    privacy_preference_history_us_ca_provide,
    system,
    dsr_version,
    request,
    privacy_request,
) -> None:
    """Test wunderkind errors have proper logs created"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    mocked_client_send.side_effect = Exception("KeyError")
    wunderkind_connection_config.system_id = system.id
    wunderkind_connection_config.save(db)

    # This preference matches on data use
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

    # This preference does not match on data use
    privacy_preference_history_us_ca_provide.privacy_request_id = privacy_request.id
    privacy_preference_history_us_ca_provide.save(db=db)

    identity = Identity(**{"email": wunderkind_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = "wunderkind_instance"

    if dsr_version == "use_dsr_2_0":
        with pytest.raises(Exception):
            consent_runner_tester(
                privacy_request,
                consent_policy,
                build_consent_dataset_graph([wunderkind_dataset_config]),
                [wunderkind_connection_config],
                {"email": wunderkind_identity_email},
                db,
            )
    else:
        consent_runner_tester(
            privacy_request,
            consent_policy,
            build_consent_dataset_graph([wunderkind_dataset_config]),
            [wunderkind_connection_config],
            {"email": wunderkind_identity_email},
            db,
        )
        # Current task and terminator task were marked as error
        assert [rt.status.value for rt in privacy_request.consent_tasks] == [
            "complete",
            "error",
            "error",
        ]

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    wunderkind_logs = execution_logs.filter_by(collection_name=dataset_name).order_by(
        "created_at"
    )
    assert wunderkind_logs.count() == 2

    assert [log.status for log in wunderkind_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.error,
    ]

    # Wunderkind system added as errored to relevant privacy preference
    assert privacy_preference_history.affected_system_status == {
        wunderkind_connection_config.system_key: ExecutionLogStatus.error.value
    }
    assert privacy_preference_history.secondary_user_ids == {
        "email": wunderkind_identity_email
    }

    # Wunderkind added as skipped to privacy preference not matching data use
    assert privacy_preference_history_us_ca_provide.affected_system_status == {
        wunderkind_connection_config.system_key: ExecutionLogStatus.skipped.value
    }
    assert not privacy_preference_history_us_ca_provide.secondary_user_ids

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_wunderkind_consent_prepared_requests_new_workflow(
    mocked_client_send,
    db,
    consent_policy,
    wunderkind_connection_config,
    wunderkind_dataset_config,
    wunderkind_identity_email,
    privacy_preference_history,
    dsr_version,
    request,
    privacy_request,
) -> None:
    """Assert attributes of the PreparedRequest created by the client for running the consent request"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

    identity = Identity(**{"email": wunderkind_identity_email})
    privacy_request.cache_identity(identity)

    consent_runner_tester(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([wunderkind_dataset_config]),
        [wunderkind_connection_config],
        {"email": wunderkind_identity_email},
        db,
    )

    assert mocked_client_send.called
    saas_request_params: SaaSRequestParams = mocked_client_send.call_args[0][0]
    assert saas_request_params.path == "/ccpa"
    query_params = mocked_client_send.call_args[0][0].query_params
    assert query_params["id_type"] == "email"
    assert query_params["id_value"] == wunderkind_identity_email
    assert query_params["consent"] == "1YY"
    assert (
        query_params["website_id"] == wunderkind_connection_config.secrets["website_id"]
    )

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_wunderkind_skipped_new_workflow(
    db,
    consent_policy,
    wunderkind_connection_config,
    wunderkind_dataset_config,
    wunderkind_identity_email,
    system,
    privacy_preference_history_us_ca_provide,
    dsr_version,
    request,
    privacy_request,
) -> None:
    """Data use mismatch between notice and system should cause request to not fire"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    wunderkind_connection_config.system_id = system.id
    wunderkind_connection_config.save(db)

    privacy_preference_history_us_ca_provide.privacy_request_id = privacy_request.id
    privacy_preference_history_us_ca_provide.save(db=db)

    identity = Identity(**{"email": wunderkind_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = "wunderkind_instance"

    v = consent_runner_tester(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([wunderkind_dataset_config]),
        [wunderkind_connection_config],
        {"email": wunderkind_identity_email},
        db,
    )

    assert v == {
        f"{dataset_name}:{dataset_name}": False
    }, "graph has one node, and request did not fire"

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    wunderkind_logs = execution_logs.filter_by(collection_name=dataset_name).order_by(
        "created_at"
    )
    assert wunderkind_logs.count() == 2

    assert [log.status for log in wunderkind_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.skipped,
    ]

    assert privacy_preference_history_us_ca_provide.affected_system_status == {
        wunderkind_connection_config.system_key: ExecutionLogStatus.skipped.value
    }
    assert not privacy_preference_history_us_ca_provide.secondary_user_ids
