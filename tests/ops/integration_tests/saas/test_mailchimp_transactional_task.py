import json
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
from fides.api.ops.schemas.saas.saas_config import SaaSRequest
from fides.api.ops.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.ops.service.connectors import SaaSConnector, get_connector
from fides.api.ops.service.privacy_request.request_runner_service import (
    build_consent_dataset_graph,
)
from fides.api.ops.task import graph_task


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
) -> None:
    """Full consent request based on the Mailchimp Transactional (Mandrill) SaaS config
    with new workflow where preferences are saved w.r.t privacy notices"""

    privacy_request = PrivacyRequest(
        id=str(uuid4()), status=PrivacyRequestStatus.pending
    )
    privacy_request.save(db)
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

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
async def test_mailchimp_transactional_consent_prepared_requests_new_workflow(
    mocked_client_send,
    db,
    consent_policy,
    mailchimp_transactional_connection_config,
    mailchimp_transactional_dataset_config,
    mailchimp_transactional_identity_email,
    privacy_preference_history,
) -> None:
    """Assert attributes of the PreparedRequest created by the client for running the consent request"""
    privacy_request = PrivacyRequest(
        id=str(uuid4()), status=PrivacyRequestStatus.pending
    )
    privacy_request.save(db)
    privacy_preference_history.privacy_request_id = privacy_request.id
    privacy_preference_history.save(db=db)

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
