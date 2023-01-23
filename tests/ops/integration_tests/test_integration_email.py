from unittest import mock

import pytest as pytest
from fideslang.models import Dataset

from fides.api.ops.graph.config import CollectionAddress
from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.datasetconfig import convert_dataset_to_graph
from fides.api.ops.models.policy import CurrentStep
from fides.api.ops.models.privacy_request import (
    CheckpointActionRequired,
    ExecutionLog,
    ExecutionLogStatus,
    ManualAction,
)
from fides.api.ops.schemas.messaging.messaging import (
    MessagingActionType,
    MessagingServiceType,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors.email_connector import (
    email_connector_erasure_send,
)
from fides.api.ops.task import graph_task
from fides.lib.models.audit_log import AuditLog, AuditLogAction


@pytest.mark.integration_postgres
@pytest.mark.integration
@mock.patch("fides.api.ops.service.connectors.email_connector.dispatch_message")
@pytest.mark.asyncio
async def test_email_connector_cache_and_delayed_send(
    mock_email_dispatch,
    db,
    erasure_policy,
    integration_postgres_config,
    email_connection_config,
    privacy_request,
    example_datasets,
    email_dataset_config,
    messaging_config,
) -> None:
    """Run an erasure privacy request with a postgres dataset and an email dataset.
    The email dataset has three separate collections.

    Call the email send and verify what would have been emailed
    """
    privacy_request.policy = erasure_policy
    rule = erasure_policy.rules[0]
    target = rule.targets[0]
    target.data_category = "user.childrens"

    cached_data_for_erasures = {
        "postgres_example_test_dataset:customer": [
            {
                "id": 1,
                "name": "John Customer",
                "email": "customer-1@example.com",
                "address_id": 1,
            }
        ],
        "postgres_example_test_dataset:report": [],
        "postgres_example_test_dataset:address": [],
        "postgres_example_test_dataset:employee": [],
        "postgres_example_test_dataset:login": [],
        "postgres_example_test_dataset:orders": [],
        "postgres_example_test_dataset:order_item": [],
        "postgres_example_test_dataset:payment_card": [],
        "postgres_example_test_dataset:product": [],
        "postgres_example_test_dataset:service_request": [],
        "postgres_example_test_dataset:visit": [],
        "email_dataset:daycare_customer": [],
        "email_dataset:children": [],
        "email_dataset:payment": [],
    }

    dataset_postgres = Dataset(**example_datasets[0])
    dataset_email = Dataset(**example_datasets[9])
    postgres_graph = convert_dataset_to_graph(
        dataset_postgres, integration_postgres_config.key
    )
    email_graph = convert_dataset_to_graph(dataset_email, email_connection_config.key)
    dataset_graph = DatasetGraph(*[postgres_graph, email_graph])

    v = await graph_task.run_erasure(
        privacy_request,
        erasure_policy,
        dataset_graph,
        [integration_postgres_config, email_connection_config],
        {"email": "customer-1@example.com"},
        cached_data_for_erasures,
        db,
    )

    assert v == {
        "email_dataset:payment": 0,
        "postgres_example_test_dataset:customer": 0,
        "postgres_example_test_dataset:report": 0,
        "postgres_example_test_dataset:employee": 0,
        "postgres_example_test_dataset:service_request": 0,
        "postgres_example_test_dataset:visit": 0,
        "postgres_example_test_dataset:orders": 0,
        "postgres_example_test_dataset:login": 0,
        "postgres_example_test_dataset:address": 0,
        "postgres_example_test_dataset:payment_card": 0,
        "email_dataset:daycare_customer": 0,
        "postgres_example_test_dataset:order_item": 0,
        "email_dataset:children": 0,
        "postgres_example_test_dataset:product": 0,
    }, "No data masked by Fidesops for the email collections"

    raw_email_template_values = (
        privacy_request.get_email_connector_template_contents_by_dataset(
            CurrentStep.erasure, "email_dataset"
        )
    )

    expected = [
        CheckpointActionRequired(
            step=CurrentStep.erasure,
            collection=CollectionAddress("email_dataset", "daycare_customer"),
            action_needed=[
                ManualAction(
                    locators={
                        "customer_id": [1]
                    },  # We have some data from postgres they can use to locate the customer_id
                    get=None,
                    update={"scholarship": "null_rewrite"},
                )
            ],
        ),
        CheckpointActionRequired(
            step=CurrentStep.erasure,
            collection=CollectionAddress("email_dataset", "payment"),
            action_needed=[
                ManualAction(
                    locators={"payer_email": ["customer-1@example.com"]},
                    get=None,
                    update=None,  # Nothing to mask on this collection
                )
            ],
        ),
        CheckpointActionRequired(
            step=CurrentStep.erasure,
            collection=CollectionAddress("email_dataset", "children"),
            action_needed=[
                ManualAction(
                    locators={
                        "parent_id": ["email_dataset:daycare_customer:id"]
                    },  # The only locator is on a separate collection on their end. We don't have data for it.
                    get=None,
                    update={
                        "birthday": "null_rewrite",
                        "first_name": "null_rewrite",
                        "last_name": "null_rewrite",
                        "report_card.grades": "null_rewrite",
                        "report_card.behavior_issues": "null_rewrite",
                        "report_card.disciplinary_action": "null_rewrite",
                        "report_card.test_scores": "null_rewrite",
                    },
                )
            ],
        ),
    ]
    for action in raw_email_template_values:
        assert (
            action in expected
        )  # "Only two collections need masking, but all are included in case they include relevant data locators."

    children_logs = db.query(ExecutionLog).filter(
        ExecutionLog.privacy_request_id == privacy_request.id,
        ExecutionLog.dataset_name == email_dataset_config.fides_key,
        ExecutionLog.collection_name == "children",
    )
    assert {"starting", "email prepared"} == {
        log.message for log in children_logs
    }, "Execution Log given unique message"
    assert {ExecutionLogStatus.in_processing, ExecutionLogStatus.complete} == {
        log.status for log in children_logs
    }

    email_connector_erasure_send(db, privacy_request)
    assert mock_email_dispatch.called
    call_args = mock_email_dispatch.call_args[1]
    assert (
        call_args["action_type"]
        == MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT
    )
    assert call_args["to_identity"] == Identity(email="test@example.com")
    assert call_args["service_type"] == MessagingServiceType.MAILGUN.value
    assert call_args["message_body_params"] == raw_email_template_values

    created_email_audit_log = (
        db.query(AuditLog)
        .filter(AuditLog.privacy_request_id == privacy_request.id)
        .all()[0]
    )
    assert (
        created_email_audit_log.message
        == "Erasure email instructions dispatched for 'email_dataset'"
    )
    assert created_email_audit_log.user_id == "system"
    assert created_email_audit_log.action == AuditLogAction.email_sent
