from datetime import datetime
from typing import Optional
from unittest import mock

import pytest
from fideslang.models import CollectionMeta, Dataset
from pydantic import ValidationError
from sqlalchemy.exc import InvalidRequestError

from fides.api import common_exceptions
from fides.api.db.session import get_db_session
from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import convert_dataset_to_graph
from fides.api.models.privacy_request import ExecutionLog, PrivacyRequest
from fides.api.schemas.policy import CurrentStep
from fides.api.schemas.privacy_request import CheckpointActionRequired
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import CONFIG
from tests.fixtures.application_fixtures import integration_secrets

from ...conftest import access_runner_tester, erasure_runner_tester
from ..service.privacy_request.test_request_runner_service import (
    get_privacy_request_results,
)


def get_collection_identifier(log) -> str:
    """
    Get a standardized identifier for a collection from an execution log.
    """

    # This is necessary because the log for a complete "Dataset traversal" does not have a collection.
    # The better approach in the long-term is to support more general execution data in the execution logs.
    if log.collection_name:
        return CollectionAddress(log.dataset_name, log.collection_name or "").value
    return log.dataset_name


def get_sorted_execution_logs(db, privacy_request: PrivacyRequest):
    return [
        (
            get_collection_identifier(log),
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
    dataset_postgres = Dataset(**example_datasets[0])

    graph = convert_dataset_to_graph(dataset_postgres, integration_postgres_config.key)
    dataset_mongo = Dataset(**example_datasets[1])
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

        customer_email = "customer-4@example.com"
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
        assert pr.get_raw_access_results() != {}

        read_connection_config.delete(db)
        pr = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            data,
        )
        assert pr.get_raw_access_results() == {}

    @mock.patch("fides.api.task.graph_task.GraphTask.log_start")
    @pytest.mark.asyncio
    async def test_delete_collection_while_in_progress(
        self,
        mocked_log_start,
        db,
        policy,
        integration_postgres_config,
        example_datasets,
        privacy_request,
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
        dataset_postgres = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(
            dataset_postgres, integration_postgres_config.key
        )
        dataset_mongo = Dataset(**example_datasets[1])
        mongo_graph = convert_dataset_to_graph(
            dataset_mongo, mongo_connection_config.key
        )
        dataset_graph = DatasetGraph(*[graph, mongo_graph])

        def delete_connection_config(_):
            """
            Delete the mongo connection in a separate session, for testing purposes, while the privacy request
            is in progress. Arbitrarily hooks into the log_start method to do this.
            """
            SessionLocal = get_db_session(CONFIG)
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

        results = access_runner_tester(
            privacy_request,
            policy,
            dataset_graph,
            [integration_postgres_config, mongo_connection_config],
            {"email": "customer-4@example.com"},
            db,
        )
        assert any(collection.startswith("mongo_test") for collection in results), (
            "mongo results still returned"
        )
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
        assert mongo_logs.filter_by(status="complete").count() == 9, (
            "Mongo collections still visited"
        )

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
        privacy_request,
    ) -> None:
        """Remove secrets to make privacy request fail, then delete the connection config. Build a graph
        that does not contain the deleted dataset config and re-run."""

        integration_mongodb_config.secrets = {}
        integration_mongodb_config.save(db)

        access_runner_tester(
            privacy_request,
            policy,
            mongo_postgres_dataset_graph,
            [integration_postgres_config, integration_mongodb_config],
            {"email": "customer-4@example.com"},
            db,
        )
        customer_detail_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id,
            dataset_name="mongo_test",
            collection_name="customer_details",
        )
        assert ["in_processing", "error"] == [
            log.status.value
            for log in customer_detail_logs.order_by(ExecutionLog.created_at)
        ]
        customer_feedback_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id,
            dataset_name="mongo_test",
            collection_name="customer_feedback",
        )
        assert ["in_processing", "error"] == [
            log.status.value
            for log in customer_feedback_logs.order_by(ExecutionLog.created_at)
        ]

        # Just rebuilding a graph without the deleted config.
        dataset_postgres = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(
            dataset_postgres, integration_postgres_config.key
        )
        postgres_only_dataset_graph = DatasetGraph(*[graph])

        results = access_runner_tester(
            privacy_request,
            policy,
            postgres_only_dataset_graph,
            [integration_postgres_config],
            {"email": "customer-4@example.com"},
            db,
        )

        customer_detail_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id,
            dataset_name="mongo_test",
            collection_name="customer_details",
        )
        assert ["in_processing", "error", "in_processing", "error"] == [
            log.status.value
            for log in customer_detail_logs.order_by(ExecutionLog.created_at)
        ]
        customer_feedback_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id,
            dataset_name="mongo_test",
            collection_name="customer_feedback",
        )
        assert ["in_processing", "error", "in_processing", "error"] == [
            log.status.value
            for log in customer_feedback_logs.order_by(ExecutionLog.created_at)
        ]

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

        customer_email = "customer-4@example.com"
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

        expected_log_count = 26

        assert pr.get_raw_access_results() != {}
        logs = get_sorted_execution_logs(db, pr)
        assert len(logs) == expected_log_count

        read_connection_config.delete(db)
        logs = get_sorted_execution_logs(db, pr)
        assert len(logs) == expected_log_count


