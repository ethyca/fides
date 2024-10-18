import json
from unittest import mock

import pytest

from fides.api.models.policy import ActionType
from fides.api.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    RequestTask,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.schemas.saas.saas_config import SaaSRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors import SaaSConnector, get_connector
from fides.api.service.privacy_request.request_runner_service import (
    build_consent_dataset_graph,
)
from tests.conftest import consent_runner_tester

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
def test_mailchimp_transactional_connection_test(
    mailchimp_transactional_connection_config,
) -> None:
    get_connector(mailchimp_transactional_connection_config).test_connection()

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.usefixtures("reset_mailchimp_transactional_data")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_mailchimp_transactional_consent_request_task_old_workflow(
    db,
    consent_policy,
    mailchimp_transactional_connection_config,
    mailchimp_transactional_dataset_config,
    mailchimp_transactional_identity_email,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Full consent request based on the Mailchimp Transactional (Mandrill) SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.consent_preferences = [
        {"data_use": "marketing.advertising", "opt_in": False}
    ]
    privacy_request.save(db)

    identity = Identity(**{"email": mailchimp_transactional_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = "mailchimp_transactional_instance"

    v = consent_runner_tester(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([mailchimp_transactional_dataset_config]),
        [mailchimp_transactional_connection_config],
        {"email": mailchimp_transactional_identity_email},
        db,
    )

    assert v == {
        f"{dataset_name}:{dataset_name}": True
    }, "graph has one node, and request completed successfully"

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    mailchimp_transactional_logs = execution_logs.filter_by(
        collection_name=dataset_name
    ).order_by("created_at")
    assert mailchimp_transactional_logs.count() == 2

    assert [log.status for log in mailchimp_transactional_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]

    for log in mailchimp_transactional_logs:
        assert log.dataset_name == dataset_name
        assert (
            log.collection_name == dataset_name
        ), "Node-level is given the same name as the dataset name"
        assert log.action_type == ActionType.consent

    connector = SaaSConnector(mailchimp_transactional_connection_config)
    connector.set_saas_request_state(
        SaaSRequest(path="test_path", method=HTTPMethod.GET)
    )  # dummy request as connector requires it
    request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.POST,
        path="/allowlists/list",
        body=json.dumps({"email": mailchimp_transactional_identity_email}),
    )
    response = connector.create_client().send(request)
    body = response.json()
    assert body == [], "Verify email has been removed from allowlist"

    request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.POST,
        path="/rejects/list",
        body=json.dumps({"email": mailchimp_transactional_identity_email}),
    )
    response = connector.create_client().send(request)
    body = response.json()[0]
    assert (
        body["email"] == mailchimp_transactional_identity_email
    ), "Verify email has been added to denylist"
    assert body["detail"] == "Added manually via the the API"

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_mailchimp_transactional_consent_prepared_requests_old_workflow(
    mocked_client_send,
    db,
    consent_policy,
    mailchimp_transactional_connection_config,
    mailchimp_transactional_dataset_config,
    mailchimp_transactional_identity_email,
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

    identity = Identity(**{"email": mailchimp_transactional_identity_email})
    privacy_request.cache_identity(identity)

    consent_runner_tester(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([mailchimp_transactional_dataset_config]),
        [mailchimp_transactional_connection_config],
        {"email": mailchimp_transactional_identity_email},
        db,
    )

    assert mocked_client_send.called
    saas_request_params: SaaSRequestParams = mocked_client_send.call_args[0][0]
    assert saas_request_params.path == "/rejects/add"
    assert (
        mailchimp_transactional_identity_email
        in mocked_client_send.call_args[0][0].body
    )

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_no_prepared_request_fired_without_consent_preferences_old_workflow(
    mocked_client_send,
    db,
    consent_policy,
    mailchimp_transactional_connection_config,
    mailchimp_transactional_dataset_config,
    mailchimp_transactional_identity_email,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Assert attributes of the PreparedRequest created by the client for running the consent request"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": mailchimp_transactional_identity_email})
    privacy_request.cache_identity(identity)

    consent_runner_tester(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([mailchimp_transactional_dataset_config]),
        [mailchimp_transactional_connection_config],
        {"email": mailchimp_transactional_identity_email},
        db,
    )

    assert not mocked_client_send.called

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.usefixtures("reset_mailchimp_transactional_data")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_mailchimp_transactional_consent_request_task_new_workflow(
    db,
    consent_policy,
    mailchimp_transactional_connection_config,
    mailchimp_transactional_dataset_config,
    mailchimp_transactional_identity_email,
    privacy_preference_history,
    privacy_preference_history_us_ca_provide,
    privacy_request,
    system,
    dsr_version,
    request,
) -> None:
    """Full consent request based on the Mailchimp Transactional (Mandrill) SaaS config
    with new workflow where preferences are saved w.r.t privacy notices

    Assert that only relevant preferences get "complete" log, others get "skipped"
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    mailchimp_transactional_connection_config.system_id = system.id
    mailchimp_transactional_connection_config.save(db)

    # This preference is relevant on data use
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

    # This preference is not relevant on data use
    privacy_preference_history_us_ca_provide.privacy_request_id = privacy_request.id
    privacy_preference_history_us_ca_provide.save(db=db)

    identity = Identity(**{"email": mailchimp_transactional_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = "mailchimp_transactional_instance"

    v = consent_runner_tester(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([mailchimp_transactional_dataset_config]),
        [mailchimp_transactional_connection_config],
        {"email": mailchimp_transactional_identity_email},
        db,
    )

    assert v == {
        f"{dataset_name}:{dataset_name}": True
    }, "graph has one node, and request completed successfully"

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    mailchimp_transactional_logs = execution_logs.filter_by(
        collection_name=dataset_name
    ).order_by("created_at")
    assert mailchimp_transactional_logs.count() == 2

    assert [log.status for log in mailchimp_transactional_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.complete,
    ]

    for log in mailchimp_transactional_logs:
        assert log.dataset_name == dataset_name
        assert (
            log.collection_name == dataset_name
        ), "Node-level is given the same name as the dataset name"
        assert log.action_type == ActionType.consent

    connector = SaaSConnector(mailchimp_transactional_connection_config)
    connector.set_saas_request_state(
        SaaSRequest(path="test_path", method=HTTPMethod.GET)
    )  # dummy request as connector requires it
    request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.POST,
        path="/allowlists/list",
        body=json.dumps({"email": mailchimp_transactional_identity_email}),
    )
    response = connector.create_client().send(request)
    body = response.json()
    assert body == [], "Verify email has been removed from allowlist"

    request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.POST,
        path="/rejects/list",
        body=json.dumps({"email": mailchimp_transactional_identity_email}),
    )
    response = connector.create_client().send(request)
    body = response.json()[0]
    assert (
        body["email"] == mailchimp_transactional_identity_email
    ), "Verify email has been added to denylist"
    assert body["detail"] == "Added manually via the the API"

    # Assert affected system status of "complete" is cached for consent reporting.
    # Secondary user ids added to this preference.
    assert privacy_preference_history.affected_system_status == {
        mailchimp_transactional_connection_config.system_key: ExecutionLogStatus.complete.value
    }
    assert privacy_preference_history.secondary_user_ids == {
        "email": mailchimp_transactional_identity_email
    }

    # Assert that preferences that aren't relevant for the given system show the system as skipped
    assert privacy_preference_history_us_ca_provide.affected_system_status == {
        mailchimp_transactional_connection_config.system_key: ExecutionLogStatus.skipped.value
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
async def test_mailchimp_transactional_consent_prepared_requests_new_workflow(
    mocked_client_send,
    db,
    consent_policy,
    mailchimp_transactional_connection_config,
    mailchimp_transactional_dataset_config,
    mailchimp_transactional_identity_email,
    privacy_preference_history,
    privacy_request_with_consent_policy,
    dsr_version,
    request,
) -> None:
    """Assert attributes of the PreparedRequest created by the client for running the consent request"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_preference_history.privacy_request_id = (
        privacy_request_with_consent_policy.id
    )
    privacy_preference_history.save(db=db)

    identity = Identity(**{"email": mailchimp_transactional_identity_email})
    privacy_request_with_consent_policy.cache_identity(identity)

    consent_runner_tester(
        privacy_request_with_consent_policy,
        consent_policy,
        build_consent_dataset_graph([mailchimp_transactional_dataset_config]),
        [mailchimp_transactional_connection_config],
        {"email": mailchimp_transactional_identity_email},
        db,
    )

    assert mocked_client_send.called
    saas_request_params: SaaSRequestParams = mocked_client_send.call_args[0][0]
    assert saas_request_params.path == "/rejects/add"
    assert (
        mailchimp_transactional_identity_email
        in mocked_client_send.call_args[0][0].body
    )

    assert privacy_preference_history.affected_system_status == {
        mailchimp_transactional_connection_config.system_key: ExecutionLogStatus.complete.value
    }
    assert privacy_preference_history.secondary_user_ids == {
        "email": mailchimp_transactional_identity_email
    }

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.usefixtures("reset_mailchimp_transactional_data")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_mailchimp_transactional_consent_request_task_new_workflow_skipped(
    db,
    consent_policy,
    mailchimp_transactional_connection_config,
    mailchimp_transactional_dataset_config,
    mailchimp_transactional_identity_email,
    system,
    privacy_preference_history_us_ca_provide,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Test privacy notice/data use system mismatch causes the request to be skipped"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    mailchimp_transactional_connection_config.system_id = system.id
    mailchimp_transactional_connection_config.save(db)

    privacy_preference_history_us_ca_provide.privacy_request_id = privacy_request.id
    privacy_preference_history_us_ca_provide.save(db=db)

    identity = Identity(**{"email": mailchimp_transactional_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = "mailchimp_transactional_instance"

    v = consent_runner_tester(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([mailchimp_transactional_dataset_config]),
        [mailchimp_transactional_connection_config],
        {"email": mailchimp_transactional_identity_email},
        db,
    )
    assert v == {
        f"{dataset_name}:{dataset_name}": False
    }, "graph has one node, and request skipped"

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    mailchimp_transactional_logs = execution_logs.filter_by(
        collection_name=dataset_name
    ).order_by("created_at")
    assert mailchimp_transactional_logs.count() == 2

    assert [log.status for log in mailchimp_transactional_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.skipped,
    ]

    for log in mailchimp_transactional_logs:
        assert log.dataset_name == dataset_name
        assert (
            log.collection_name == dataset_name
        ), "Node-level is given the same name as the dataset name"
        assert log.action_type == ActionType.consent

    # Assert affected system status of skipped is cached for consent reporting.
    # Secondary user ids not added because request skipped.
    assert privacy_preference_history_us_ca_provide.affected_system_status == {
        system.fides_key: "skipped"
    }
    assert not privacy_preference_history_us_ca_provide.secondary_user_ids

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.usefixtures("reset_mailchimp_transactional_data")
@mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_mailchimp_transactional_consent_request_task_error(
    mocked_client_send,
    db,
    consent_policy,
    mailchimp_transactional_connection_config,
    mailchimp_transactional_dataset_config,
    mailchimp_transactional_identity_email,
    system,
    privacy_preference_history,
    privacy_preference_history_us_ca_provide,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Assert logging is correctly created for privacy preferences on errored request
    Assert case when some privacy preferences were relevant but not all.
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    mocked_client_send.side_effect = Exception("KeyError")
    mailchimp_transactional_connection_config.system_id = system.id
    mailchimp_transactional_connection_config.save(db)

    # This preference matches on data use
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

    # This preference doesn't match on data use
    privacy_preference_history_us_ca_provide.privacy_request_id = privacy_request.id
    privacy_preference_history_us_ca_provide.save(db=db)

    identity = Identity(**{"email": mailchimp_transactional_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = "mailchimp_transactional_instance"

    if dsr_version == "use_dsr_2_0":
        with pytest.raises(Exception):
            consent_runner_tester(
                privacy_request,
                consent_policy,
                build_consent_dataset_graph([mailchimp_transactional_dataset_config]),
                [mailchimp_transactional_connection_config],
                {"email": mailchimp_transactional_identity_email},
                db,
            )
    else:
        consent_runner_tester(
            privacy_request,
            consent_policy,
            build_consent_dataset_graph([mailchimp_transactional_dataset_config]),
            [mailchimp_transactional_connection_config],
            {"email": mailchimp_transactional_identity_email},
            db,
        )
        rt = privacy_request.consent_tasks.filter(
            RequestTask.collection_address
            == "mailchimp_transactional_instance:mailchimp_transactional_instance"
        ).first()
        assert rt.status == ExecutionLogStatus.error  # Matches status of Execution Log
        terminator_task = privacy_request.get_terminate_task_by_action(
            ActionType.consent
        )
        # Terminator task was also marked "errored"
        assert terminator_task.status == ExecutionLogStatus.error

    execution_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id
    )

    mailchimp_transactional_logs = execution_logs.filter_by(
        collection_name=dataset_name
    ).order_by("created_at")
    assert mailchimp_transactional_logs.count() == 2

    assert [log.status for log in mailchimp_transactional_logs] == [
        ExecutionLogStatus.in_processing,
        ExecutionLogStatus.error,
    ]

    # Assert affected system status of error cached for consent reporting.
    db.refresh(privacy_preference_history)
    assert privacy_preference_history.affected_system_status == {
        system.fides_key: "error"
    }
    assert privacy_preference_history.secondary_user_ids == {
        "email": "customer-1@example.com"
    }
    db.refresh(privacy_preference_history_us_ca_provide)

    # This preference was not relevant on data use, so it was never considered
    # in propagation - preference shows system was skipped
    assert privacy_preference_history_us_ca_provide.affected_system_status == {
        system.fides_key: "skipped"
    }
    assert not privacy_preference_history_us_ca_provide.secondary_user_ids
