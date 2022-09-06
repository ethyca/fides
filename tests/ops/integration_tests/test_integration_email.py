import pytest as pytest

from fidesops.ops.graph.config import CollectionAddress
from fidesops.ops.graph.graph import DatasetGraph
from fidesops.ops.models.datasetconfig import convert_dataset_to_graph
from fidesops.ops.models.policy import CurrentStep
from fidesops.ops.models.privacy_request import CollectionActionRequired, ManualAction
from fidesops.ops.schemas.dataset import FidesopsDataset
from fidesops.ops.task import graph_task


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.asyncio
async def test_collections_with_manual_erasure_confirmation(
    db,
    erasure_policy,
    integration_postgres_config,
    email_connection_config,
    privacy_request,
    example_datasets,
) -> None:
    """Run an erasure privacy request with a postgres dataset and an email dataset.
    The email dataset has three separate collections.
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

    dataset_postgres = FidesopsDataset(**example_datasets[0])
    dataset_email = FidesopsDataset(**example_datasets[9])
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

    assert raw_email_template_values == {
        "children": CollectionActionRequired(
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
        "daycare_customer": CollectionActionRequired(
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
        "payment": CollectionActionRequired(
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
    }, "Only two collections need masking, but all are included in case they include relevant data locators."
