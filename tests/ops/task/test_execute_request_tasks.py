import pytest

from fides.api.common_exceptions import (
    PrivacyRequestNotFound,
    RequestTaskNotFound,
    ResumeTaskException,
    UpstreamTasksNotReady,
)
from fides.api.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    Collection,
    CollectionAddress,
    FieldAddress,
)
from fides.api.graph.execution import ExecutionNode
from fides.api.graph.graph import DatasetGraph, Edge
from fides.api.graph.traversal import Traversal
from fides.api.models.privacy_request import ExecutionLogStatus, RequestTask
from fides.api.schemas.policy import ActionType
from fides.api.service.connectors import PostgreSQLConnector
from fides.api.task.create_request_tasks import (
    collect_tasks_fn,
    persist_new_access_request_tasks,
)
from fides.api.task.execute_request_tasks import (
    can_run_task_body,
    create_graph_task,
    run_prerequisite_task_checks,
)


@pytest.fixture()
def create_postgres_access_request_tasks(postgres_dataset_graph, db, privacy_request):
    identity = {"email": "customer-1@example.com"}
    traversal: Traversal = Traversal(postgres_dataset_graph, identity)
    traversal_nodes = {}
    end_nodes = traversal.traverse(traversal_nodes, collect_tasks_fn)

    _ = persist_new_access_request_tasks(
        db,
        privacy_request,
        traversal,
        traversal_nodes,
        end_nodes,
        postgres_dataset_graph,
    )


class TestRunPrerequisiteTaskChecks:
    def test_privacy_request_does_not_exist(self, db):
        with pytest.raises(PrivacyRequestNotFound):
            run_prerequisite_task_checks(db, "12345", "12345")

    def test_request_task_does_not_exist(self, db, privacy_request):
        with pytest.raises(RequestTaskNotFound):
            run_prerequisite_task_checks(db, privacy_request.id, "12345")

    @pytest.mark.usefixtures("request_task")
    def test_upstream_tasks_not_complete(self, db, privacy_request):
        terminator_task = privacy_request.access_tasks.filter(
            RequestTask.collection_address == TERMINATOR_ADDRESS.value
        ).first()

        with pytest.raises(UpstreamTasksNotReady):
            # Upstream request task is not ready
            run_prerequisite_task_checks(db, privacy_request.id, terminator_task.id)

    def test_upstream_tasks_complete(self, db, privacy_request, request_task):
        # Root task is completed so downstream request task can run
        root_task = privacy_request.access_tasks.filter(
            RequestTask.collection_address == ROOT_COLLECTION_ADDRESS.value
        ).first()
        pr, rt, ur = run_prerequisite_task_checks(
            db, privacy_request.id, request_task.id
        )
        assert pr == privacy_request
        assert rt == request_task
        assert ur.all() == [root_task]

        # Request task is skipped so downstream terminator task can run
        terminator_task = privacy_request.access_tasks.filter(
            RequestTask.collection_address == TERMINATOR_ADDRESS.value
        ).first()
        request_task.update_status(db, ExecutionLogStatus.skipped)

        pr, rt, ur = run_prerequisite_task_checks(
            db, privacy_request.id, terminator_task.id
        )
        assert ur.all() == [request_task]


