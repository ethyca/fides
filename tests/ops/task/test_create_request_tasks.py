from datetime import datetime
from unittest import mock
from unittest.mock import MagicMock

import pytest
from fideslang import Dataset

from fides.api.common_exceptions import TraversalError
from fides.api.graph.config import ROOT_COLLECTION_ADDRESS, TERMINATOR_ADDRESS
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal, TraversalNode
from fides.api.models.datasetconfig import convert_dataset_to_graph
from fides.api.models.privacy_request import ExecutionLog, RequestTask
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import ExecutionLogStatus, PrivacyRequestStatus
from fides.api.task.create_request_tasks import (
    collect_tasks_fn,
    get_existing_ready_tasks,
    persist_initial_erasure_request_tasks,
    persist_new_access_request_tasks,
    persist_new_consent_request_tasks,
    run_access_request,
    run_consent_request,
    run_erasure_request,
    update_erasure_tasks_with_access_data,
)
from fides.api.task.execute_request_tasks import run_access_node
from fides.api.task.graph_task import build_consent_dataset_graph
from fides.config import CONFIG
from tests.conftest import wait_for_tasks_to_complete
from tests.ops.task.traversal_data import combined_mongo_postgresql_graph

from ..graph.graph_test_util import erasure_policy, field

payment_card_serialized_collection = {
    "name": "payment_card",
    "after": [],
    "masking_strategy_override": None,
    "partitioning": None,
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
            "custom_request_field": None,
            "masking_strategy_override": None,
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
            "custom_request_field": None,
            "masking_strategy_override": None,
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
            "custom_request_field": None,
            "masking_strategy_override": None,
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
            "custom_request_field": None,
            "masking_strategy_override": None,
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
            "custom_request_field": None,
            "masking_strategy_override": None,
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
            "custom_request_field": None,
            "masking_strategy_override": None,
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
            "custom_request_field": None,
            "masking_strategy_override": None,
        },
    ],
    "erase_after": [],
    "grouped_inputs": [],
    "skip_processing": False,
    "data_categories": [],
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
    "dataset_connection_key": "my_postgres_db_1",
    "skipped_nodes": None,
}


