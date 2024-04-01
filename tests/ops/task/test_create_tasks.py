from datetime import datetime

import pytest
from fideslang import Dataset

from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal, TraversalNode
from fides.api.models.datasetconfig import convert_dataset_to_graph
from fides.api.models.privacy_request import ExecutionLogStatus, RequestTask
from fides.api.schemas.policy import ActionType
from fides.api.task.create_tasks import (
    collect_tasks_fn,
    persist_initial_erasure_request_tasks,
    persist_new_access_request_tasks,
    persist_new_consent_request_tasks,
    run_consent_request,
    update_erasure_tasks_with_access_data,
)
from fides.api.task.execute_tasks import run_access_node
from fides.api.task.graph_task import build_consent_dataset_graph
from tests.conftest import wait_for_access_terminator_completion

payment_card_serialized_collection = {
    "name": "payment_card",
    "after": [],
    "fields": [
        {
            "name": "billing_address_id",
            "length": None,
            "identity": None,
            "is_array": False,
            "read_only": None,
            "references": [["postgres_example_test_dataset:address:id", "to"]],
            "primary_key": False,
            "data_categories": ["system.operations"],
            "data_type_converter": "None",
            "return_all_elements": None,
        },
        {
            "name": "ccn",
            "length": None,
            "identity": None,
            "is_array": False,
            "read_only": None,
            "references": [],
            "primary_key": False,
            "data_categories": ["user.financial.bank_account"],
            "data_type_converter": "None",
            "return_all_elements": None,
        },
        {
            "name": "code",
            "length": None,
            "identity": None,
            "is_array": False,
            "read_only": None,
            "references": [],
            "primary_key": False,
            "data_categories": ["user.financial"],
            "data_type_converter": "None",
            "return_all_elements": None,
        },
        {
            "name": "customer_id",
            "length": None,
            "identity": None,
            "is_array": False,
            "read_only": None,
            "references": [["postgres_example_test_dataset:customer:id", "from"]],
            "primary_key": False,
            "data_categories": ["user.unique_id"],
            "data_type_converter": "None",
            "return_all_elements": None,
        },
        {
            "name": "id",
            "length": None,
            "identity": None,
            "is_array": False,
            "read_only": None,
            "references": [],
            "primary_key": True,
            "data_categories": ["system.operations"],
            "data_type_converter": "None",
            "return_all_elements": None,
        },
        {
            "name": "name",
            "length": None,
            "identity": None,
            "is_array": False,
            "read_only": None,
            "references": [],
            "primary_key": False,
            "data_categories": ["user.financial"],
            "data_type_converter": "None",
            "return_all_elements": None,
        },
        {
            "name": "preferred",
            "length": None,
            "identity": None,
            "is_array": False,
            "read_only": None,
            "references": [],
            "primary_key": False,
            "data_categories": ["user"],
            "data_type_converter": "None",
            "return_all_elements": None,
        },
    ],
    "erase_after": [],
    "grouped_inputs": [],
    "skip_processing": False,
}

payment_card_serialized_traversal_details = {
    "input_keys": ["postgres_example_test_dataset:customer"],
    "incoming_edges": [
        [
            "postgres_example_test_dataset:customer:id",
            "postgres_example_test_dataset:payment_card:customer_id",
        ]
    ],
    "outgoing_edges": [
        [
            "postgres_example_test_dataset:payment_card:billing_address_id",
            "postgres_example_test_dataset:address:id",
        ]
    ],
    "dataset_connection_key": "postgres_example",
}


