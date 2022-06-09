import uuid

import pytest
from pydantic import ValidationError

from fidesops.graph.config import CollectionAddress
from fidesops.graph.graph import DatasetGraph
from fidesops.models.datasetconfig import convert_dataset_to_graph
from fidesops.models.policy import PausedStep
from fidesops.models.privacy_request import (
    ExecutionLog,
    PrivacyRequest,
    StoppedCollection,
)
from fidesops.schemas.dataset import FidesopsDataset
from fidesops.task import graph_task


@pytest.mark.integration
def test_restart_graph_from_failure(
    db,
    policy,
    example_datasets,
    integration_postgres_config,
    integration_mongodb_config,
) -> None:
    """Run a failed privacy request and restart from failure"""
    dataset_postgres = FidesopsDataset(**example_datasets[0])
    graph = convert_dataset_to_graph(dataset_postgres, integration_postgres_config.key)
    dataset_mongo = FidesopsDataset(**example_datasets[1])
    mongo_graph = convert_dataset_to_graph(
        dataset_mongo, integration_mongodb_config.key
    )
    dataset_graph = DatasetGraph(*[graph, mongo_graph])

    privacy_request = PrivacyRequest(
        id=f"test_postgres_access_request_task_{uuid.uuid4()}"
    )

    # Temporarily remove the secrets from the mongo connection to prevent execution from occurring
    saved_secrets = integration_mongodb_config.secrets
    integration_mongodb_config.secrets = {}

    # Attempt to run the graph; execution will stop when we reach one of the mongo nodes
    with pytest.raises(Exception) as exc:
        graph_task.run_access_request(
            privacy_request,
            policy,
            dataset_graph,
            [integration_postgres_config, integration_mongodb_config],
            {"email": "customer-1@example.com"},
        )
    assert exc.value.__class__ == ValidationError
    assert (
        exc.value.errors()[0]["msg"]
        == "MongoDBSchema must be supplied a 'url' or all of: ['host']."
    )

    execution_logs = [
        (
            CollectionAddress(log.dataset_name, log.collection_name).value,
            log.status.value,
        )
        for log in db.query(ExecutionLog)
        .filter_by(privacy_request_id=privacy_request.id)
        .order_by("created_at")
    ]

    # Assert execution logs failed at mongo node
    assert execution_logs == [
        ("postgres_example_test_dataset:customer", "in_processing"),
        ("postgres_example_test_dataset:customer", "complete"),
        ("postgres_example_test_dataset:payment_card", "in_processing"),
        ("postgres_example_test_dataset:payment_card", "complete"),
        ("postgres_example_test_dataset:orders", "in_processing"),
        ("postgres_example_test_dataset:orders", "complete"),
        ("postgres_example_test_dataset:order_item", "in_processing"),
        ("postgres_example_test_dataset:order_item", "complete"),
        ("postgres_example_test_dataset:product", "in_processing"),
        ("postgres_example_test_dataset:product", "complete"),
        ("mongo_test:customer_details", "in_processing"),
        ("mongo_test:customer_details", "error"),
    ]
    assert privacy_request.get_failed_collection_details() == StoppedCollection(
        step=PausedStep.access,
        collection=CollectionAddress("mongo_test", "customer_details"),
    )

    # Reset secrets
    integration_mongodb_config.secrets = saved_secrets

    # Rerun access request using cached results
    graph_task.run_access_request(
        privacy_request,
        policy,
        dataset_graph,
        [integration_postgres_config, integration_mongodb_config],
        {"email": "customer-1@example.com"},
    )

    assert (
        db.query(ExecutionLog)
        .filter_by(
            privacy_request_id=privacy_request.id,
            dataset_name="postgres_example_test_dataset",
            collection_name="customer",
        )
        .count()
        == 2
    ), "Postgres customer collection does not re-run"

    assert db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id,
        dataset_name="mongo_test",
        collection_name="customer_details",
    )

    customer_detail_logs = [
        (
            CollectionAddress(log.dataset_name, log.collection_name).value,
            log.status.value,
        )
        for log in db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id,
            dataset_name="mongo_test",
            collection_name="customer_details",
        )
    ]

    assert customer_detail_logs == [
        ("mongo_test:customer_details", "in_processing"),
        ("mongo_test:customer_details", "error"),
        ("mongo_test:customer_details", "in_processing"),
        ("mongo_test:customer_details", "complete"),
    ], "Mongo customer_details node reruns"