class TestPersistAccessRequestTasks:
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
        # Identity data is saved as encrypted access data -
        assert root_task.access_data == [{"email": "customer-1@example.com"}]
        assert root_task.get_access_data() == [{"email": "customer-1@example.com"}]
        # ARTIFICIAL NODES don't have collections or traversal details
        assert root_task.collection is None
        assert root_task.traversal_details == {}
        assert root_task.is_root_task
        assert not root_task.is_terminator_task

        # Assert key details on terminator task
        terminator_task = privacy_request.get_terminate_task_by_action(
            ActionType.access
        )

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
        assert terminator_task.access_data == []
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
        assert payment_card_task.access_data == []
        assert payment_card_task.collection == payment_card_serialized_collection
        assert (
            payment_card_task.traversal_details
            == payment_card_serialized_traversal_details
        )
        assert not payment_card_task.is_root_task
        assert not payment_card_task.is_terminator_task

    def test_persist_access_tasks_with_object_fields_in_collection(
        self, db, privacy_request, postgres_and_mongo_dataset_graph
    ):
        identity = {"email": "customer-1@example.com"}

        traversal: Traversal = Traversal(postgres_and_mongo_dataset_graph, identity)
        traversal_nodes = {}
        end_nodes = traversal.traverse(traversal_nodes, collect_tasks_fn)

        ready_tasks = persist_new_access_request_tasks(
            db,
            privacy_request,
            traversal,
            traversal_nodes,
            end_nodes,
            postgres_and_mongo_dataset_graph,
        )
        assert len(ready_tasks) == 1

        customer_profile = privacy_request.access_tasks.filter(
            RequestTask.collection_address == "mongo_test:internal_customer_profile"
        ).first()

        # Object fields serialized correctly
        assert customer_profile.collection == {
            "name": "internal_customer_profile",
            "after": [],
            "masking_strategy_override": None,
            "partitioning": None,
            "fields": [
                {
                    "name": "_id",
                    "length": None,
                    "identity": None,
                    "is_array": False,
                    "read_only": None,
                    "references": [],
                    "primary_key": True,
                    "data_categories": ["system.operations"],
                    "data_type_converter": "object_id",
                    "return_all_elements": None,
                    "custom_request_field": None,
                    "masking_strategy_override": None,
                },
                {
                    "name": "customer_identifiers",
                    "fields": {
                        "internal_id": {
                            "name": "internal_id",
                            "length": None,
                            "identity": None,
                            "is_array": False,
                            "read_only": None,
                            "references": [
                                [
                                    "mongo_test:customer_feedback:customer_information.internal_customer_id",
                                    "from",
                                ]
                            ],
                            "primary_key": False,
                            "data_categories": None,
                            "data_type_converter": "string",
                            "return_all_elements": None,
                            "custom_request_field": None,
                            "masking_strategy_override": None,
                        },
                        "derived_phone": {
                            "name": "derived_phone",
                            "length": None,
                            "identity": "phone_number",
                            "is_array": True,
                            "read_only": None,
                            "references": [],
                            "primary_key": False,
                            "data_categories": ["user"],
                            "data_type_converter": "string",
                            "return_all_elements": True,
                            "custom_request_field": None,
                            "masking_strategy_override": None,
                        },
                        "derived_emails": {
                            "name": "derived_emails",
                            "length": None,
                            "identity": "email",
                            "is_array": True,
                            "read_only": None,
                            "references": [],
                            "primary_key": False,
                            "data_categories": ["user"],
                            "data_type_converter": "string",
                            "return_all_elements": None,
                            "custom_request_field": None,
                            "masking_strategy_override": None,
                        },
                    },
                    "length": None,
                    "identity": None,
                    "is_array": False,
                    "read_only": None,
                    "references": [],
                    "primary_key": False,
                    "data_categories": None,
                    "data_type_converter": "object",
                    "return_all_elements": None,
                    "custom_request_field": None,
                    "masking_strategy_override": None,
                },
                {
                    "name": "derived_interests",
                    "length": None,
                    "identity": None,
                    "is_array": True,
                    "read_only": None,
                    "references": [],
                    "primary_key": False,
                    "data_categories": ["user"],
                    "data_type_converter": "string",
                    "return_all_elements": None,
                    "custom_request_field": None,
                    "masking_strategy_override": None,
                },
            ],
            "erase_after": [],
            "grouped_inputs": [],
            "skip_processing": False,
            "data_categories": [],
        }

    def test_no_collections(self, db, privacy_request):
        identity = {"email": "customer-1@example.com"}

        traversal: Traversal = Traversal(DatasetGraph(), identity)
        traversal_nodes = {}
        end_nodes = traversal.traverse(traversal_nodes, collect_tasks_fn)

        ready_tasks = persist_new_access_request_tasks(
            db,
            privacy_request,
            traversal,
            traversal_nodes,
            end_nodes,
            DatasetGraph(),
        )

        assert len(ready_tasks) == 1
        db.refresh(privacy_request)
        assert len(privacy_request.access_tasks.all()) == 2
        assert privacy_request.access_tasks[0].is_root_task
        assert privacy_request.access_tasks[0].upstream_tasks == []
        assert privacy_request.access_tasks[0].downstream_tasks == [
            TERMINATOR_ADDRESS.value
        ]

        assert privacy_request.access_tasks[1].is_terminator_task
        assert privacy_request.access_tasks[1].upstream_tasks == [
            ROOT_COLLECTION_ADDRESS.value
        ]
        assert privacy_request.access_tasks[1].downstream_tasks == []

    @mock.patch(
        "fides.api.task.create_request_tasks.queue_request_task",
    )
    def test_run_access_request_no_request_tasks_existing(
        self, run_access_node_mock, db, privacy_request, policy
    ):
        """Request tasks created by run_access_request and the root task is queued"""
        ready = run_access_request(
            privacy_request,
            policy,
            DatasetGraph(),
            [],
            {"email": "customer-4@example.com"},
            db,
            privacy_request_proceed=False,
        )

        assert len(ready) == 1
        root_task = ready[0]
        assert root_task.is_root_task

        assert run_access_node_mock.called
        run_access_node_mock.assert_called_with(root_task, False)

    @mock.patch(
        "fides.api.task.create_request_tasks.queue_request_task",
    )
    def test_reprocess_access_request_with_existing_request_tasks(
        self, run_access_node_mock, request_task, db, privacy_request, policy
    ):
        assert privacy_request.access_tasks.count() == 3

        ready = run_access_request(
            privacy_request,
            policy,
            DatasetGraph(),
            [],
            {"email": "customer-4@example.com"},
            db,
            privacy_request_proceed=False,
        )

        assert len(ready) == 1
        ready_task = ready[0]
        assert ready_task == request_task
        assert not ready_task.is_root_task
        assert ready_task.status == ExecutionLogStatus.pending

        assert run_access_node_mock.called
        run_access_node_mock.assert_called_with(request_task, False)

    @mock.patch(
        "fides.api.task.create_request_tasks.queue_request_task",
    )
    def test_run_access_request_with_unreachable_nodes(
        self,
        run_access_node_mock,
        db,
        privacy_request,
        policy,
        dataset_graph_with_unreachable_collections: DatasetGraph,
    ):
        """Request tasks created by run_access_request and the root task is queued"""
        with pytest.raises(TraversalError) as err:
            run_access_request(
                privacy_request,
                policy,
                dataset_graph_with_unreachable_collections,
                [],
                {"email": "customer-4@example.com"},
                db,
                privacy_request_proceed=False,
            )

        assert "Some nodes were not reachable:" in str(err.value)
        assert "dataset_with_unreachable_collections:login" in str(err.value)
        assert "dataset_with_unreachable_collections:report" in str(err.value)

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.error

        # We expect two error logs, one per unreachable collection
        error_logs = privacy_request.execution_logs.filter(
            ExecutionLog.status == ExecutionLogStatus.error
        )
        assert error_logs.count() == 2
        error_logs = sorted(
            error_logs, key=lambda execution_log: execution_log.collection_name
        )
        assert error_logs[0].dataset_name == "Dataset traversal"
        assert (
            error_logs[0].collection_name
            == "dataset_with_unreachable_collections.login"
        )
        assert (
            error_logs[0].message
            == "Node dataset_with_unreachable_collections:login is not reachable"
        )
        assert error_logs[1].dataset_name == "Dataset traversal"
        assert (
            error_logs[1].collection_name
            == "dataset_with_unreachable_collections.report"
        )
        assert (
            error_logs[1].message
            == "Node dataset_with_unreachable_collections:report is not reachable"
        )

        run_access_node_mock.assert_not_called()


