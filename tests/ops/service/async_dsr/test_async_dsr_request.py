import json
import random
from typing import Any, Dict, List
from unittest import mock
from unittest.mock import Mock
from uuid import uuid4

import pytest

from fides.api.common_exceptions import (
    AwaitingAsyncTask,
)
from fides.api.graph.execution import ExecutionNode
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.policy import Policy
from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.redis_cache import Identity
from fides.api.schemas.saas.saas_config import ParamValue, SaaSConfig, SaaSRequest
from fides.api.service.connectors import get_connector
from fides.api.service.connectors.saas_connector import SaaSConnector
from fides.api.models.privacy_request.request_task import AsyncTaskType

from fides.api.task.create_request_tasks import (
    collect_tasks_fn,
    persist_initial_erasure_request_tasks,
    persist_new_access_request_tasks,
)



class TestAsyncDsrRequest:
    """
    Tests the DSR Request flow, from the start of the request to the very completion of it
    """

    @pytest.fixture(scope="function")
    def async_graph(self, saas_async_polling_example_dataset_config, db, privacy_request):
        # Build proper async graph with persisted request tasks
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
        If a read request is marked with needing an async callback response, the initial response is ignored and
        we raise an AwaitingAsyncTask exception.
        We mark the request task as a Polling Task so we can recognize it in the request runner service.

        """
        # Build graph to get legitimate access Request Task
        connector: SaaSConnector = get_connector(saas_async_polling_example_connection_config)
        mock_send().json.return_value = {"results_pending": True}

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
        # Check that we are sending the correct request to the start endpoint
        call_args = mock_send.call_args[0][0]
        assert call_args.path == "/api/v1/user"
        # Check the identity! TODO

        # Check that we have saved the request task as a polling task
        db.refresh(request_task)

        assert request_task.async_type == AsyncTaskType.polling



    def test_status_request_pending_queue_executes():
        """
        If a read request is marked with needing an async callback response, the initial response is ignored and
        we raise an AwaitingAsyncTask exception
        """
        # Build graph to get legitimate access Request Task
        connector: SaaSConnector = get_connector(saas_async_polling_example_connection_config)
        mock_send().json.return_value = {"results_pending": True}

        # Mock this request task with expected attributes if the callback endpoint was hit

    def test_status_request_complete_queue_executes():
        """
        If a read request is marked with needing an async callback response, the initial response is ignored and
        we raise an AwaitingAsyncTask exception
        """
        # Build graph to get legitimate access Request Task
        connector: SaaSConnector = get_connector(saas_async_polling_example_connection_config)
        mock_send().json.return_value = {"results_pending": True}

        # Mock this request task with expected attributes if the callback endpoint was hit

    def test_finished_async_request_does_not_execute():
        """
        If a read request is marked with needing an async callback response, the initial response is ignored and
        we raise an AwaitingAsyncTask exception
        """
        # Build graph to get legitimate access Request Task
        connector: SaaSConnector = get_connector(saas_async_polling_example_connection_config)
        mock_send().json.return_value = {"results_pending": True}

        # Mock this request task with expected attributes if the callback endpoint was hit
