import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    PrivacyRequestCanceled,
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
    FieldPath,
)
from fides.api.graph.execution import ExecutionNode
from fides.api.graph.graph import DatasetGraph, Edge
from fides.api.graph.traversal import Traversal
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.privacy_request import (
    ExecutionLogStatus,
    PrivacyRequestStatus,
    RequestTask,
)
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
from fides.api.task.graph_runners import use_dsr_3_0_scheduler
from fides.api.task.graph_task import mark_current_and_downstream_nodes_as_failed
from fides.api.task.task_resources import TaskResources
from fides.api.util.cache import FidesopsRedis, get_cache


def _collect_task_resources(
    session: Session, request_task: RequestTask
) -> TaskResources:
    """Build the TaskResources artifact which just collects some Database resources needed for the current task
    Currently just used for testing -
    """
    return TaskResources(
        request_task.privacy_request,
        request_task.privacy_request.policy,
        session.query(ConnectionConfig).all(),
        request_task,
        session,
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

    def test_privacy_request_was_cancelled(self, db, privacy_request):
        privacy_request.status = PrivacyRequestStatus.canceled
        privacy_request.save(db)

        with pytest.raises(PrivacyRequestCanceled):
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
        resources = _collect_task_resources(db, request_task)

        graph_task = create_graph_task(db, request_task, resources)

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

        resources = _collect_task_resources(db, request_task)

        with pytest.raises(ResumeTaskException):
            create_graph_task(db, request_task, resources)

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

    @pytest.mark.skip(reason="move to plus in progress")
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

    def test_query_field_paths(self, address_execution_node, employee_execution_node):
        assert address_execution_node.query_field_paths == {
            FieldPath(
                "id",
            )
        }
        assert employee_execution_node.query_field_paths == {
            FieldPath("email"),
        }

    def test_dependent_identity_fields(self, address_execution_node):
        assert not address_execution_node.dependent_identity_fields

        # Edit node to add a grouped field that also is an identity field
        address_execution_node.grouped_fields = {
            address_execution_node.collection.fields[0].name
        }
        address_execution_node.collection.fields[0].identity = "email"
        assert address_execution_node.dependent_identity_fields

    def test_build_incoming_field_path_maps(self, address_execution_node):
        """Light test of most common path, the first tuple"""
        field_path_maps = address_execution_node.build_incoming_field_path_maps()[0]

        assert field_path_maps[
            CollectionAddress("postgres_example_test_dataset", "employee")
        ] == [
            (
                FieldPath(
                    "address_id",
                ),
                FieldPath(
                    "id",
                ),
            )
        ]
        assert field_path_maps[
            CollectionAddress("postgres_example_test_dataset", "customer")
        ] == [
            (
                FieldPath(
                    "address_id",
                ),
                FieldPath(
                    "id",
                ),
            )
        ]
        assert field_path_maps[
            CollectionAddress("postgres_example_test_dataset", "orders")
        ] == [
            (
                FieldPath(
                    "shipping_address_id",
                ),
                FieldPath(
                    "id",
                ),
            )
        ]
        assert field_path_maps[
            CollectionAddress("postgres_example_test_dataset", "payment_card")
        ] == [
            (
                FieldPath(
                    "billing_address_id",
                ),
                FieldPath(
                    "id",
                ),
            )
        ]

    def test_typed_filtered_values(self, address_execution_node):
        assert address_execution_node.typed_filtered_values({"id": [1, 2]}) == {
            "id": [1, 2]
        }
        assert (
            address_execution_node.typed_filtered_values({"non_existent_id": [1, 2]})
            == {}
        )


class TestCanRunTaskBody:
    def test_task_is_pending(self, request_task):
        assert request_task.status == ExecutionLogStatus.pending
        assert can_run_task_body(request_task)

    def test_task_is_skipped(self, db, request_task):
        request_task.update_status(db, ExecutionLogStatus.skipped)
        assert not can_run_task_body(request_task)

    def test_task_is_error(self, db, request_task):
        request_task.update_status(db, ExecutionLogStatus.error)
        # Error states need to be set to pending when reprocessing
        assert not can_run_task_body(request_task)

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


class TestMarkCurrentAndDownstreamNodesAsFailed:
    def test_mark_tasks_as_failed(
        self, db, privacy_request, request_task, erasure_request_task
    ):
        root_task = privacy_request.get_root_task_by_action(ActionType.access)
        terminator_task = privacy_request.get_terminate_task_by_action(
            ActionType.access
        )
        assert request_task.status == ExecutionLogStatus.pending
        assert terminator_task.status == ExecutionLogStatus.pending

        mark_current_and_downstream_nodes_as_failed(request_task, db)

        db.refresh(root_task)
        db.refresh(request_task)
        db.refresh(terminator_task)
        db.refresh(erasure_request_task)

        # Upstream task unaffected
        assert root_task.status == ExecutionLogStatus.complete
        # Both current task and terminator task marked as error
        assert request_task.status == ExecutionLogStatus.error
        assert terminator_task.status == ExecutionLogStatus.error
        # Task of a different action type unaffected
        assert erasure_request_task.status == ExecutionLogStatus.pending


class TestGetDSRVersion:
    @pytest.mark.usefixtures("use_dsr_2_0")
    def test_use_dsr_2_0(self, privacy_request):
        assert use_dsr_3_0_scheduler(privacy_request, ActionType.access) is False

    @pytest.mark.usefixtures("use_dsr_3_0")
    def test_use_dsr_3_0(self, privacy_request):
        assert use_dsr_3_0_scheduler(privacy_request, ActionType.access) is True

    @pytest.mark.usefixtures("use_dsr_3_0")
    def test_use_dsr_2_0_override(
        self,
        privacy_request,
    ):
        cache: FidesopsRedis = get_cache()
        key = f"access_request__test_dataset:test_collection"
        cache.set_encoded_object(f"{privacy_request.id}__{key}", 2)

        # Privacy request already started processing on DSR 2.0 so we continue on DSR 2.0
        assert use_dsr_3_0_scheduler(privacy_request, ActionType.access) is False

    @pytest.mark.usefixtures("use_dsr_2_0")
    def test_use_dsr_3_0_override(self, privacy_request, request_task):
        # Privacy Request already started processing on 3.0, but we allow it to be switched to 2.0
        assert use_dsr_3_0_scheduler(privacy_request, ActionType.access) is False