@pytest.mark.integration
class TestSkipCollectionDueToDisabledConnectionConfig:
    @pytest.mark.asyncio
    async def test_skip_collection_new_request(
        self,
        db,
        policy,
        integration_postgres_config,
        integration_mongodb_config,
        mongo_postgres_dataset_graph,
        privacy_request,
    ) -> None:
        """Mark Mongo ConnectionConfig as disabled, run access request,
        and then assert that all mongo collections are skipped"""

        integration_mongodb_config.disabled = True
        integration_mongodb_config.save(db)

        results = access_runner_tester(
            privacy_request,
            policy,
            mongo_postgres_dataset_graph,
            [integration_postgres_config, integration_mongodb_config],
            {"email": "customer-4@example.com"},
            db,
        )
        assert all([dataset.startswith("postgres_example") for dataset in results]), (
            "No mongo results"
        )

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

    @mock.patch("fides.api.task.graph_task.GraphTask.log_start")
    @pytest.mark.asyncio
    async def test_run_disabled_collections_in_progress(
        self,
        mocked_log_start,
        db,
        policy,
        privacy_request,
        integration_postgres_config,
        example_datasets,
    ) -> None:
        """Assert that disabling a collection while the privacy request is in progress can affect the current execution plan.
        ConnectionConfigs that are disabled while a request is in progress will be skipped after the current session is committed.

        This test was written for DSR 2.0 and is flaky for DSR 3.0 - only running on DSR 2.0 here.
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

        dataset_postgres = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(
            dataset_postgres, integration_postgres_config.key
        )
        dataset_mongo = Dataset(**example_datasets[1])
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
            SessionLocal = get_db_session(CONFIG)
            new_session = SessionLocal()
            reloaded_config = new_session.query(ConnectionConfig).get(
                mongo_connection_config.id
            )
            reloaded_config.disabled = True
            reloaded_config.save(new_session)
            new_session.close()

        mocked_log_start.side_effect = disable_connection_config

        results = access_runner_tester(
            privacy_request,
            policy,
            dataset_graph,
            [integration_postgres_config, mongo_connection_config],
            {"email": "customer-4@example.com"},
            db,
        )
        assert not any(collection.startswith("mongo_test") for collection in results), (
            "mongo results not returned"
        )
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
        assert mongo_logs.filter_by(status="skipped").count() == 9, (
            "All mongo collections skipped"
        )

        db.delete(mongo_connection_config)

    @pytest.mark.asyncio
    async def test_skip_collection_on_restart(
        self,
        db,
        policy,
        integration_postgres_config,
        integration_mongodb_config,
        mongo_postgres_dataset_graph,
        privacy_request,
    ) -> None:
        """Remove secrets to make privacy request fail, then disable connection config
        and confirm that datastores are skipped on re-run"""

        integration_mongodb_config.secrets = {}
        integration_mongodb_config.save(db)

        access_runner_tester(
            privacy_request,
            policy,
            mongo_postgres_dataset_graph,
            [integration_postgres_config, integration_mongodb_config],
            {"email": "customer-4@example.com"},
            db,
        )

        customer_detail_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id,
            dataset_name="mongo_test",
            collection_name="customer_details",
        )
        assert ["in_processing", "error"] == [
            log.status.value
            for log in customer_detail_logs.order_by(ExecutionLog.created_at)
        ]
        customer_feedback_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id,
            dataset_name="mongo_test",
            collection_name="customer_feedback",
        )
        assert ["in_processing", "error"] == [
            log.status.value
            for log in customer_feedback_logs.order_by(ExecutionLog.created_at)
        ]

        integration_mongodb_config.disabled = True
        integration_mongodb_config.save(db)

        results = access_runner_tester(
            privacy_request,
            policy,
            mongo_postgres_dataset_graph,
            [integration_postgres_config, integration_mongodb_config],
            {"email": "customer-4@example.com"},
            db,
        )

        customer_detail_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id,
            dataset_name="mongo_test",
            collection_name="customer_details",
        )
        assert ["in_processing", "error", "skipped"] == [
            log.status.value
            for log in customer_detail_logs.order_by(ExecutionLog.created_at)
        ]
        customer_feedback_logs = db.query(ExecutionLog).filter_by(
            privacy_request_id=privacy_request.id,
            dataset_name="mongo_test",
            collection_name="customer_feedback",
        )
        assert ["in_processing", "error", "skipped"] == [
            log.status.value
            for log in customer_feedback_logs.order_by(ExecutionLog.created_at)
        ]

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

        customer_email = "customer-4@example.com"
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

        expected_log_count = 26

        assert pr.get_raw_access_results() != {}
        logs = get_sorted_execution_logs(db, pr)
        assert len(logs) == expected_log_count

        read_connection_config.disabled = True
        read_connection_config.save(db)
        logs = get_sorted_execution_logs(db, pr)
        assert len(logs) == expected_log_count


@pytest.mark.integration
class TestSkipMarkedCollections:
    def _build_postgres_dataset_graph_with_skipped_collection(
        self,
        example_datasets,
        integration_config,
        skipped_collection_name: Optional[str],
    ):
        """test helper"""

        dataset_postgres = Dataset(**example_datasets[0])
        if skipped_collection_name:
            skipped_collection = next(
                col
                for col in dataset_postgres.collections
                if col.name == skipped_collection_name
            )
            skipped_collection.fides_meta = CollectionMeta
            skipped_collection.fides_meta.skip_processing = True

        graph = convert_dataset_to_graph(dataset_postgres, integration_config.key)
        dataset_graph = DatasetGraph(*[graph])
        return dataset_graph

    @pytest.mark.asyncio
    async def test_no_collections_marked_as_skipped(
        self,
        db,
        policy,
        example_datasets,
        integration_postgres_config,
        privacy_request,
    ) -> None:
        """Sanity check - nothing marked as skipped. All collections expected in results."""

        postgres_graph = self._build_postgres_dataset_graph_with_skipped_collection(
            example_datasets, integration_postgres_config, skipped_collection_name=None
        )

        results = access_runner_tester(
            privacy_request,
            policy,
            postgres_graph,
            [integration_postgres_config],
            {"email": "customer-4@example.com"},
            db,
        )

        assert len(results) == len(example_datasets[0]["collections"])
        assert "login" not in results

    @pytest.mark.asyncio
    async def test_collection_marked_as_skipped_with_nothing_downstream(
        self,
        db,
        policy,
        example_datasets,
        privacy_request,
        integration_postgres_config,
    ) -> None:
        """Mark the login collection as skipped.  This collection has no downstream dependencies, so skipping is fine!"""

        postgres_graph = self._build_postgres_dataset_graph_with_skipped_collection(
            example_datasets,
            integration_postgres_config,
            skipped_collection_name="login",
        )

        results = access_runner_tester(
            privacy_request,
            policy,
            postgres_graph,
            [integration_postgres_config],
            {"email": "customer-4@example.com"},
            db,
        )

        assert len(results) == len(example_datasets[0]["collections"]) - 1
        assert "login" not in results

    @pytest.mark.asyncio
    async def test_collection_marked_as_skipped_with_dependencies(
        self,
        db,
        policy,
        privacy_request,
        example_datasets,
        integration_postgres_config,
    ) -> None:
        """Mark the address collection as skipped.  Many collections are marked as relying on this collection so this fails
        early when building the DatasetGraph"""

        with pytest.raises(common_exceptions.ValidationError):
            postgres_graph = self._build_postgres_dataset_graph_with_skipped_collection(
                example_datasets,
                integration_postgres_config,
                skipped_collection_name="address",
            )

            access_runner_tester(
                privacy_request,
                policy,
                postgres_graph,
                [integration_postgres_config],
                {"email": "customer-4@example.com"},
                db,
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_restart_graph_from_failure(
    db,
    policy,
    example_datasets,
    integration_postgres_config,
    integration_mongodb_config,
    mongo_postgres_dataset_graph,
    privacy_request,
) -> None:
    """Run a failed privacy request and restart from failure"""

    # Temporarily remove the secrets from the mongo connection to prevent execution from occurring
    saved_secrets = integration_mongodb_config.secrets
    integration_mongodb_config.secrets = {}
    integration_mongodb_config.save(db)

    access_runner_tester(
        privacy_request,
        policy,
        mongo_postgres_dataset_graph,
        [integration_postgres_config, integration_mongodb_config],
        {"email": "customer-4@example.com"},
        db,
    )
    customer_detail_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id,
        dataset_name="mongo_test",
        collection_name="customer_details",
    )
    assert ["in_processing", "error"] == [
        log.status.value
        for log in customer_detail_logs.order_by(ExecutionLog.created_at)
    ]
    customer_feedback_logs = db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id,
        dataset_name="mongo_test",
        collection_name="customer_feedback",
    )
    assert ["in_processing", "error"] == [
        log.status.value
        for log in customer_feedback_logs.order_by(ExecutionLog.created_at)
    ]

    assert privacy_request.get_failed_checkpoint_details() == CheckpointActionRequired(
        step=CurrentStep.access,
    )

    # Reset secrets
    integration_mongodb_config.secrets = saved_secrets
    integration_mongodb_config.save(db)

    access_runner_tester(
        privacy_request,
        policy,
        mongo_postgres_dataset_graph,
        [integration_postgres_config, integration_mongodb_config],
        {"email": "customer-4@example.com"},
        db,
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
            get_collection_identifier(log),
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
async def test_restart_graph_from_failure_on_different_scheduler(
    db,
    policy,
    example_datasets,
    integration_postgres_config,
    integration_mongodb_config,
    mongo_postgres_dataset_graph,
    privacy_request,
) -> None:
    """Run a failed privacy request and restart from failure."""

    # Temporarily remove the secrets from the mongo connection to prevent execution from occurring
    saved_secrets = integration_mongodb_config.secrets
    integration_mongodb_config.secrets = {}
    integration_mongodb_config.save(db)

    access_runner_tester(
        privacy_request,
        policy,
        mongo_postgres_dataset_graph,
        [integration_postgres_config, integration_mongodb_config],
        {"email": "customer-4@example.com"},
        db,
    )

    assert privacy_request.get_failed_checkpoint_details() == CheckpointActionRequired(
        step=CurrentStep.access,
    )

    # Reset secrets
    integration_mongodb_config.secrets = saved_secrets
    integration_mongodb_config.save(db)

    access_runner_tester(
        privacy_request,
        policy,
        mongo_postgres_dataset_graph,
        [integration_postgres_config, integration_mongodb_config],
        {"email": "customer-4@example.com"},
        db,
    )

    db.refresh(privacy_request)

    assert privacy_request.access_tasks.count() > 0

    expected_customer_executions = 2
    assert (
        db.query(ExecutionLog)
        .filter_by(
            privacy_request_id=privacy_request.id,
            dataset_name="postgres_example_test_dataset",
            collection_name="customer",
        )
        .count()
        == expected_customer_executions
    ), "Postgres customer collection execution count mismatch"

    assert db.query(ExecutionLog).filter_by(
        privacy_request_id=privacy_request.id,
        dataset_name="mongo_test",
        collection_name="customer_details",
    )

    customer_detail_logs = [
        (
            get_collection_identifier(log),
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
    erasure_policy,
    integration_postgres_config,
    integration_mongodb_config,
    mongo_postgres_dataset_graph,
    privacy_request_with_erasure_policy,
) -> None:
    """Run a failed privacy request and restart from failure during the erasure portion.

    An erasure request first runs an access and then an erasure request.
    If the erasure portion fails, and we reprocess, we don't re-run the access portion currently.
    """

    # Run access portion like normal
    access_runner_tester(
        privacy_request_with_erasure_policy,
        erasure_policy,
        mongo_postgres_dataset_graph,
        [integration_postgres_config, integration_mongodb_config],
        {"email": "customer-4@example.com"},
        db,
    )
    assert [("access", "in_processing"), ("access", "complete")] == [
        (c.action_type.value, c.status.value)
        for c in db.query(ExecutionLog)
        .filter_by(
            privacy_request_id=privacy_request_with_erasure_policy.id,
            collection_name="address",
        )
        .order_by(ExecutionLog.created_at)
        .all()
    ]

    saved_secrets = {}
    for cc in db.query(ConnectionConfig).filter(
        ConnectionConfig.connection_type == ConnectionType.postgres
    ):
        saved_secrets[cc.key] = cc.secrets.copy()
        cc.secrets = None
        cc.created_at = datetime.now()
        cc.save(db)
    db.commit()

    erasure_runner_tester(
        privacy_request_with_erasure_policy,
        erasure_policy,
        mongo_postgres_dataset_graph,
        [integration_postgres_config, integration_mongodb_config],
        {"email": "customer-4@example.com"},
        get_cached_data_for_erasures(privacy_request_with_erasure_policy.id),
        db,
    )
    assert ["in_processing", "complete", "in_processing", "error"] == [
        c.status.value
        for c in db.query(ExecutionLog)
        .filter_by(
            privacy_request_id=privacy_request_with_erasure_policy.id,
            collection_name="address",
        )
        .order_by(ExecutionLog.created_at)
        .all()
    ]

    for config in db.query(ConnectionConfig).filter(
        ConnectionConfig.connection_type == ConnectionType.postgres
    ):
        config.secrets = saved_secrets[config.key]
        config.save(db)

    erasure_runner_tester(
        privacy_request_with_erasure_policy,
        erasure_policy,
        mongo_postgres_dataset_graph,
        [integration_postgres_config, integration_mongodb_config],
        {"email": "customer-4@example.com"},
        get_cached_data_for_erasures(privacy_request_with_erasure_policy.id),
        db,
    )

    assert (
        db.query(ExecutionLog)
        .filter_by(
            privacy_request_id=privacy_request_with_erasure_policy.id,
            dataset_name="mongo_test",
            collection_name="customer_details",
        )
        .count()
        == 4
    ), "Mongo customer_details collection has two access and two erasures"

    address_logs = [
        (
            get_collection_identifier(log),
            log.action_type.value,
            log.status.value,
        )
        for log in db.query(ExecutionLog)
        .filter_by(
            privacy_request_id=privacy_request_with_erasure_policy.id,
            collection_name="address",
        )
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