class TestCreateGraphTask:
    @pytest.mark.usefixtures("create_postgres_access_request_tasks")
    def test_create_graph_task(self, db, privacy_request):
        """Request Tasks from the database can be re-hydrated into Graph Tasks"""

        request_task = privacy_request.access_tasks.filter(
            RequestTask.collection_address == "postgres_example_test_dataset:address"
        ).first()

        graph_task = create_graph_task(db, request_task)

        assert graph_task.request_task == request_task
        assert graph_task.key == CollectionAddress.from_string(
            "postgres_example_test_dataset:address"
        )

        execution_node = graph_task.execution_node
        assert isinstance(execution_node.collection, Collection)
        assert execution_node.address == CollectionAddress.from_string(
            "postgres_example_test_dataset:address"
        )
        assert isinstance(graph_task.connector, PostgreSQLConnector)

    @pytest.mark.usefixtures("create_postgres_access_request_tasks")
    def test_error_hydrating_graph_task(self, db, privacy_request):
        """If GraphTask cannot be hydrated, error is thrown, current task and downstream tasks
        are marked as error and execution log created for current node

        Normally the Graph Task would take care of this, but in this case, we couldn't create
        the graph task in the first place
        """

        request_task = privacy_request.access_tasks.filter(
            RequestTask.collection_address == "postgres_example_test_dataset:address"
        ).first()
        # Set required field to None on RequestTask.collection
        request_task.collection["name"] = None
        request_task.save(db)

        with pytest.raises(ResumeTaskException):
            create_graph_task(db, request_task)

        db.refresh(request_task)

        downstream_task = privacy_request.access_tasks.filter(
            RequestTask.collection_address == request_task.downstream_tasks[0]
        ).first()
        assert downstream_task.status == ExecutionLogStatus.error

        execution_log = privacy_request.execution_logs.first()
        assert execution_log.dataset_name == "postgres_example_test_dataset"
        assert execution_log.collection_name == "address"
        assert execution_log.action_type == ActionType.access
        assert execution_log.status == ExecutionLogStatus.error


class TestExecutionNode:
    @pytest.fixture()
    @pytest.mark.usefixtures("create_postgres_access_request_tasks")
    def address_execution_node(
        self, privacy_request, create_postgres_access_request_tasks
    ):
        request_task = privacy_request.access_tasks.filter(
            RequestTask.collection_address == "postgres_example_test_dataset:address"
        ).first()

        execution_node = ExecutionNode(request_task)
        return execution_node

    @pytest.fixture()
    @pytest.mark.usefixtures("create_postgres_access_request_tasks")
    def employee_execution_node(
        self, privacy_request, create_postgres_access_request_tasks
    ):
        request_task = privacy_request.access_tasks.filter(
            RequestTask.collection_address == "postgres_example_test_dataset:employee"
        ).first()

        execution_node = ExecutionNode(request_task)
        return execution_node

    def test_collection_address(self, address_execution_node):
        assert isinstance(address_execution_node.collection, Collection)
        assert address_execution_node.address == CollectionAddress.from_string(
            "postgres_example_test_dataset:address"
        )

    def test_incoming_edges(self, address_execution_node):
        """Assert incoming edges are hydrated from the Traversal details saved on the Request Task"""
        assert address_execution_node.incoming_edges == {
            Edge(
                FieldAddress.from_string(
                    "postgres_example_test_dataset:payment_card:billing_address_id"
                ),
                FieldAddress.from_string("postgres_example_test_dataset:address:id"),
            ),
            Edge(
                FieldAddress.from_string(
                    "postgres_example_test_dataset:customer:address_id"
                ),
                FieldAddress.from_string("postgres_example_test_dataset:address:id"),
            ),
            Edge(
                FieldAddress.from_string(
                    "postgres_example_test_dataset:orders:shipping_address_id"
                ),
                FieldAddress.from_string("postgres_example_test_dataset:address:id"),
            ),
            Edge(
                FieldAddress.from_string(
                    "postgres_example_test_dataset:employee:address_id"
                ),
                FieldAddress.from_string("postgres_example_test_dataset:address:id"),
            ),
        }
        assert address_execution_node.outgoing_edges == set()

    def test_input_keys(self, address_execution_node):
        """Assert input keys are hydrated from the Traversal details saved on the Request Task"""

        assert address_execution_node.input_keys == [
            CollectionAddress.from_string("postgres_example_test_dataset:customer"),
            CollectionAddress.from_string("postgres_example_test_dataset:employee"),
            CollectionAddress.from_string("postgres_example_test_dataset:orders"),
            CollectionAddress.from_string("postgres_example_test_dataset:payment_card"),
        ]

    def test_outgoing_edges(self, employee_execution_node):
        """Assert outgoing edges are hydrated from the Traversal details saved on the Request Task"""

        assert employee_execution_node.outgoing_edges == {
            Edge(
                FieldAddress.from_string("postgres_example_test_dataset:employee:id"),
                FieldAddress.from_string(
                    "postgres_example_test_dataset:service_request:employee_id"
                ),
            ),
            Edge(
                FieldAddress.from_string(
                    "postgres_example_test_dataset:employee:address_id"
                ),
                FieldAddress.from_string("postgres_example_test_dataset:address:id"),
            ),
        }

    def test_incoming_edges_by_collection(self, address_execution_node):
        """Assert incoming_edges_from_collection are built from incoming edges saved on the traversal details"""
        assert address_execution_node.incoming_edges_by_collection == {
            CollectionAddress.from_string("postgres_example_test_dataset:customer"): [
                Edge(
                    FieldAddress.from_string(
                        "postgres_example_test_dataset:customer:address_id"
                    ),
                    FieldAddress.from_string(
                        "postgres_example_test_dataset:address:id"
                    ),
                )
            ],
            CollectionAddress.from_string(
                "postgres_example_test_dataset:payment_card"
            ): [
                Edge(
                    FieldAddress.from_string(
                        "postgres_example_test_dataset:payment_card:billing_address_id"
                    ),
                    FieldAddress.from_string(
                        "postgres_example_test_dataset:address:id"
                    ),
                )
            ],
            CollectionAddress.from_string("postgres_example_test_dataset:orders"): [
                Edge(
                    FieldAddress.from_string(
                        "postgres_example_test_dataset:orders:shipping_address_id"
                    ),
                    FieldAddress.from_string(
                        "postgres_example_test_dataset:address:id"
                    ),
                )
            ],
            CollectionAddress.from_string("postgres_example_test_dataset:employee"): [
                Edge(
                    FieldAddress.from_string(
                        "postgres_example_test_dataset:employee:address_id"
                    ),
                    FieldAddress.from_string(
                        "postgres_example_test_dataset:address:id"
                    ),
                )
            ],
        }

    @pytest.mark.usefixtures("sentry_connection_config_without_secrets")
    def test_grouped_fields(
        self, db, privacy_request, sentry_dataset_config_without_secrets
    ):
        """Test that a config with grouped inputs (sentry saas connector) has grouped inputs persisted"""
        merged_graph = sentry_dataset_config_without_secrets.get_graph()
        graph = DatasetGraph(merged_graph)

        identity = {"email": "customer-1@example.com"}
        traversal: Traversal = Traversal(graph, identity)
        traversal_nodes = {}
        end_nodes = traversal.traverse(traversal_nodes, collect_tasks_fn)

        _ = persist_new_access_request_tasks(
            db,
            privacy_request,
            traversal,
            traversal_nodes,
            end_nodes,
            graph,
        )

        issues_task = privacy_request.access_tasks.filter(
            RequestTask.collection_address == "sentry_dataset:issues"
        ).first()
        execution_node = ExecutionNode(issues_task)
        assert execution_node.grouped_fields == {
            "project_slug",
            "query",
            "organization_slug",
        }