class TestPersistErasureRequestTasks:
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
        # Because the access graph completes in full first, getting all the data the erasure
        # graph needs to build masking requests, the erasure graph can be run entirely
        # in parallel. So the end nodes are all of the nodes.
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

        root_task = privacy_request.get_root_task_by_action(ActionType.erasure)
        assert root_task.action_type == ActionType.erasure
        assert root_task.privacy_request_id == privacy_request.id
        assert root_task.collection_address == "__ROOT__:__ROOT__"
        assert root_task.dataset_name == "__ROOT__"
        assert root_task.collection_name == "__ROOT__"
        assert root_task.status == ExecutionLogStatus.complete
        assert root_task.upstream_tasks == []
        # Every node other than the terminate node is downstream of the root node
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
        assert root_task.get_access_data() == []
        # ARTIFICIAL NODES don't have collections or traversal details
        assert root_task.collection is None
        assert root_task.traversal_details == {}
        assert root_task.is_root_task
        assert not root_task.is_terminator_task

        # Assert key details on terminator task
        terminator_task = privacy_request.get_terminate_task_by_action(
            ActionType.erasure
        )
        assert terminator_task.action_type == ActionType.erasure
        assert terminator_task.collection_name == "__TERMINATE__"
        assert terminator_task.dataset_name == "__TERMINATE__"
        assert terminator_task.status == ExecutionLogStatus.pending
        # Every node but the root node has the terminator task downstream of it
        assert terminator_task.upstream_tasks == root_task.downstream_tasks
        assert terminator_task.downstream_tasks == []
        assert terminator_task.all_descendant_tasks == []
        assert terminator_task.access_data is None
        assert terminator_task.data_for_erasures is None
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
        # Even though the downstream task is just the terminate node and the upstream
        # task is just the root node, it's upstream and downstream edges are still
        # based on data dependencies
        assert payment_card_task.collection == payment_card_serialized_collection
        assert (
            payment_card_task.traversal_details
            == payment_card_serialized_traversal_details
        )

        assert not payment_card_task.is_root_task
        assert not payment_card_task.is_terminator_task

    @pytest.mark.timeout(5)
    @pytest.mark.integration
    @pytest.mark.integration_postgres
    def test_update_erasure_tasks_with_access_data(
        self, db, privacy_request, example_datasets, integration_postgres_config
    ):
        """Test that erasure tasks are updated with the corresponding erasure data collected
        from the access task"""
        dataset = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, integration_postgres_config.key)
        dataset_graph = DatasetGraph(*[graph])

        identity = {"email": "customer-1@example.com"}
        traversal: Traversal = Traversal(dataset_graph, identity)

        traversal_nodes = {}
        access_end_nodes = traversal.traverse(traversal_nodes, collect_tasks_fn)
        erasure_end_nodes = list(dataset_graph.nodes.keys())

        ready_tasks = persist_new_access_request_tasks(
            db,
            privacy_request,
            traversal,
            traversal_nodes,
            access_end_nodes,
            dataset_graph,
        )

        persist_initial_erasure_request_tasks(
            db,
            privacy_request,
            traversal_nodes,
            erasure_end_nodes,
            dataset_graph,
        )

        run_access_node.delay(
            privacy_request.id, ready_tasks[0].id, privacy_request_proceed=False
        )
        wait_for_tasks_to_complete(db, privacy_request, ActionType.access)

        update_erasure_tasks_with_access_data(db, privacy_request)
        payment_card_task = privacy_request.erasure_tasks.filter(
            RequestTask.collection_address
            == "postgres_example_test_dataset:payment_card"
        ).first()

        # access data collected for masking was added to this erasure node of the same address
        assert payment_card_task.data_for_erasures == [
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
        assert payment_card_task.get_data_for_erasures() == [
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
        assert payment_card_task.status == ExecutionLogStatus.pending

        address_task = privacy_request.erasure_tasks.filter(
            RequestTask.collection_address == "postgres_example_test_dataset:address"
        ).first()

        assert address_task.traversal_details["input_keys"] == [
            "postgres_example_test_dataset:customer",
            "postgres_example_test_dataset:employee",
            "postgres_example_test_dataset:orders",
            "postgres_example_test_dataset:payment_card",
        ]

    @pytest.mark.timeout(5)
    @pytest.mark.integration
    @pytest.mark.integration_postgres
    @pytest.mark.integration_mongodb
    def test_update_erasure_tasks_with_placeholder_access_data(
        self,
        db,
        privacy_request,
        mongo_inserts,
        postgres_inserts,
        integration_postgres_config,
        integration_mongodb_config,
    ):
        """Test that erasure tasks are updated with the corresponding erasure data collected
        from the access task"""
        policy = erasure_policy(db, "user.name", "user.contact")
        privacy_request.policy_id = policy.id
        privacy_request.save(db)

        mongo_dataset, postgres_dataset = combined_mongo_postgresql_graph(
            integration_postgres_config, integration_mongodb_config
        )

        graph = DatasetGraph(mongo_dataset, postgres_dataset)

        identity = {"email": mongo_inserts["customer"][0]["email"]}
        traversal: Traversal = Traversal(graph, identity)

        traversal_nodes = {}
        access_end_nodes = traversal.traverse(traversal_nodes, collect_tasks_fn)
        erasure_end_nodes = list(graph.nodes.keys())

        ready_tasks = persist_new_access_request_tasks(
            db,
            privacy_request,
            traversal,
            traversal_nodes,
            access_end_nodes,
            graph,
        )

        persist_initial_erasure_request_tasks(
            db,
            privacy_request,
            traversal_nodes,
            erasure_end_nodes,
            graph,
        )

        run_access_node.delay(
            privacy_request.id, ready_tasks[0].id, privacy_request_proceed=False
        )
        wait_for_tasks_to_complete(db, privacy_request, ActionType.access)

        update_erasure_tasks_with_access_data(db, privacy_request)

        conversations_task = privacy_request.erasure_tasks.filter(
            RequestTask.collection_address == "mongo_test:conversations"
        ).first()
        # Erasure format may save array elements to denote what elements should not be masked while preserving original index
        assert conversations_task.get_data_for_erasures()[1]["thread"] == [
            {
                "comment": "com_0013",
                "message": "should we text Grace when we land or should we just surprise her?",
                "chat_name": "John C",
                "ccn": "123456789",
            },
            "FIDESOPS_DO_NOT_MASK",
            {
                "comment": "com_0015",
                "message": "Aw but she loves surprises.",
                "chat_name": "John C",
                "ccn": "123456789",
            },
            "FIDESOPS_DO_NOT_MASK",
        ]

    @pytest.mark.integration_external
    @pytest.mark.integration_bigquery
    def test_erase_after_database_collections_upstream_and_downstream_tasks(
        self, db, privacy_request, example_datasets, bigquery_connection_config
    ):
        dataset = Dataset(**example_datasets[7])
        initial_graph = convert_dataset_to_graph(
            dataset, bigquery_connection_config.key
        )
        graph = DatasetGraph(*[initial_graph])

        identity = {"email": "customer-1@example.com"}
        traversal: Traversal = Traversal(graph, identity)

        traversal_nodes = {}
        _ = traversal.traverse(traversal_nodes, collect_tasks_fn)
        erasure_end_nodes = list(graph.nodes.keys())

        persist_initial_erasure_request_tasks(
            db,
            privacy_request,
            traversal_nodes,
            erasure_end_nodes,
            graph,
        )

        # Assert "erase_after" caused customer task to run after "address" task
        address_task = privacy_request.erasure_tasks.filter(
            RequestTask.collection_address == "bigquery_example_test_dataset:address"
        ).first()
        assert address_task.downstream_tasks == [
            "bigquery_example_test_dataset:customer"
        ]
        assert address_task.collection["masking_strategy_override"] is None

        customer_task = privacy_request.erasure_tasks.filter(
            RequestTask.collection_address == "bigquery_example_test_dataset:customer"
        ).first()
        assert set(customer_task.upstream_tasks) == {
            "__ROOT__:__ROOT__",
            "bigquery_example_test_dataset:address",
        }

        # Assert erase_after stored on collection on customer task
        assert set(customer_task.collection["erase_after"]) == {
            "__ROOT__:__ROOT__",
            "bigquery_example_test_dataset:address",
        }

        employee_task = privacy_request.erasure_tasks.filter(
            RequestTask.collection_address == "bigquery_example_test_dataset:employee"
        ).first()
        assert employee_task.collection["masking_strategy_override"] == {
            "strategy": "delete"
        }
        # Assert erase_after stored on collection on customer task
        assert employee_task.collection["erase_after"] == []
        assert employee_task.upstream_tasks == ["__ROOT__:__ROOT__"]

    def test_erase_after_saas_upstream_and_downstream_tasks(
        self,
        db,
        privacy_request,
        saas_erasure_order_config,
        saas_erasure_order_connection_config,
        saas_erasure_order_dataset_config,
    ):
        saas_erasure_order_connection_config.update(
            db, data={"saas_config": saas_erasure_order_config}
        )
        merged_graph = saas_erasure_order_dataset_config.get_graph()
        graph = DatasetGraph(merged_graph)

        identity = {"email": "customer-1@example.com"}
        traversal: Traversal = Traversal(graph, identity)

        traversal_nodes = {}
        _ = traversal.traverse(traversal_nodes, collect_tasks_fn)
        erasure_end_nodes = list(graph.nodes.keys())

        persist_initial_erasure_request_tasks(
            db,
            privacy_request,
            traversal_nodes,
            erasure_end_nodes,
            graph,
        )

        orders_task = privacy_request.erasure_tasks.filter(
            RequestTask.collection_address == "saas_erasure_order_instance:orders"
        ).first()
        # These are tasks that are specifically marked as "erase_after"
        assert orders_task.upstream_tasks == [
            "__ROOT__:__ROOT__",
            "saas_erasure_order_instance:orders_to_refunds",
            "saas_erasure_order_instance:refunds_to_orders",
        ]
        assert orders_task.downstream_tasks == ["saas_erasure_order_instance:labels"]
        # Data dependencies are still from the root node
        assert orders_task.traversal_details["input_keys"] == ["__ROOT__:__ROOT__"]
        serialized_collection = orders_task.collection
        assert serialized_collection["name"] == "orders"
        assert len(serialized_collection["fields"]) == 2
        assert serialized_collection["fields"] == [
            {
                "name": "id",
                "length": None,
                "identity": None,
                "is_array": False,
                "read_only": None,
                "references": [],
                "primary_key": True,
                "data_categories": ["system.operations"],
                "data_type_converter": "integer",
                "return_all_elements": None,
                "custom_request_field": None,
                "masking_strategy_override": None,
            },
            {
                "name": "email",
                "length": None,
                "identity": "email",
                "is_array": False,
                "read_only": None,
                "references": [],
                "primary_key": False,
                "data_categories": None,
                "data_type_converter": "None",
                "return_all_elements": None,
                "custom_request_field": None,
                "masking_strategy_override": None,
            },
        ]
        assert not serialized_collection["skip_processing"]
        assert serialized_collection["grouped_inputs"] == []
        assert set(serialized_collection["erase_after"]) == {
            "saas_erasure_order_instance:orders_to_refunds",
            "saas_erasure_order_instance:refunds_to_orders",
            "__ROOT__:__ROOT__",
        }

        refunds_task = privacy_request.erasure_tasks.filter(
            RequestTask.collection_address == "saas_erasure_order_instance:refunds"
        ).first()
        # These are tasks that are specifically marked as "erase_after"
        assert refunds_task.upstream_tasks == [
            "__ROOT__:__ROOT__",
            "saas_erasure_order_instance:orders_to_refunds",
            "saas_erasure_order_instance:refunds_to_orders",
        ]
        assert refunds_task.downstream_tasks == ["saas_erasure_order_instance:labels"]

        labels_task = privacy_request.erasure_tasks.filter(
            RequestTask.collection_address == "saas_erasure_order_instance:labels"
        ).first()
        # Data dependencies are still from the root node
        assert labels_task.traversal_details["input_keys"] == ["__ROOT__:__ROOT__"]
        # These are tasks that are specifically marked as "erase_after"
        assert labels_task.upstream_tasks == [
            "__ROOT__:__ROOT__",
            "saas_erasure_order_instance:orders",
            "saas_erasure_order_instance:refunds",
        ]
        assert labels_task.downstream_tasks == ["__TERMINATE__:__TERMINATE__"]

        orders_to_refunds = privacy_request.erasure_tasks.filter(
            RequestTask.collection_address
            == "saas_erasure_order_instance:orders_to_refunds"
        ).first()
        # Data dependencies are from orders node though
        assert orders_to_refunds.traversal_details["input_keys"] == [
            "saas_erasure_order_instance:orders"
        ]
        assert orders_to_refunds.upstream_tasks == ["__ROOT__:__ROOT__"]
        assert orders_to_refunds.downstream_tasks == [
            "saas_erasure_order_instance:orders",
            "saas_erasure_order_instance:refunds",
        ]

        refunds_to_order = privacy_request.erasure_tasks.filter(
            RequestTask.collection_address
            == "saas_erasure_order_instance:refunds_to_orders"
        ).first()
        # Data dependencies are refunds node though
        assert refunds_to_order.traversal_details["input_keys"] == [
            "saas_erasure_order_instance:refunds"
        ]
        assert refunds_to_order.upstream_tasks == ["__ROOT__:__ROOT__"]
        assert refunds_to_order.downstream_tasks == [
            "saas_erasure_order_instance:orders",
            "saas_erasure_order_instance:refunds",
        ]

        products = privacy_request.erasure_tasks.filter(
            RequestTask.collection_address == "saas_erasure_order_instance:products"
        ).first()
        # Data dependencies are still from the root node
        assert products.traversal_details["input_keys"] == ["__ROOT__:__ROOT__"]
        # These are tasks that are specifically marked as "erase_after"
        assert products.upstream_tasks == ["__ROOT__:__ROOT__"]
        assert products.downstream_tasks == ["__TERMINATE__:__TERMINATE__"]

    def test_erase_after_incorrectly_creates_cycle(
        self,
        db,
        privacy_request,
        saas_erasure_order_config,
        saas_erasure_order_connection_config,
        saas_erasure_order_dataset_config,
    ):
        dataset_name = saas_erasure_order_connection_config.get_saas_config().fides_key
        saas_erasure_order_config["endpoints"][0]["erase_after"].append(
            f"{dataset_name}.labels"
        )
        saas_erasure_order_connection_config.update(
            db, data={"saas_config": saas_erasure_order_config}
        )
        merged_graph = saas_erasure_order_dataset_config.get_graph()
        graph = DatasetGraph(merged_graph)

        identity = {"email": "customer-1@example.com"}
        traversal: Traversal = Traversal(graph, identity)

        traversal_nodes = {}
        _ = traversal.traverse(traversal_nodes, collect_tasks_fn)
        erasure_end_nodes = list(graph.nodes.keys())

        with pytest.raises(TraversalError):
            persist_initial_erasure_request_tasks(
                db,
                privacy_request,
                traversal_nodes,
                erasure_end_nodes,
                graph,
            )

    def test_no_collections(self, db, privacy_request):
        identity = {"email": "customer-1@example.com"}

        graph = DatasetGraph()

        traversal: Traversal = Traversal(graph, identity)

        traversal_nodes = {}
        _ = traversal.traverse(traversal_nodes, collect_tasks_fn)
        erasure_end_nodes = list(graph.nodes.keys())
        ready_tasks = persist_initial_erasure_request_tasks(
            db,
            privacy_request,
            traversal_nodes,
            erasure_end_nodes,
            graph,
        )

        assert len(ready_tasks) == 0
        db.refresh(privacy_request)

        assert len(privacy_request.erasure_tasks.all()) == 2
        assert privacy_request.erasure_tasks[0].is_root_task
        assert privacy_request.erasure_tasks[0].upstream_tasks == []
        assert privacy_request.erasure_tasks[0].downstream_tasks == [
            TERMINATOR_ADDRESS.value
        ]

        assert privacy_request.erasure_tasks[1].is_terminator_task
        assert privacy_request.erasure_tasks[1].upstream_tasks == [
            ROOT_COLLECTION_ADDRESS.value
        ]
        assert privacy_request.erasure_tasks[1].downstream_tasks == []

    @mock.patch(
        "fides.api.task.create_request_tasks.update_erasure_tasks_with_access_data",
    )
    @mock.patch(
        "fides.api.task.create_request_tasks.queue_request_task",
    )
    def test_run_erasure_request_with_existing_request_tasks(
        self,
        run_erasure_node_mock,
        update_erasure_tasks_with_access_data_mock,
        request_task,
        erasure_request_task,
        db,
        privacy_request,
        policy,
    ):
        assert privacy_request.access_tasks.count() == 3
        assert privacy_request.erasure_tasks.count() == 3

        # The ready tasks here are all the nodes connected to the erasure node
        ready = run_erasure_request(
            privacy_request,
            db,
            privacy_request_proceed=False,
        )

        assert len(ready) == 1
        ready_task = ready[0]
        assert not ready_task.is_root_task
        assert ready_task == erasure_request_task

        assert ready_task.status == ExecutionLogStatus.pending
        assert ready_task.action_type == ActionType.erasure

        assert update_erasure_tasks_with_access_data_mock.called
        update_erasure_tasks_with_access_data_mock.called_with(db, privacy_request)
        assert run_erasure_node_mock.called
        run_erasure_node_mock.assert_called_with(erasure_request_task, False)


class TestPersistConsentRequestTasks:
    def test_persist_new_consent_request_tasks(
        self,
        db,
        privacy_request,
        saas_example_dataset_config,
    ):
        graph = build_consent_dataset_graph([saas_example_dataset_config])

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
            "saas_connector_example:saas_connector_example"
        ]
        assert root_task.all_descendant_tasks == [
            "__TERMINATE__:__TERMINATE__",
            "saas_connector_example:saas_connector_example",
        ]
        assert root_task.status == ExecutionLogStatus.complete
        assert root_task.access_data == [{"ga_client_id": "test_id"}]
        assert root_task.get_access_data() == [{"ga_client_id": "test_id"}]
        terminator_task = privacy_request.get_terminate_task_by_action(
            ActionType.consent
        )

        assert terminator_task.is_terminator_task
        assert terminator_task.action_type == ActionType.consent
        assert terminator_task.upstream_tasks == [
            "saas_connector_example:saas_connector_example"
        ]
        assert terminator_task.downstream_tasks == []
        assert terminator_task.all_descendant_tasks == []
        assert terminator_task.status == ExecutionLogStatus.pending

        ga_task = privacy_request.consent_tasks.filter(
            RequestTask.collection_address
            == "saas_connector_example:saas_connector_example",
        ).first()
        assert not ga_task.is_root_task
        assert not ga_task.is_terminator_task
        assert ga_task.action_type == ActionType.consent
        # Consent nodes have no data dependencies - they just have the root upstream
        # and the terminate node downstream
        assert ga_task.upstream_tasks == ["__ROOT__:__ROOT__"]
        assert ga_task.downstream_tasks == ["__TERMINATE__:__TERMINATE__"]
        assert ga_task.all_descendant_tasks == ["__TERMINATE__:__TERMINATE__"]
        assert ga_task.status == ExecutionLogStatus.pending

        # The collection is a fake one for Consent, since requests happen at the dataset level
        assert ga_task.collection == {
            "name": "saas_connector_example",
            "after": [],
            "fields": [],
            "erase_after": [],
            "partitioning": None,
            "grouped_inputs": [],
            "data_categories": [],
            "skip_processing": False,
            "masking_strategy_override": None,
        }
        assert ga_task.traversal_details == {
            "input_keys": [],
            "incoming_edges": [],
            "outgoing_edges": [],
            "dataset_connection_key": "saas_connector_example",
            "skipped_nodes": None,
        }

    @mock.patch(
        "fides.api.task.create_request_tasks.queue_request_task",
    )
    def test_run_consent_request_no_request_tasks_existing(
        self, run_consent_node_mock, db, privacy_request, policy
    ):
        ready = run_consent_request(
            privacy_request,
            DatasetGraph(),
            {"email": "customer-4@example.com"},
            db,
            privacy_request_proceed=False,
        )

        assert len(ready) == 1
        root_task = ready[0]
        assert root_task.is_root_task

        assert run_consent_node_mock.called
        run_consent_node_mock.assert_called_with(root_task, False)

    @mock.patch(
        "fides.api.task.create_request_tasks.queue_request_task",
    )
    def test_reprocess_consent_request_with_existing_request_tasks(
        self, run_consent_node_mock, consent_request_task, db, privacy_request, policy
    ):
        assert privacy_request.consent_tasks.count() == 3

        ready = run_consent_request(
            privacy_request,
            DatasetGraph(),
            {"email": "customer-4@example.com"},
            db,
            privacy_request_proceed=False,
        )

        assert len(ready) == 1
        ready_task = ready[0]
        assert ready_task == consent_request_task
        assert not ready_task.is_root_task
        assert ready_task.action_type == ActionType.consent
        assert ready_task.status == ExecutionLogStatus.pending

        assert run_consent_node_mock.called
        run_consent_node_mock.assert_called_with(consent_request_task, False)

        # No new consent tasks created
        assert privacy_request.consent_tasks.count() == 3


class TestGetExistingReadyTasks:
    def test_no_request_tasks(self, privacy_request, db):
        assert get_existing_ready_tasks(db, privacy_request, ActionType.access) == []

    def test_task_should_be_same_action_type(self, privacy_request, db):
        rt = RequestTask.create(
            db,
            data={
                "privacy_request_id": privacy_request.id,
                "collection_address": "dataset:collection",
                "collection_name": "collection",
                "dataset_name": "dataset",
                "action_type": ActionType.erasure,
                "status": "pending",
            },
        )
        assert get_existing_ready_tasks(db, privacy_request, ActionType.access) == []
        rt.delete(db)

    def test_task_must_be_incomplete(self, privacy_request, db):
        rt = RequestTask.create(
            db,
            data={
                "privacy_request_id": privacy_request.id,
                "collection_address": "dataset:collection",
                "collection_name": "collection",
                "dataset_name": "dataset",
                "action_type": ActionType.erasure,
                "status": "complete",
            },
        )
        assert get_existing_ready_tasks(db, privacy_request, ActionType.access) == []
        rt.delete(db)

    def test_task_needs_to_have_upstream_complete(self, privacy_request, db):
        upstream = RequestTask.create(
            db,
            data={
                "privacy_request_id": privacy_request.id,
                "collection_address": "dataset:other_collection",
                "collection_name": "other_collection",
                "dataset_name": "dataset",
                "action_type": ActionType.access,
                "status": "pending",
                "upstream_tasks": [],
            },
        )
        rt = RequestTask.create(
            db,
            data={
                "privacy_request_id": privacy_request.id,
                "collection_address": "dataset:collection",
                "collection_name": "collection",
                "dataset_name": "dataset",
                "action_type": ActionType.access,
                "status": "pending",
                "upstream_tasks": [upstream.collection_address],
            },
        )
        # rt is not ready but upstream is
        assert get_existing_ready_tasks(db, privacy_request, ActionType.access) == [
            upstream
        ]
        rt.delete(db)

    def test_error_status_is_marked_as_pending(self, privacy_request, db):
        upstream = RequestTask.create(
            db,
            data={
                "privacy_request_id": privacy_request.id,
                "collection_address": "dataset:other_collection",
                "collection_name": "other_collection",
                "dataset_name": "dataset",
                "action_type": ActionType.access,
                "status": "pending",
                "upstream_tasks": [],
            },
        )
        rt = RequestTask.create(
            db,
            data={
                "privacy_request_id": privacy_request.id,
                "collection_address": "dataset:collection",
                "collection_name": "collection",
                "dataset_name": "dataset",
                "action_type": ActionType.access,
                "status": "error",
                "upstream_tasks": [upstream.collection_address],
            },
        )
        # rt is not ready but upstream is
        assert get_existing_ready_tasks(db, privacy_request, ActionType.access) == [
            upstream
        ]
        db.refresh(rt)
        # The current "errored" task is marked as pending, even if its upstream
        # tasks aren't ready
        assert rt.status == ExecutionLogStatus.pending
        upstream.delete(db)
        rt.delete(db)

    def test_ready_tasks(self, privacy_request, db):
        rt = RequestTask.create(
            db,
            data={
                "privacy_request_id": privacy_request.id,
                "collection_address": "dataset:collection",
                "collection_name": "collection",
                "dataset_name": "dataset",
                "action_type": ActionType.access,
                "status": "pending",
            },
        )
        assert get_existing_ready_tasks(db, privacy_request, ActionType.access) == [rt]


class TestRunAccessRequestWithRequestTasks:
    @pytest.mark.timeout(5)
    @pytest.mark.integration
    @pytest.mark.integration_postgres
    @pytest.mark.integration_mongodb
    def test_run_access_request(
        self,
        db,
        privacy_request,
        policy,
        mongo_inserts,
        postgres_inserts,
        postgres_integration_db,
        integration_mongodb_config_with_dataset,
        integration_postgres_config_with_dataset,
    ):
        # uses a fixture that also creates the dataset config for more realistic testing
        integration_postgres_config = integration_postgres_config_with_dataset
        integration_mongodb_config = integration_mongodb_config_with_dataset

        mongo_dataset = integration_mongodb_config.datasets[0].get_graph()
        postgres_dataset = integration_postgres_config.datasets[0].get_graph()

        graph = DatasetGraph(mongo_dataset, postgres_dataset)

        identity = {"email": mongo_inserts["customer"][0]["email"]}

        run_access_request(
            privacy_request,
            policy,
            graph,
            [
                integration_mongodb_config_with_dataset,
                integration_postgres_config_with_dataset,
            ],
            identity,
            db,
            privacy_request_proceed=True,
        )
        wait_for_tasks_to_complete(db, privacy_request, ActionType.access)

        assert privacy_request.access_tasks.count() == 16
        assert privacy_request.erasure_tasks.count() == 0

        all_access_tasks = privacy_request.access_tasks.all()

        assert {t.collection_address for t in all_access_tasks} == {
            "__ROOT__:__ROOT__",
            "mongo_test:customer_feedback",
            "postgres_example:customer",
            "mongo_test:internal_customer_profile",
            "mongo_test:address",
            "postgres_example:orders",
            "mongo_test:orders",
            "mongo_test:customer_details",
            "mongo_test:rewards",
            "postgres_example:payment_card",
            "mongo_test:conversations",
            "mongo_test:flights",
            "postgres_example:address",
            "mongo_test:aircraft",
            "mongo_test:employee",
            "__TERMINATE__:__TERMINATE__",
        }
        assert all(t.status == ExecutionLogStatus.complete for t in all_access_tasks)
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.complete

        raw_access_results = privacy_request.get_raw_access_results()

        # Two addresses being found tests that our input_keys are working properly
        assert [
            address["id"] for address in raw_access_results["postgres_example:address"]
        ] == [1000, 1002]

        customer_details = raw_access_results["mongo_test:customer_details"][0]
        assert customer_details["customer_id"] == 10000
        assert customer_details["gender"] == "male"
        assert customer_details["birthday"] == datetime(1988, 1, 10, 0, 0)
        assert customer_details["workplace_info"] == {
            "employer": "Green Tea Company",
            "position": "Head Grower",
            "direct_reports": ["Margo Robbins"],
        }
        assert customer_details["emergency_contacts"] == [
            {
                "name": "Grace Customer",
                "relationship": "mother",
                "phone": "123-456-7890",
            },
            {
                "name": "Joseph Customer",
                "relationship": "brother",
                "phone": "000-000-0000",
            },
        ]
        assert customer_details["children"] == ["Kent Customer", "Kenny Customer"]

    @pytest.mark.timeout(5)
    @pytest.mark.integration
    @pytest.mark.integration_postgres
    @pytest.mark.integration_mongodb
    def test_run_access_request_with_error(
        self,
        db,
        privacy_request,
        policy,
        mongo_inserts,
        postgres_inserts,
        integration_mongodb_config_with_dataset,
        integration_postgres_config_with_dataset,
    ):
        # uses a fixture that also creates the dataset config for more realistic testing
        integration_postgres_config = integration_postgres_config_with_dataset
        integration_mongodb_config = integration_mongodb_config_with_dataset

        mongo_dataset = integration_mongodb_config.datasets[0].get_graph()
        postgres_dataset = integration_postgres_config.datasets[0].get_graph()

        graph = DatasetGraph(mongo_dataset, postgres_dataset)

        identity = {"email": mongo_inserts["customer"][0]["email"]}

        # Temporarily remove the secrets from the mongo connection to prevent execution from occurring
        saved_secrets = integration_mongodb_config.secrets
        integration_mongodb_config.secrets = {}
        integration_mongodb_config.save(db)

        run_access_request(
            privacy_request,
            policy,
            graph,
            [integration_postgres_config, integration_mongodb_config],
            identity,
            db,
            privacy_request_proceed=True,
        )
        wait_for_tasks_to_complete(db, privacy_request, ActionType.access)

        assert privacy_request.access_tasks.count() == 16
        assert privacy_request.erasure_tasks.count() == 0

        postgres_customer_task = privacy_request.access_tasks.filter(
            RequestTask.collection_address == "postgres_example:address"
        ).first()
        customer_task_updated = postgres_customer_task.updated_at

        mongo_flights_task = privacy_request.access_tasks.filter(
            RequestTask.collection_address == "mongo_test:flights"
        ).first()
        mongo_flights_task_updated = mongo_flights_task.updated_at

        # Mongo tasks are marked as error but the postgres tasks are still
        # able to complete.
        task_statuses = {
            request_task.collection_address: request_task.status.value
            for request_task in privacy_request.access_tasks
        }
        assert task_statuses == {
            "__ROOT__:__ROOT__": "complete",
            "mongo_test:customer_feedback": "error",
            "postgres_example:customer": "complete",
            "mongo_test:internal_customer_profile": "error",
            "mongo_test:orders": "error",
            "mongo_test:customer_details": "error",
            "mongo_test:address": "error",
            "postgres_example:orders": "complete",
            "mongo_test:rewards": "error",
            "mongo_test:flights": "error",
            "mongo_test:conversations": "error",
            "postgres_example:payment_card": "complete",
            "mongo_test:aircraft": "error",
            "mongo_test:employee": "error",
            "postgres_example:address": "complete",
            "__TERMINATE__:__TERMINATE__": "error",
        }

        integration_mongodb_config.secrets = saved_secrets
        integration_mongodb_config.save(db)

        run_access_request(
            privacy_request,
            policy,
            graph,
            [integration_postgres_config, integration_mongodb_config],
            {"email": mongo_inserts["customer"][0]["email"]},
            db,
            privacy_request_proceed=True,
        )
        wait_for_tasks_to_complete(db, privacy_request, ActionType.access)

        # No new tasks were created - we just updated the statuses of the old ones
        assert privacy_request.access_tasks.count() == 16
        assert privacy_request.erasure_tasks.count() == 0

        assert all(
            t.status == ExecutionLogStatus.complete
            for t in privacy_request.access_tasks
        )
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.complete

        # These results are not yet filtered by data category
        raw_results = privacy_request.get_raw_access_results()

        # Selected postgres results - retrieved first pass
        customer_info = raw_results["postgres_example:customer"][0]
        assert customer_info["id"] == 10000
        assert customer_info["email"] == "test_one@example.com"
        assert customer_info["address_id"] == 1000

        # Existing task was unchanged on re-run because it was already completed
        db.refresh(postgres_customer_task)
        assert postgres_customer_task.updated_at == customer_task_updated

        # Selected Mongo results - retrieved second pass
        flight_info = raw_results["mongo_test:flights"][0]
        assert flight_info["passenger_information"] == {
            "passenger_ids": ["D222-22221"],
            "full_name": "John Customer",
        }
        assert flight_info["flight_no"] == "AA230"
        assert flight_info["pilots"] == ["3", "4"]
        # Existing task was modified
        db.refresh(mongo_flights_task)
        assert mongo_flights_task.updated_at > mongo_flights_task_updated


class TestRunErasureRequestWithRequestTasks:
    @pytest.mark.timeout(15)
    @pytest.mark.integration
    @pytest.mark.integration_postgres
    @pytest.mark.integration_mongodb
    def test_run_erasure_request(
        self,
        db,
        mongo_inserts,
        postgres_inserts,
        privacy_request_with_erasure_policy,
        erasure_policy,
        example_datasets,
        postgres_integration_db,
        integration_mongodb_config,
        integration_postgres_config,
    ):
        """Large test handling access and erasure with a failed erasure step"""
        mongo_dataset, postgres_dataset = combined_mongo_postgresql_graph(
            integration_postgres_config, integration_mongodb_config
        )

        field(
            [mongo_dataset], "mongo_test", "conversations", "thread", "chat_name"
        ).data_categories = ["user.name"]
        field(
            [postgres_dataset], "postgres_example", "customer", "name"
        ).data_categories = ["user.name"]
        field(
            [mongo_dataset],
            "mongo_test",
            "customer_details",
            "workplace_info",
            "direct_reports",
        ).data_categories = ["user.name"]
        field(
            [mongo_dataset],
            "mongo_test",
            "customer_details",
            "emergency_contacts",
            "name",
        ).data_categories = ["user.name"]
        field(
            [mongo_dataset],
            "mongo_test",
            "flights",
            "passenger_information",
            "full_name",
        ).data_categories = ["user.name"]
        field([mongo_dataset], "mongo_test", "employee", "name").data_categories = [
            "user.name"
        ]

        graph = DatasetGraph(mongo_dataset, postgres_dataset)

        identity = {"email": mongo_inserts["customer"][0]["email"]}

        CONFIG.execution.task_retry_count = 0
        CONFIG.execution.task_retry_delay = 0.1
        CONFIG.execution.task_retry_backoff = 0.01
        p = mock.patch(
            "fides.api.service.connectors.MongoDBConnector.mask_data",
            new=MagicMock(side_effect=Exception("Key Error")),
        )
        p.start()

        assert privacy_request_with_erasure_policy.access_tasks.count() == 0
        assert privacy_request_with_erasure_policy.erasure_tasks.count() == 0

        run_access_request(
            privacy_request_with_erasure_policy,
            erasure_policy,
            graph,
            [integration_postgres_config, integration_mongodb_config],
            identity,
            db,
            privacy_request_proceed=False,
        )
        wait_for_tasks_to_complete(
            db, privacy_request_with_erasure_policy, ActionType.access
        )
        assert privacy_request_with_erasure_policy.access_tasks.count() == 16
        # These were created preemptively alongside the access request tasks so they match
        assert privacy_request_with_erasure_policy.erasure_tasks.count() == 16

        # Run erasure portion first time, but it is expected to fail because
        # Mongo connector is not working
        run_erasure_request(
            privacy_request_with_erasure_policy, db, privacy_request_proceed=False
        )
        wait_for_tasks_to_complete(
            db, privacy_request_with_erasure_policy, ActionType.erasure
        )

        postgres_customer_task = (
            privacy_request_with_erasure_policy.erasure_tasks.filter(
                RequestTask.collection_address == "postgres_example:address"
            ).first()
        )
        customer_task_updated = postgres_customer_task.updated_at

        mongo_flights_task = privacy_request_with_erasure_policy.erasure_tasks.filter(
            RequestTask.collection_address == "mongo_test:flights"
        ).first()
        mongo_flights_task_updated = mongo_flights_task.updated_at

        # Mongo tasks are marked as error but the postgres tasks are still
        # able to complete.
        db.refresh(privacy_request_with_erasure_policy)
        task_statuses = {
            request_task.collection_address: request_task.status.value
            for request_task in privacy_request_with_erasure_policy.erasure_tasks
        }
        assert task_statuses == {
            "__ROOT__:__ROOT__": "complete",
            "mongo_test:internal_customer_profile": "error",
            "mongo_test:rewards": "error",
            "postgres_example:customer": "complete",
            "mongo_test:customer_feedback": "error",
            "mongo_test:employee": "error",
            "mongo_test:address": "error",
            "postgres_example:payment_card": "complete",
            "mongo_test:orders": "error",
            "mongo_test:customer_details": "error",
            "postgres_example:orders": "complete",
            "postgres_example:address": "complete",
            "mongo_test:flights": "error",
            "mongo_test:conversations": "error",
            "mongo_test:aircraft": "error",
            "__TERMINATE__:__TERMINATE__": "error",
        }

        # Stop mocking MongoDBConnector.mask_data
        p.stop()

        # Run erasure one more time
        run_erasure_request(
            privacy_request_with_erasure_policy, db, privacy_request_proceed=False
        )
        wait_for_tasks_to_complete(
            db, privacy_request_with_erasure_policy, ActionType.erasure
        )

        assert all(
            t.status == ExecutionLogStatus.complete
            for t in privacy_request_with_erasure_policy.erasure_tasks
        )

        rows_masked = privacy_request_with_erasure_policy.get_raw_masking_counts()

        # Existing completed task was not touched on Run #2
        db.refresh(postgres_customer_task)
        assert postgres_customer_task.updated_at == customer_task_updated

        # Existing error task was modified on run #2
        db.refresh(mongo_flights_task)
        assert mongo_flights_task.updated_at > mongo_flights_task_updated

        # No new tasks were created
        assert privacy_request_with_erasure_policy.erasure_tasks.count() == 16

        assert rows_masked == {
            "mongo_test:rewards": 0,
            "mongo_test:customer_feedback": 0,
            "postgres_example:customer": 1,
            "mongo_test:employee": 2,
            "mongo_test:internal_customer_profile": 0,
            "postgres_example:payment_card": 0,
            "mongo_test:address": 0,
            "mongo_test:orders": 0,
            "postgres_example:orders": 0,
            "postgres_example:address": 0,
            "mongo_test:customer_details": 1,
            "mongo_test:conversations": 2,
            "mongo_test:flights": 1,
            "mongo_test:aircraft": 0,
        }

        # Remove request tasks and re-run access request
        db.query(RequestTask).filter(
            RequestTask.privacy_request_id == privacy_request_with_erasure_policy.id
        ).delete()
        run_access_request(
            privacy_request_with_erasure_policy,
            erasure_policy,
            graph,
            [integration_postgres_config, integration_mongodb_config],
            identity,
            db,
            privacy_request_proceed=False,
        )
        wait_for_tasks_to_complete(
            db, privacy_request_with_erasure_policy, ActionType.access
        )
        raw_access_results = (
            privacy_request_with_erasure_policy.get_raw_access_results()
        )
        # erasure policy targeted names with null rewrite strategy
        assert raw_access_results["postgres_example:customer"][0]["name"] is None
        assert (
            raw_access_results["mongo_test:conversations"][0]["thread"][0]["chat_name"]
            is None
        )
        assert (
            raw_access_results["mongo_test:conversations"][1]["thread"][0]["chat_name"]
            is None
        )
        assert (
            raw_access_results["mongo_test:conversations"][1]["thread"][1]["chat_name"]
            is None
        )
        assert raw_access_results["mongo_test:employee"][0]["name"] is None
        assert raw_access_results["mongo_test:employee"][1]["name"] is None
        assert raw_access_results["mongo_test:customer_details"][0]["workplace_info"][
            "direct_reports"
        ] == [None]
        assert not raw_access_results["mongo_test:customer_details"][0][
            "emergency_contacts"
        ][0]["name"]
        assert not raw_access_results["mongo_test:customer_details"][0][
            "emergency_contacts"
        ][1]["name"]
        assert not raw_access_results["mongo_test:flights"][0]["passenger_information"][
            "full_name"
        ]
