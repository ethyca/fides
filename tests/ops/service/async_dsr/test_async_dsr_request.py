import time
from unittest import mock
from unittest.mock import Mock

import pytest
from loguru import logger

from fides.api.common_exceptions import AwaitingAsyncTask
from fides.api.graph.execution import ExecutionNode
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.privacy_request import RequestTask
from fides.api.models.privacy_request.request_task import AsyncTaskType
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.async_dsr.async_dsr_service import execute_polling_task
from fides.api.service.connectors import get_connector
from fides.api.service.connectors.saas_connector import SaaSConnector
from fides.api.task.create_request_tasks import (
    collect_tasks_fn,
    persist_initial_erasure_request_tasks,
    persist_new_access_request_tasks,
)
from tests.ops.service.privacy_request.test_request_runner_service import (
    get_privacy_request_results,
)


class TestAsyncDsrRequest:
    """
    Tests the DSR Request flow, from the start of the request to the very completion of it
    """

    @pytest.fixture(scope="function")
    def async_graph(
        self, saas_async_polling_example_dataset_config, db, privacy_request
    ):
        # Build proper async graph with persisted request tasks to test the connector
        async_graph = saas_async_polling_example_dataset_config.get_graph()
        graph = DatasetGraph(async_graph)
        traversal = Traversal(graph, {"email": "customer-1@example.com"})
        traversal_nodes = {}
        end_nodes = traversal.traverse(traversal_nodes, collect_tasks_fn)
        persist_new_access_request_tasks(
            db, privacy_request, traversal, traversal_nodes, end_nodes, graph
        )
        persist_initial_erasure_request_tasks(
            db, privacy_request, traversal_nodes, end_nodes, graph
        )

    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_read_request_expects_async_results(
        self,
        mock_send: Mock,
        privacy_request,
        db,
        saas_async_polling_example_connection_config,
        async_graph,
    ):
        """
        If a read request is marked with needing an async polling response, the initial response is ignored and
        we raise an AwaitingAsyncTask exception.
        We mark the request task as a Polling Task so we can recognize it in the request runner service.

        """
        # Build graph to get legitimate access Request Task
        connector: SaaSConnector = get_connector(
            saas_async_polling_example_connection_config
        )
        mock_send().json.return_value = {
            "id": "123",
        }

        # Mock this request task with expected attributes if the callback endpoint was hit
        request_task = privacy_request.access_tasks.filter(
            RequestTask.collection_name == "user"
        ).first()

        execution_node = ExecutionNode(request_task)

        with pytest.raises(AwaitingAsyncTask):
            assert (
                connector.retrieve_data(
                    execution_node,
                    privacy_request.policy,
                    privacy_request,
                    request_task,
                    {},
                )
                == []
            )
        logger.info(f"Request Task: {request_task.access_data}")

        # Check that we are sending the correct request to the start endpoint
        call_args = mock_send.call_args[0][0]
        assert call_args.path == "/api/v1/user"
        # Check that we are storing properly the async type and the data
        assert request_task.async_type == AsyncTaskType.polling
        assert request_task.get_access_data() == [
            {
                "id": "123",
            }
        ]

    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_status_request_pending_queue_executes(
        self,
        mock_send: Mock,
        saas_async_polling_example_connection_config,
        saas_async_polling_example_dataset_config,
        db,
        policy,
        dsr_version,
        request,
        run_privacy_request_task,
    ):
        """
        When we have a pending status request with polling, when we execute the queue, we should call the status endpoint
        and get the result status.
        If its pending, then we should continue to poll and await the results.
        """
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
        mock_send().json.return_value = {"id": "123"}
        pr = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            {"identity": {"email": "customer-1@example.com"}},
            task_timeout=120,
        )
        db.refresh(pr)
        if dsr_version == "use_dsr_2_0":
            # Async Access Requests not supported for DSR 2.0 - the given
            # node cannot be paused
            assert pr.status == PrivacyRequestStatus.complete
            return
        if dsr_version == "use_dsr_3_0":
            assert pr.status == PrivacyRequestStatus.in_processing
            assert pr.access_tasks[0].status == ExecutionLogStatus.complete
            # Saas Polling task was marked as needing async results, so the Request
            # Task was put in a paused state
            assert pr.access_tasks[1].status == ExecutionLogStatus.awaiting_processing
            assert (
                pr.access_tasks[1].collection_address
                == "saas_async_polling_config:user"
            )

            mock_send().json.return_value = {"request_complete": False}
            # Requeue the polling task
            execute_polling_task(db, pr.access_tasks[1])
            db.refresh(pr)
            # We are still awaiting for processing and data should be the base response data
            assert pr.access_tasks[1].status == ExecutionLogStatus.awaiting_processing
            assert pr.access_tasks[1].get_access_data() == [
                {
                    "id": "123",
                }
            ]

            mock_send().json.return_value = {"request_complete": True}
            # Requeue the polling task
            execute_polling_task(db, pr.access_tasks[1])
            time.sleep(10)
            db.refresh(pr)
            # We are still awaiting for processing and data should be the base response data
            assert pr.access_tasks[1].status == ExecutionLogStatus.complete
            # Access Data tests require a MockAuthenticatedClient thats on Fidesplus to chain return values.
