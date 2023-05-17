import json
from unittest import mock
from uuid import uuid4

import pytest

from fides.api.models.policy import ActionType
from fides.api.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
    PrivacyRequestStatus,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.schemas.saas.saas_config import SaaSRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors import SaaSConnector, get_connector
from fides.api.service.privacy_request.request_runner_service import (
    build_consent_dataset_graph,
)
from fides.api.task import graph_task


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp_transactional
def test_mailchimp_transactional_connection_test(
    mailchimp_transactional_connection_config,
) -> None:
    get_connector(mailchimp_transactional_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp_transactional
@pytest.mark.asyncio
@pytest.mark.usefixtures("reset_mailchimp_transactional_data")
async def test_mailchimp_transactional_consent_request_task_old_workflow(
    db,
    consent_policy,
    mailchimp_transactional_connection_config,
    mailchimp_transactional_dataset_config,
    mailchimp_transactional_identity_email,
) -> None:
    """Full consent request based on the Mailchimp Transactional (Mandrill) SaaS config"""

    privacy_request = PrivacyRequest(
        id=str(uuid4()),
        consent_preferences=[{"data_use": "advertising", "opt_in": False}],
    )

    identity = Identity(**{"email": mailchimp_transactional_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = "mailchimp_transactional_instance"

    v = await graph_task.run_consent_request(
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


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp_transactional
@pytest.mark.asyncio
@mock.patch("fides.api.ops.service.connectors.saas_connector.AuthenticatedClient.send")
async def test_mailchimp_transactional_consent_prepared_requests_old_workflow(
    mocked_client_send,
    db,
    consent_policy,
    mailchimp_transactional_connection_config,
    mailchimp_transactional_dataset_config,
    mailchimp_transactional_identity_email,
) -> None:
    """Assert attributes of the PreparedRequest created by the client for running the consent request"""

    privacy_request = PrivacyRequest(
        id=str(uuid4()),
        consent_preferences=[{"data_use": "advertising", "opt_in": False}],
    )

    identity = Identity(**{"email": mailchimp_transactional_identity_email})
    privacy_request.cache_identity(identity)

    await graph_task.run_consent_request(
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


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp_transactional
@pytest.mark.asyncio
@mock.patch("fides.api.ops.service.connectors.saas_connector.AuthenticatedClient.send")
async def test_no_prepared_request_fired_without_consent_preferences_old_workflow(
    mocked_client_send,
    db,
    consent_policy,
    mailchimp_transactional_connection_config,
    mailchimp_transactional_dataset_config,
    mailchimp_transactional_identity_email,
) -> None:
    """Assert attributes of the PreparedRequest created by the client for running the consent request"""

    privacy_request = PrivacyRequest(
        id=str(uuid4()),
    )

    identity = Identity(**{"email": mailchimp_transactional_identity_email})
    privacy_request.cache_identity(identity)

    await graph_task.run_consent_request(
        privacy_request,
        consent_policy,
        build_consent_dataset_graph([mailchimp_transactional_dataset_config]),
        [mailchimp_transactional_connection_config],
        {"email": mailchimp_transactional_identity_email},
        db,
    )

    assert not mocked_client_send.called


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp_transactional
@pytest.mark.asyncio
@pytest.mark.usefixtures("reset_mailchimp_transactional_data")
async def test_mailchimp_transactional_consent_request_task_new_workflow(
    db,
    consent_policy,
    mailchimp_transactional_connection_config,
    mailchimp_transactional_dataset_config,
    mailchimp_transactional_identity_email,
    privacy_preference_history,
    privacy_preference_history_us_ca_provide,
    system,
) -> None:
    """Full consent request based on the Mailchimp Transactional (Mandrill) SaaS config
    with new workflow where preferences are saved w.r.t privacy notices

    Assert that only relevant preferences get "complete" log, others get "skipped"
    """
    mailchimp_transactional_connection_config.system_id = system.id
    mailchimp_transactional_connection_config.save(db)

    privacy_request = PrivacyRequest(
        id=str(uuid4()), status=PrivacyRequestStatus.pending
    )
    privacy_request.save(db)
    # This preference is relevant on data use
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

    # This preference is not relevant on data use
    privacy_preference_history_us_ca_provide.privacy_request_id = privacy_request.id
    privacy_preference_history_us_ca_provide.save(db=db)

    identity = Identity(**{"email": mailchimp_transactional_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = "mailchimp_transactional_instance"

    v = await graph_task.run_consent_request(
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


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp_transactional
@pytest.mark.asyncio
@mock.patch("fides.api.ops.service.connectors.saas_connector.AuthenticatedClient.send")
async def test_mailchimp_transactional_consent_prepared_requests_new_workflow(
    mocked_client_send,
    db,
    consent_policy,
    mailchimp_transactional_connection_config,
    mailchimp_transactional_dataset_config,
    mailchimp_transactional_identity_email,
    privacy_preference_history,
    privacy_request_with_consent_policy,
) -> None:
    """Assert attributes of the PreparedRequest created by the client for running the consent request"""

    privacy_preference_history.privacy_request_id = (
        privacy_request_with_consent_policy.id
    )
    privacy_preference_history.save(db=db)

    identity = Identity(**{"email": mailchimp_transactional_identity_email})
    privacy_request_with_consent_policy.cache_identity(identity)

    await graph_task.run_consent_request(
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


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp_transactional
@pytest.mark.asyncio
@pytest.mark.usefixtures("reset_mailchimp_transactional_data")
async def test_mailchimp_transactional_consent_request_task_new_workflow_skipped(
    db,
    consent_policy,
    mailchimp_transactional_connection_config,
    mailchimp_transactional_dataset_config,
    mailchimp_transactional_identity_email,
    system,
    privacy_preference_history_us_ca_provide,
) -> None:
    """Test privacy notice/data use system mismatch causes the request to be skipped"""
    mailchimp_transactional_connection_config.system_id = system.id
    mailchimp_transactional_connection_config.save(db)

    privacy_request = PrivacyRequest(
        id=str(uuid4()), status=PrivacyRequestStatus.pending
    )
    privacy_request.save(db)
    privacy_preference_history_us_ca_provide.privacy_request_id = privacy_request.id
    privacy_preference_history_us_ca_provide.save(db=db)

    identity = Identity(**{"email": mailchimp_transactional_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = "mailchimp_transactional_instance"

    v = await graph_task.run_consent_request(
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


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp_transactional
@pytest.mark.asyncio
@pytest.mark.usefixtures("reset_mailchimp_transactional_data")
@mock.patch("fides.api.ops.service.connectors.saas_connector.AuthenticatedClient.send")
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
) -> None:
    """Assert logging is correctly created for privacy preferences on errored request
    Assert case when some privacy preferences were relevant but not all.
    """
    mocked_client_send.side_effect = Exception("KeyError")
    mailchimp_transactional_connection_config.system_id = system.id
    mailchimp_transactional_connection_config.save(db)

    privacy_request = PrivacyRequest(
        id=str(uuid4()), status=PrivacyRequestStatus.pending
    )
    privacy_request.save(db)
    # This preference matches on data use
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

    # This preference doesn't match on data use
    privacy_preference_history_us_ca_provide.privacy_request_id = privacy_request.id
    privacy_preference_history_us_ca_provide.save(db=db)

    identity = Identity(**{"email": mailchimp_transactional_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = "mailchimp_transactional_instance"

    with pytest.raises(Exception):
        await graph_task.run_consent_request(
            privacy_request,
            consent_policy,
            build_consent_dataset_graph([mailchimp_transactional_dataset_config]),
            [mailchimp_transactional_connection_config],
            {"email": mailchimp_transactional_identity_email},
            db,
        )

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