class TestCanRunTaskBody:
    def test_task_is_pending(self, request_task):
        assert request_task.status == ExecutionLogStatus.pending
        assert can_run_task_body(request_task)

    def test_task_is_skipped(self, db, request_task):
        request_task.update_status(db, ExecutionLogStatus.skipped)
        assert not can_run_task_body(request_task)

    def test_task_is_error(self, db, request_task):
        # Shouldn't hit this case - it would have been reset to pending on reprocessing
        request_task.update_status(db, ExecutionLogStatus.error)
        assert can_run_task_body(request_task)

    def test_task_is_complete(self, db, request_task):
        request_task.update_status(db, ExecutionLogStatus.complete)
        assert not can_run_task_body(request_task)

    @pytest.mark.usefixtures("request_task")
    def test_task_is_root(self, privacy_request):
        root_task = privacy_request.get_root_task_by_action(ActionType.access)
        assert root_task.status == ExecutionLogStatus.complete
        assert not can_run_task_body(root_task)

    @pytest.mark.usefixtures("request_task")
    def test_task_is_terminator(self, privacy_request):
        terminator_task = privacy_request.get_terminate_task_by_action(
            ActionType.access
        )
        assert terminator_task.status == ExecutionLogStatus.pending
        assert not can_run_task_body(terminator_task)
