import uuid
from unittest import mock

import pytest
from fideslib.db.session import get_db_session
from pydantic import ValidationError
from sqlalchemy.exc import InvalidRequestError

from fidesops.ops.core.config import config
from fidesops.ops.graph.config import CollectionAddress
from fidesops.ops.graph.graph import DatasetGraph
from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.datasetconfig import convert_dataset_to_graph
from fidesops.ops.models.policy import CurrentStep
from fidesops.ops.models.privacy_request import (
    CheckpointActionRequired,
    ExecutionLog,
    PrivacyRequest,
)
from fidesops.ops.schemas.dataset import FidesopsDataset
from fidesops.ops.task import graph_task
from fidesops.ops.task.graph_task import get_cached_data_for_erasures

from ..fixtures.application_fixtures import integration_secrets
from ..service.privacy_request.request_runner_service_test import (
    get_privacy_request_results,
)


def get_sorted_execution_logs(db, privacy_request: PrivacyRequest):
    return [
        (
            CollectionAddress(log.dataset_name, log.collection_name).value,
            log.status.value,
        )
        for log in db.query(ExecutionLog)
        .filter_by(privacy_request_id=privacy_request.id)
        .order_by("created_at")
    ]


@pytest.fixture(scope="function")
def mongo_postgres_dataset_graph(
    example_datasets, integration_postgres_config, integration_mongodb_config
):
    dataset_postgres = FidesopsDataset(**example_datasets[0])
    graph = convert_dataset_to_graph(dataset_postgres, integration_postgres_config.key)
    dataset_mongo = FidesopsDataset(**example_datasets[1])
    mongo_graph = convert_dataset_to_graph(
        dataset_mongo, integration_mongodb_config.key
    )
    dataset_graph = DatasetGraph(*[graph, mongo_graph])
    return dataset_graph