class TestPersistRequestTasks:
    @pytest.fixture()
    def postgres_dataset_graph(self, example_datasets, integration_postgres_config):
        dataset_postgres = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(
            dataset_postgres, integration_postgres_config.key
        )

        dataset_graph = DatasetGraph(*[graph])
        return dataset_graph

    def test_persist_access_tasks(self, db, privacy_request, postgres_dataset_graph):
        """Test the RequestTasks that are generated for an access request"""
        identity = {"email": "customer-1@example.com"}
        traversal: Traversal = Traversal(postgres_dataset_graph, identity)
        traversal_nodes = {}
        end_nodes = traversal.traverse(traversal_nodes, collect_tasks_fn)

        ready_tasks = persist_new_access_request_tasks(
            db,
            privacy_request,
            traversal,
            traversal_nodes,
            end_nodes,
            postgres_dataset_graph,
        )
        assert len(ready_tasks) == 1

        root_task = ready_tasks[0]
        # The Root Task is the only one ready to be queued - assert key details
        assert root_task.privacy_request_id == privacy_request.id
        assert root_task.action_type == ActionType.access
        assert root_task.collection_address == "__ROOT__:__ROOT__"
        assert root_task.dataset_name == "__ROOT__"
        assert root_task.collection_name == "__ROOT__"
        # We just create the root task in the completed state automatically
        assert root_task.status == ExecutionLogStatus.complete
        assert root_task.upstream_tasks == []
        # These are the downstream data dependencies
        assert root_task.downstream_tasks == [
            "postgres_example_test_dataset:customer",
            "postgres_example_test_dataset:employee",
            "postgres_example_test_dataset:report",
            "postgres_example_test_dataset:service_request",
            "postgres_example_test_dataset:visit",
        ]
        # All nodes can be reached by the root node
        assert (
            len(root_task.all_descendant_tasks)
            == 12
            == privacy_request.access_tasks.count() - 1
        )
        # Identity data is saved as access data -
        assert root_task.access_data == '[{"email": "customer-1@example.com"}]'
        assert root_task.get_decoded_access_data() == [
            {"email": "customer-1@example.com"}
        ]
        assert root_task.erasure_input_data is None
        # ARTIFICIAL NODES don't have collections or traversal details
        assert root_task.collection is None
        assert root_task.traversal_details == {}
        assert root_task.is_root_task
        assert not root_task.is_terminator_task

        # Assert key details on terminator task
        terminator_task = privacy_request.access_tasks.filter(
            RequestTask.collection_address == "__TERMINATE__:__TERMINATE__"
        ).first()
        assert terminator_task.action_type == ActionType.access
        assert terminator_task.collection_name == "__TERMINATE__"
        assert terminator_task.dataset_name == "__TERMINATE__"
        assert terminator_task.status == ExecutionLogStatus.pending
        assert terminator_task.upstream_tasks == [
            "postgres_example_test_dataset:address",
            "postgres_example_test_dataset:login",
            "postgres_example_test_dataset:product",
            "postgres_example_test_dataset:report",
            "postgres_example_test_dataset:service_request",
            "postgres_example_test_dataset:visit",
        ]

        assert terminator_task.downstream_tasks == []
        assert terminator_task.all_descendant_tasks == []
        assert terminator_task.access_data == "[]"
        assert terminator_task.erasure_input_data is None
        # ARTIFICIAL NODES don't have collections or traversal details
        assert terminator_task.collection is None
        assert terminator_task.traversal_details == {}
        assert not terminator_task.is_root_task
        assert terminator_task.is_terminator_task

        # Assert key details on payment card task
        payment_card_task = privacy_request.access_tasks.filter(
            RequestTask.collection_address
            == "postgres_example_test_dataset:payment_card"
        ).first()
        assert payment_card_task.action_type == ActionType.access
        assert payment_card_task.collection_name == "payment_card"
        assert payment_card_task.dataset_name == "postgres_example_test_dataset"
        assert payment_card_task.status == ExecutionLogStatus.pending
        assert payment_card_task.upstream_tasks == [
            "postgres_example_test_dataset:customer"
        ]
        assert payment_card_task.downstream_tasks == [
            "postgres_example_test_dataset:address"
        ]
        assert payment_card_task.all_descendant_tasks == [
            "__TERMINATE__:__TERMINATE__",
            "postgres_example_test_dataset:address",
        ]
        assert payment_card_task.access_data == "[]"
        assert payment_card_task.erasure_input_data is None
        assert payment_card_task.collection == payment_card_serialized_collection
        assert (
            payment_card_task.traversal_details
            == payment_card_serialized_traversal_details
        )
        assert not payment_card_task.is_root_task
        assert not payment_card_task.is_terminator_task

    def test_persist_initial_erasure_request_tasks(
        self, db, privacy_request, postgres_dataset_graph
    ):
        """Test the RequestTasks that are generated for an erasure graph
        These are generated at the same time as the access graph, but are not runnable
        until the access graph is completed in full
        """
        identity = {"email": "customer-1@example.com"}
        traversal: Traversal = Traversal(postgres_dataset_graph, identity)

        traversal_nodes = {}
        _ = traversal.traverse(traversal_nodes, collect_tasks_fn)
        erasure_end_nodes = list(postgres_dataset_graph.nodes.keys())

        ready_tasks = persist_initial_erasure_request_tasks(
            db,
            privacy_request,
            traversal_nodes,
            erasure_end_nodes,
            postgres_dataset_graph,
        )
        assert ready_tasks == []

        assert privacy_request.erasure_tasks.count() == 13

        root_task = privacy_request.erasure_tasks.filter(
            RequestTask.collection_address == "__ROOT__:__ROOT__"
        ).first()
        assert root_task.action_type == ActionType.erasure
        assert root_task.privacy_request_id == privacy_request.id
        assert root_task.collection_address == "__ROOT__:__ROOT__"
        assert root_task.dataset_name == "__ROOT__"
        assert root_task.collection_name == "__ROOT__"
        assert root_task.status == ExecutionLogStatus.complete
        assert root_task.upstream_tasks == []
        # Every node other than the terminate node is downstream
        assert root_task.downstream_tasks == [
            "postgres_example_test_dataset:address",
            "postgres_example_test_dataset:customer",
            "postgres_example_test_dataset:employee",
            "postgres_example_test_dataset:login",
            "postgres_example_test_dataset:order_item",
            "postgres_example_test_dataset:orders",
            "postgres_example_test_dataset:payment_card",
            "postgres_example_test_dataset:product",
            "postgres_example_test_dataset:report",
            "postgres_example_test_dataset:service_request",
            "postgres_example_test_dataset:visit",
        ]
        # Every node that can be reached by the root node
        assert (
            len(root_task.all_descendant_tasks)
            == 12
            == privacy_request.erasure_tasks.count() - 1
        )
        assert root_task.access_data is None
        assert root_task.data_for_erasures is None
        assert root_task.erasure_input_data is None
        assert root_task.get_decoded_access_data() == []
        # ARTIFICIAL NODES don't have collections or traversal details
        assert root_task.collection is None
        assert root_task.traversal_details == {}
        assert root_task.is_root_task
        assert not root_task.is_terminator_task

        # Assert key details on terminator task
        terminator_task = privacy_request.erasure_tasks.filter(
            RequestTask.collection_address == "__TERMINATE__:__TERMINATE__"
        ).first()
        assert terminator_task.action_type == ActionType.erasure
        assert terminator_task.collection_name == "__TERMINATE__"
        assert terminator_task.dataset_name == "__TERMINATE__"
        assert terminator_task.status == ExecutionLogStatus.pending
        # Every node but the root node has the terminator task downstream
        assert terminator_task.upstream_tasks == root_task.downstream_tasks
        assert terminator_task.downstream_tasks == []
        assert terminator_task.all_descendant_tasks == []
        assert terminator_task.access_data is None
        assert terminator_task.data_for_erasures is None
        assert terminator_task.erasure_input_data is None
        # ARTIFICIAL NODES don't have collections or traversal details
        assert terminator_task.collection is None
        assert terminator_task.traversal_details == {}
        assert not terminator_task.is_root_task
        assert terminator_task.is_terminator_task

        # Assert key details on payment card task
        payment_card_task = privacy_request.erasure_tasks.filter(
            RequestTask.collection_address
            == "postgres_example_test_dataset:payment_card"
        ).first()
        assert payment_card_task.action_type == ActionType.erasure
        assert payment_card_task.collection_name == "payment_card"
        assert payment_card_task.dataset_name == "postgres_example_test_dataset"
        assert payment_card_task.status == ExecutionLogStatus.pending
        assert payment_card_task.upstream_tasks == ["__ROOT__:__ROOT__"]
        assert payment_card_task.downstream_tasks == [
            "__TERMINATE__:__TERMINATE__",
        ]
        assert payment_card_task.all_descendant_tasks == [
            "__TERMINATE__:__TERMINATE__",
        ]
        assert payment_card_task.access_data is None
        assert payment_card_task.data_for_erasures is None
        assert payment_card_task.erasure_input_data is None
        assert payment_card_task.collection == payment_card_serialized_collection
        assert (
            payment_card_task.traversal_details
            == payment_card_serialized_traversal_details
        )

        assert not payment_card_task.is_root_task
        assert not payment_card_task.is_terminator_task

    @pytest.mark.timeout(5)
    @pytest.mark.integration_postgres
    def test_update_erasure_tasks_with_access_data(
        self, db, privacy_request, postgres_dataset_graph
    ):
        """Test that erasure tasks are updated with the corresponding erasure data collected
        from the access task"""
        identity = {"email": "customer-1@example.com"}
        traversal: Traversal = Traversal(postgres_dataset_graph, identity)

        traversal_nodes = {}
        access_end_nodes = traversal.traverse(traversal_nodes, collect_tasks_fn)
        erasure_end_nodes = list(postgres_dataset_graph.nodes.keys())

        ready_tasks = persist_new_access_request_tasks(
            db,
            privacy_request,
            traversal,
            traversal_nodes,
            access_end_nodes,
            postgres_dataset_graph,
        )

        persist_initial_erasure_request_tasks(
            db,
            privacy_request,
            traversal_nodes,
            erasure_end_nodes,
            postgres_dataset_graph,
        )

        run_access_node.delay(privacy_request.id, ready_tasks[0].id)
        wait_for_access_terminator_completion(db, privacy_request)

        update_erasure_tasks_with_access_data(db, privacy_request)
        payment_card_task = privacy_request.erasure_tasks.filter(
            RequestTask.collection_address
            == "postgres_example_test_dataset:payment_card"
        ).first()

        # access data collected for masking was added to the erasure node of the same address
        assert (
            payment_card_task.data_for_erasures
            == '[{"billing_address_id": 1, "ccn": 123456789, "code": 321, "customer_id": 1, "id": "pay_aaa-aaa", "name": "Example Card 1", "preferred": true}]'
        )
        assert payment_card_task.get_decoded_data_for_erasures() == [
            {
                "billing_address_id": 1,
                "ccn": 123456789,
                "code": 321,
                "customer_id": 1,
                "id": "pay_aaa-aaa",
                "name": "Example Card 1",
                "preferred": True,
            }
        ]

        # Access data from upstream nodes added for use in nodes that don't collect their own access data like emails
        assert (
            payment_card_task.erasure_input_data
            == '[[{"address_id": 1, "created": "date_encoded_2020-04-01T11:47:42", "email": "customer-1@example.com", "id": 1, "name": "John Customer"}]]'
        )
        assert payment_card_task.get_decoded_erasure_input_data() == [
            [
                {
                    "address_id": 1,
                    "created": datetime(2020, 4, 1, 11, 47, 42),
                    "email": "customer-1@example.com",
                    "id": 1,
                    "name": "John Customer",
                }
            ]
        ]
        assert payment_card_task.status == ExecutionLogStatus.pending

    def test_persist_new_consent_request_tasks(
        self,
        db,
        privacy_request,
        google_analytics_connection_config_without_secrets,
        google_analytics_dataset_config_no_secrets,
    ):
        graph = build_consent_dataset_graph(
            [google_analytics_dataset_config_no_secrets]
        )

        traversal_nodes = {}
        # Unlike erasure and access graphs, we don't call traversal.traverse, but build a simpler
        # graph that just has one node per dataset
        for col_address, node in graph.nodes.items():
            traversal_node = TraversalNode(node)
            traversal_nodes[col_address] = traversal_node

        ready_tasks = persist_new_consent_request_tasks(
            db, privacy_request, traversal_nodes, {"ga_client_id": "test_id"}, graph
        )

        assert len(ready_tasks) == 1
        root_task = ready_tasks[0]
        assert root_task.is_root_task
        assert root_task.action_type == ActionType.consent
        assert root_task.upstream_tasks == []
        assert root_task.downstream_tasks == [
            "google_analytics_instance:google_analytics_instance"
        ]
        assert root_task.all_descendant_tasks == [
            "__TERMINATE__:__TERMINATE__",
            "google_analytics_instance:google_analytics_instance",
        ]
        assert root_task.status == ExecutionLogStatus.complete

        terminator_task = privacy_request.consent_tasks.filter(
            RequestTask.collection_address == "__TERMINATE__:__TERMINATE__",
        ).first()
        assert terminator_task.is_terminator_task
        assert terminator_task.action_type == ActionType.consent
        assert terminator_task.upstream_tasks == [
            "google_analytics_instance:google_analytics_instance"
        ]
        assert terminator_task.downstream_tasks == []
        assert terminator_task.all_descendant_tasks == []
        assert terminator_task.status == ExecutionLogStatus.pending

        ga_task = privacy_request.consent_tasks.filter(
            RequestTask.collection_address
            == "google_analytics_instance:google_analytics_instance",
        ).first()
        assert not ga_task.is_root_task
        assert not ga_task.is_terminator_task
        assert ga_task.action_type == ActionType.consent
        assert ga_task.upstream_tasks == ["__ROOT__:__ROOT__"]
        assert ga_task.downstream_tasks == ["__TERMINATE__:__TERMINATE__"]
        assert ga_task.all_descendant_tasks == ["__TERMINATE__:__TERMINATE__"]
        assert ga_task.status == ExecutionLogStatus.pending

        assert ga_task.collection == {
            "name": "google_analytics_instance",
            "after": [],
            "fields": [],
            "erase_after": [],
            "grouped_inputs": [],
            "skip_processing": False,
        }
        assert ga_task.traversal_details == {
            "input_keys": [],
            "incoming_edges": [],
            "outgoing_edges": [],
            "dataset_connection_key": "google_analytics_instance",
        }