@pytest.mark.integration
class TestDeleteCollection:
    @pytest.mark.usefixtures(
        "postgres_integration_db", "postgres_example_test_dataset_config_read_access"
    )
    def test_delete_collection_before_new_request(
        self,
        db,
        policy,
        read_connection_config,
        run_privacy_request_task,
    ) -> None:
        """Delete the connection config before execution starts which also
        deletes its dataset config. The graph is built with nothing in it, and no results are returned.
        """
        customer_email = "customer-1@example.com"
        data = {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": policy.key,
            "identity": {"email": customer_email},
        }

        pr = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            data,
        )
        assert pr.get_results() != {}

        read_connection_config.delete(db)
        pr = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            data,
        )
        assert pr.get_results() == {}

    @mock.patch("fidesops.ops.task.graph_task.GraphTask.log_start")
    @pytest.mark.asyncio
    async def test_delete_collection_while_in_progress(
        self,
        mocked_log_start,
        db,
        policy,
        integration_postgres_config,
        example_datasets,
    ) -> None:
        """Assert that deleting a collection while the privacy request is in progress doesn't affect the current execution plan.
        We still proceed to visit the deleted collections, because we rely on the ConnectionConfigs already in memory.
        """
        # Create a new ConnectionConfig instead of using the fixture because I need to be able to access this
        # outside of the current session.
        mongo_connection_config = ConnectionConfig(
            key="mongo_example_in_progress",
            connection_type=ConnectionType.mongodb,
            access=AccessLevel.write,
            secrets=integration_secrets["mongo_example"],
            name="mongo_example_in_progress",
        )
        mongo_connection_config.save(db)
        dataset_postgres = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(
            dataset_postgres, integration_postgres_config.key
        )
        dataset_mongo = FidesopsDataset(**example_datasets[1])
        mongo_graph = convert_dataset_to_graph(
            dataset_mongo, mongo_connection_config.key
        )
        dataset_graph = DatasetGraph(*[graph, mongo_graph])

        def delete_connection_config(_):
            """
            Delete the mongo connection in a separate session, for testing purposes, while the privacy request
            is in progress. Arbitrarily hooks into the log_start method to do this.
            """
            SessionLocal = get_db_session(config)
            new_session = SessionLocal()
            try:
                reloaded_config = new_session.query(ConnectionConfig).get(
                    mongo_connection_config.id
                )

                reloaded_config.delete(db)
            except InvalidRequestError:
                pass
            new_session.close()

        mocked_log_start.side_effect = delete_connection_config
        privacy_request = PrivacyRequest(
            id=f"test_postgres_access_request_task_{uuid.uuid4()}"
        )

        results = await graph_task.run_access_request(
            privacy_request,
            policy,
            dataset_graph,
            [integration_postgres_config, mongo_connection_config],
            {"email": "customer-1@example.com"},
            db,
        )
        assert any(
            collection.startswith("mongo_test") for collection in results
        ), "mongo results still returned"
        assert any(
            collection.startswith("postgres_example_test_dataset")
            for collection in results
        ), "postgres results returned"

        postgres_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id,
            dataset_name="postgres_example_test_dataset",
        )
        assert postgres_logs.count() == 11
        assert postgres_logs.filter_by(status="complete").count() == 11

        mongo_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id, dataset_name="mongo_test"
        )
        assert mongo_logs.count() == 9
        assert (
            mongo_logs.filter_by(status="complete").count() == 9
        ), "Mongo collections still visited"

        db.delete(mongo_connection_config)

    @pytest.mark.asyncio
    async def test_collection_omitted_on_restart_from_failure(
        self,
        db,
        policy,
        integration_postgres_config,
        integration_mongodb_config,
        mongo_postgres_dataset_graph,
        example_datasets,
        run_privacy_request_task,
    ) -> None:
        """Remove secrets to make privacy request fail, then delete the connection config. Build a graph
        that does not contain the deleted dataset config and re-run."""

        integration_mongodb_config.secrets = {}
        integration_mongodb_config.save(db)

        privacy_request = PrivacyRequest(
            id=f"test_postgres_access_request_task_{uuid.uuid4()}"
        )

        with pytest.raises(ValidationError):
            await graph_task.run_access_request(
                privacy_request,
                policy,
                mongo_postgres_dataset_graph,
                [integration_postgres_config, integration_mongodb_config],
                {"email": "customer-1@example.com"},
                db,
            )

        execution_logs = get_sorted_execution_logs(db, privacy_request)
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
        ], "Execution failed at first mongo collection"

        integration_mongodb_config.delete(db)

        # Just rebuilding a graph without the deleted config.
        dataset_postgres = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(
            dataset_postgres, integration_postgres_config.key
        )
        postgres_only_dataset_graph = DatasetGraph(*[graph])

        results = await graph_task.run_access_request(
            privacy_request,
            policy,
            postgres_only_dataset_graph,
            [integration_postgres_config],
            {"email": "customer-1@example.com"},
            db,
        )

        execution_logs = get_sorted_execution_logs(db, privacy_request)
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
            ("postgres_example_test_dataset:employee", "in_processing"),
            ("postgres_example_test_dataset:employee", "complete"),
            ("postgres_example_test_dataset:service_request", "in_processing"),
            ("postgres_example_test_dataset:service_request", "complete"),
            ("postgres_example_test_dataset:report", "in_processing"),
            ("postgres_example_test_dataset:report", "complete"),
            ("postgres_example_test_dataset:visit", "in_processing"),
            ("postgres_example_test_dataset:visit", "complete"),
            ("postgres_example_test_dataset:address", "in_processing"),
            ("postgres_example_test_dataset:address", "complete"),
            ("postgres_example_test_dataset:login", "in_processing"),
            ("postgres_example_test_dataset:login", "complete"),
        ], "No mongo collections run"

        assert all(
            [dataset.startswith("postgres_example") for dataset in results]
        ), "No mongo results"

    @pytest.mark.usefixtures(
        "postgres_integration_db", "postgres_example_test_dataset_config_read_access"
    )
    def test_delete_connection_config_on_completed_request(
        self,
        db,
        policy,
        read_connection_config,
        run_privacy_request_task,
    ) -> None:
        """Delete the connection config on a completed request leaves execution logs untouched"""
        customer_email = "customer-1@example.com"
        data = {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": policy.key,
            "identity": {"email": customer_email},
        }

        pr = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            data,
        )
        assert pr.get_results() != {}
        logs = get_sorted_execution_logs(db, pr)
        assert len(logs) == 22

        read_connection_config.delete(db)
        logs = get_sorted_execution_logs(db, pr)
        assert len(logs) == 22


@pytest.mark.integration
class TestSkipDisabledCollection:
    @pytest.mark.asyncio
    async def test_skip_collection_new_request(
        self,
        db,
        policy,
        integration_postgres_config,
        integration_mongodb_config,
        mongo_postgres_dataset_graph,
    ) -> None:
        """Mark Mongo ConnectionConfig as disabled, run access request,
        and then assert that all mongo collections are skipped"""

        integration_mongodb_config.disabled = True
        integration_mongodb_config.save(db)

        privacy_request = PrivacyRequest(
            id=f"test_postgres_access_request_task_{uuid.uuid4()}"
        )

        results = await graph_task.run_access_request(
            privacy_request,
            policy,
            mongo_postgres_dataset_graph,
            [integration_postgres_config, integration_mongodb_config],
            {"email": "customer-1@example.com"},
            db,
        )
        assert all(
            [dataset.startswith("postgres_example") for dataset in results]
        ), "No mongo results"

        postgres_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id,
            dataset_name="postgres_example_test_dataset",
        )
        assert postgres_logs.count() == 22
        assert postgres_logs.filter_by(status="in_processing").count() == 11
        assert postgres_logs.filter_by(status="complete").count() == 11

        mongo_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id, dataset_name="mongo_test"
        )
        assert mongo_logs.count() == 9
        assert mongo_logs.filter_by(status="skipped").count() == 9

    @mock.patch("fidesops.ops.task.graph_task.GraphTask.log_start")
    @pytest.mark.asyncio
    async def test_run_disabled_collections_in_progress(
        self,
        mocked_log_start,
        db,
        policy,
        integration_postgres_config,
        example_datasets,
    ) -> None:
        """Assert that disabling a collection while the privacy request is in progress can affect the current execution plan.
        ConnectionConfigs that are disabled while a request is in progress will be skipped after the current session is committed.
        """
        # Create a new ConnectionConfig instead of using the fixture because I need to be able to access this
        # outside of the current session.
        mongo_connection_config = ConnectionConfig(
            key="mongo_example_in_progress",
            connection_type=ConnectionType.mongodb,
            access=AccessLevel.write,
            secrets=integration_secrets["mongo_example"],
            name="mongo_example_in_progress",
        )
        mongo_connection_config.save(db)

        dataset_postgres = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(
            dataset_postgres, integration_postgres_config.key
        )
        dataset_mongo = FidesopsDataset(**example_datasets[1])
        mongo_graph = convert_dataset_to_graph(
            dataset_mongo, mongo_connection_config.key
        )
        dataset_graph = DatasetGraph(*[graph, mongo_graph])

        def disable_connection_config(_):
            """
            Disable the mongo connection in a separate session.

            For testing purposes, this just hooks into the log_start method (there's nothing special about using
            the log_start method to do this, other than it doesn't disrupt the actual traversal). Instead of creating an
            in_processing log, I'm hooking in here to disable the mongo ConnectionConfig
            in a new session, to mimic the ConnectionConfig being disabled by a separate request while request
            is in progress.
            """
            SessionLocal = get_db_session(config)
            new_session = SessionLocal()
            reloaded_config = new_session.query(ConnectionConfig).get(
                mongo_connection_config.id
            )
            reloaded_config.disabled = True
            reloaded_config.save(new_session)
            new_session.close()

        mocked_log_start.side_effect = disable_connection_config

        privacy_request = PrivacyRequest(
            id=f"test_postgres_access_request_task_{uuid.uuid4()}"
        )

        results = await graph_task.run_access_request(
            privacy_request,
            policy,
            dataset_graph,
            [integration_postgres_config, mongo_connection_config],
            {"email": "customer-1@example.com"},
            db,
        )
        assert not any(
            collection.startswith("mongo_test") for collection in results
        ), "mongo results not returned"
        assert any(
            collection.startswith("postgres_example_test_dataset")
            for collection in results
        )

        postgres_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id,
            dataset_name="postgres_example_test_dataset",
        )
        assert postgres_logs.count() == 11
        assert postgres_logs.filter_by(status="complete").count() == 11

        mongo_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id, dataset_name="mongo_test"
        )
        assert mongo_logs.count() == 9
        assert (
            mongo_logs.filter_by(status="skipped").count() == 9
        ), "All mongo collections skipped"

        db.delete(mongo_connection_config)

    @pytest.mark.asyncio
    async def test_skip_collection_on_restart(
        self,
        db,
        policy,
        integration_postgres_config,
        integration_mongodb_config,
        mongo_postgres_dataset_graph,
    ) -> None:
        """Remove secrets to make privacy request fail, then disable connection config
        and confirm that datastores are skipped on re-run"""

        integration_mongodb_config.secrets = {}
        integration_mongodb_config.save(db)

        privacy_request = PrivacyRequest(
            id=f"test_postgres_access_request_task_{uuid.uuid4()}"
        )

        with pytest.raises(ValidationError):
            await graph_task.run_access_request(
                privacy_request,
                policy,
                mongo_postgres_dataset_graph,
                [integration_postgres_config, integration_mongodb_config],
                {"email": "customer-1@example.com"},
                db,
            )

        execution_logs = get_sorted_execution_logs(db, privacy_request)
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
        ], "Execution failed at first mongo collection"

        integration_mongodb_config.disabled = True
        integration_mongodb_config.save(db)

        results = await graph_task.run_access_request(
            privacy_request,
            policy,
            mongo_postgres_dataset_graph,
            [integration_postgres_config, integration_mongodb_config],
            {"email": "customer-1@example.com"},
            db,
        )

        execution_logs = get_sorted_execution_logs(db, privacy_request)
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
            ("postgres_example_test_dataset:employee", "in_processing"),
            ("postgres_example_test_dataset:employee", "complete"),
            ("postgres_example_test_dataset:service_request", "in_processing"),
            ("postgres_example_test_dataset:service_request", "complete"),
            ("mongo_test:customer_feedback", "skipped"),
            ("mongo_test:internal_customer_profile", "skipped"),
            ("mongo_test:rewards", "skipped"),
            ("postgres_example_test_dataset:report", "in_processing"),
            ("postgres_example_test_dataset:report", "complete"),
            ("postgres_example_test_dataset:visit", "in_processing"),
            ("postgres_example_test_dataset:visit", "complete"),
            ("postgres_example_test_dataset:address", "in_processing"),
            ("postgres_example_test_dataset:address", "complete"),
            ("mongo_test:customer_details", "skipped"),
            ("mongo_test:flights", "skipped"),
            ("mongo_test:employee", "skipped"),
            ("mongo_test:aircraft", "skipped"),
            ("mongo_test:conversations", "skipped"),
            ("mongo_test:payment_card", "skipped"),
            ("postgres_example_test_dataset:login", "in_processing"),
            ("postgres_example_test_dataset:login", "complete"),
        ], "Rerun skips disabled collections"

        assert all(
            [dataset.startswith("postgres_example") for dataset in results]
        ), "No mongo results"

    @pytest.mark.usefixtures(
        "postgres_integration_db", "postgres_example_test_dataset_config_read_access"
    )
    def test_disable_connection_config_on_completed_request(
        self,
        db,
        policy,
        read_connection_config,
        run_privacy_request_task,
    ) -> None:
        """Disabling the connection config on a completed request leaves execution logs untouched"""
        customer_email = "customer-1@example.com"
        data = {
            "requested_at": "2021-08-30T16:09:37.359Z",
            "policy_key": policy.key,
            "identity": {"email": customer_email},
        }

        pr = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            data,
        )
        assert pr.get_results() != {}
        logs = get_sorted_execution_logs(db, pr)
        assert len(logs) == 22

        read_connection_config.disabled = True
        read_connection_config.save(db)
        logs = get_sorted_execution_logs(db, pr)
        assert len(logs) == 22


@pytest.mark.integration
@pytest.mark.asyncio
async def test_restart_graph_from_failure(
    db,
    policy,
    example_datasets,
    integration_postgres_config,
    integration_mongodb_config,
    mongo_postgres_dataset_graph,
) -> None:
    """Run a failed privacy request and restart from failure"""

    privacy_request = PrivacyRequest(
        id=f"test_postgres_access_request_task_{uuid.uuid4()}"
    )

    # Temporarily remove the secrets from the mongo connection to prevent execution from occurring
    saved_secrets = integration_mongodb_config.secrets
    integration_mongodb_config.secrets = {}
    integration_mongodb_config.save(db)

    # Attempt to run the graph; execution will stop when we reach one of the mongo nodes
    with pytest.raises(Exception) as exc:
        await graph_task.run_access_request(
            privacy_request,
            policy,
            mongo_postgres_dataset_graph,
            [integration_postgres_config, integration_mongodb_config],
            {"email": "customer-1@example.com"},
            db,
        )
    assert exc.value.__class__ == ValidationError
    assert (
        exc.value.errors()[0]["msg"]
        == "MongoDBSchema must be supplied a 'url' or all of: ['host']."
    )

    execution_logs = get_sorted_execution_logs(db, privacy_request)
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
    assert privacy_request.get_failed_checkpoint_details() == CheckpointActionRequired(
        step=CurrentStep.access,
        collection=CollectionAddress("mongo_test", "customer_details"),
    )

    # Reset secrets
    integration_mongodb_config.secrets = saved_secrets
    integration_mongodb_config.save(db)

    # Rerun access request using cached results
    with mock.patch(
        "fidesops.ops.task.graph_task.fideslog_graph_rerun"
    ) as mock_log_event:
        await graph_task.run_access_request(
            privacy_request,
            policy,
            mongo_postgres_dataset_graph,
            [integration_postgres_config, integration_mongodb_config],
            {"email": "customer-1@example.com"},
            db,
        )

        # Assert analytics event created - before and after graph on rerun did not change
        analytics_event = mock_log_event.call_args.args[0]
        assert analytics_event.docker is True
        assert analytics_event.event == "rerun_access_graph"
        assert analytics_event.event_created_at is not None
        assert analytics_event.extra_data == {
            "prev_collection_count": 20,
            "curr_collection_count": 20,
            "added_collection_count": 0,
            "removed_collection_count": 0,
            "added_edge_count": 0,
            "removed_edge_count": 0,
            "already_processed_access_collection_count": 5,
            "already_processed_erasure_collection_count": 0,
            "skipped_added_edge_count": 0,
            "privacy_request": privacy_request.id,
        }

        assert analytics_event.error is None
        assert analytics_event.status_code is None
        assert analytics_event.endpoint is None
        assert analytics_event.local_host is None

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
        for log in db.query(ExecutionLog)
        .filter_by(
            privacy_request_id=privacy_request.id,
            dataset_name="mongo_test",
            collection_name="customer_details",
        )
        .order_by("created_at")
    ]

    assert customer_detail_logs == [
        ("mongo_test:customer_details", "in_processing"),
        ("mongo_test:customer_details", "error"),
        ("mongo_test:customer_details", "in_processing"),
        ("mongo_test:customer_details", "complete"),
    ], "Mongo customer_details node reruns"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_restart_graph_from_failure_during_erasure(
    db,
    policy,
    example_datasets,
    integration_postgres_config,
    integration_mongodb_config,
    mongo_postgres_dataset_graph,
) -> None:
    """Run a failed privacy request and restart from failure during the erasure portion.

    An erasure request first runs an access and then an erasure request.
    If the erasure portion fails, and we reprocess, we don't re-run the access portion currently.
    """

    privacy_request = PrivacyRequest(
        id=f"test_postgres_access_request_task_{uuid.uuid4()}"
    )

    # Run access portion like normal
    await graph_task.run_access_request(
        privacy_request,
        policy,
        mongo_postgres_dataset_graph,
        [integration_postgres_config, integration_mongodb_config],
        {"email": "customer-1@example.com"},
        db,
    )

    # Temporarily remove the secrets from the postgres connection to prevent execution from occurring
    saved_secrets = integration_postgres_config.secrets
    integration_postgres_config.secrets = {}
    integration_postgres_config.save(db)

    # Attempt to run the erasure graph; execution will stop when we reach one of the mongo nodes
    with pytest.raises(Exception) as exc:
        await graph_task.run_erasure(
            privacy_request,
            policy,
            mongo_postgres_dataset_graph,
            [integration_postgres_config, integration_mongodb_config],
            {"email": "customer-1@example.com"},
            get_cached_data_for_erasures(privacy_request.id),
            db,
        )
        assert exc.value.__class__ == ValidationError
        assert (
            exc.value.errors()[0]["msg"]
            == "PostgreSQLSchema must be supplied a 'url' or all of: ['host']."
        )

    # Reset secrets
    integration_postgres_config.secrets = saved_secrets
    integration_postgres_config.save(db)

    # Rerun erasure portion of request using cached results
    with mock.patch(
        "fidesops.ops.task.graph_task.fideslog_graph_rerun"
    ) as mock_log_event:
        await graph_task.run_erasure(
            privacy_request,
            policy,
            mongo_postgres_dataset_graph,
            [integration_postgres_config, integration_mongodb_config],
            {"email": "customer-1@example.com"},
            get_cached_data_for_erasures(privacy_request.id),
            db,
        )

        # Assert analytics event created - before and after graph on rerun did not change
        analytics_event = mock_log_event.call_args.args[0]
        assert analytics_event.docker is True
        assert analytics_event.event == "rerun_erasure_graph"
        assert analytics_event.event_created_at is not None
        assert analytics_event.extra_data == {
            "prev_collection_count": 20,
            "curr_collection_count": 20,
            "added_collection_count": 0,
            "removed_collection_count": 0,
            "added_edge_count": 0,
            "removed_edge_count": 0,
            "already_processed_access_collection_count": 20,
            "already_processed_erasure_collection_count": 9,
            "skipped_added_edge_count": 0,
            "privacy_request": privacy_request.id,
        }

        assert analytics_event.error is None
        assert analytics_event.status_code is None
        assert analytics_event.endpoint is None
        assert analytics_event.local_host is None

    assert (
        db.query(ExecutionLog)
        .filter_by(
            privacy_request_id=privacy_request.id,
            dataset_name="mongo_test",
            collection_name="customer_details",
        )
        .count()
        == 4
    ), "Mongo customer_details collection has two access and two erasures"

    address_logs = [
        (
            CollectionAddress(log.dataset_name, log.collection_name).value,
            log.action_type.value,
            log.status.value,
        )
        for log in db.query(ExecutionLog)
        .filter_by(privacy_request_id=privacy_request.id, collection_name="address")
        .order_by("created_at")
    ]

    assert address_logs == [
        ("postgres_example_test_dataset:address", "access", "in_processing"),
        ("postgres_example_test_dataset:address", "access", "complete"),
        ("postgres_example_test_dataset:address", "erasure", "in_processing"),
        ("postgres_example_test_dataset:address", "erasure", "error"),
        ("postgres_example_test_dataset:address", "erasure", "in_processing"),
        ("postgres_example_test_dataset:address", "erasure", "complete"),
    ], "Postgres address collection reruns on erasure portion"
