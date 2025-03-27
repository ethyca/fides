import uuid
from typing import Any, Dict
from unittest import mock
from uuid import uuid4

import pytest
from bson import ObjectId
from fideslang.models import Dataset

from fides.api.common_exceptions import SkippingConsentPropagation
from fides.api.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    Collection,
    CollectionAddress,
    FieldPath,
    GraphDataset,
)
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal, TraversalNode
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import Policy, Rule, RuleTarget
from fides.api.models.privacy_request import ExecutionLog
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import ExecutionLogStatus
from fides.api.task.deprecated_graph_task import (
    _evaluate_erasure_dependencies,
    format_data_use_map_for_caching,
    update_erasure_mapping_from_cache,
)
from fides.api.task.graph_task import (
    EMPTY_REQUEST,
    EMPTY_REQUEST_TASK,
    GraphTask,
    TaskResources,
    build_affected_field_logs,
    collect_queries,
    filter_by_enabled_actions,
)
from fides.api.task.task_resources import Connections
from fides.api.util.consent_util import (
    cache_initial_status_and_identities_for_consent_reporting,
)

from ..graph.graph_test_util import (
    MockMongoTask,
    MockSqlTask,
    collection,
    erasure_policy,
    field,
    generate_field_list,
    generate_node,
)
from .traversal_data import (
    combined_mongo_postgresql_graph,
    sample_traversal,
    traversal_paired_dependency,
)

connection_configs = [
    ConnectionConfig(key="mysql", connection_type=ConnectionType.postgres),
    ConnectionConfig(key="postgres", connection_type=ConnectionType.postgres),
    ConnectionConfig(key="mssql", connection_type=ConnectionType.mssql),
]


@pytest.fixture(scope="function")
def combined_traversal_node_dict(integration_mongodb_config, connection_config):
    mongo_dataset, postgres_dataset = combined_mongo_postgresql_graph(
        connection_config, integration_mongodb_config
    )
    graph = DatasetGraph(mongo_dataset, postgres_dataset)
    identity = {"email": "customer-1@example.com", "phone_number": "111-111-1111"}
    combined_traversal = Traversal(graph, identity)
    return combined_traversal.traversal_node_dict


@pytest.fixture(scope="function")
def make_graph_task(integration_mongodb_config, connection_config, db):
    def task(node):
        request_task = node.to_mock_request_task()
        return MockMongoTask(
            TaskResources(
                EMPTY_REQUEST,
                Policy(),
                [connection_config, integration_mongodb_config],
                request_task,
                db,
            ),
        )

    return task


class TestPreProcessInputData:
    def test_pre_process_input_data_scalar(self, db) -> None:
        t = sample_traversal()
        n = t.traversal_node_dict[CollectionAddress("mysql", "Address")]
        request_task = n.to_mock_request_task()

        task = MockSqlTask(
            TaskResources(EMPTY_REQUEST, Policy(), connection_configs, request_task, db)
        )
        customers_data = [
            {"contact_address_id": 31, "foo": "X"},
            {"contact_address_id": 32, "foo": "Y"},
        ]
        orders_data = [
            {"billing_address_id": 1, "shipping_address_id": 2},
            {"billing_address_id": 11, "shipping_address_id": 22},
        ]
        v = task.pre_process_input_data(customers_data, orders_data)
        assert set(v["id"]) == {31, 32, 1, 2, 11, 22}

    def test_pre_process_input_nested_identity(
        self, combined_traversal_node_dict, make_graph_task
    ):
        """
        Identity data used to locate record on nested email

        Customer feedback node has one input:
        ROOT.email -> customer_feedback.customer_information.email
        """
        node = combined_traversal_node_dict[
            CollectionAddress("mongo_test", "customer_feedback")
        ]
        root_email_input = [{"email": "customer-1@example.com"}]
        assert make_graph_task(node).pre_process_input_data(root_email_input) == {
            "customer_information.email": ["customer-1@example.com"],
            "fidesops_grouped_inputs": [],
        }

    def test_pre_process_input_customer_feedback_collection(
        self, combined_traversal_node_dict, make_graph_task
    ):
        """
        Nested internal_customer_id used to locate record matching nested internal_id

        Internal customer profile node has two inputs:
        ROOT.email -> internal_customer_profile.derived_emails(string[])
        customer_feedback.customer_information.internal_customer_id -> internal_customer_profile.customer_identifiers.internal_id
        """
        node = combined_traversal_node_dict[
            CollectionAddress("mongo_test", "internal_customer_profile")
        ]
        internal_customer_profile_task = make_graph_task(node)
        root_email_input = [{"email": "customer-1@example.com"}]
        customer_feedback_input = [
            {
                "_id": ObjectId("61eb388ecfb4a3721238a39b"),
                "customer_information": {
                    "email": "customer-1@example.com",
                    "phone": "333-333-3333",
                    "internal_customer_id": "cust_001",
                },
            }
        ]

        assert internal_customer_profile_task.pre_process_input_data(
            root_email_input, customer_feedback_input
        ) == {
            "customer_identifiers.derived_emails": ["customer-1@example.com"],
            "customer_identifiers.internal_id": ["cust_001"],
            "fidesops_grouped_inputs": [],
        }

        # group_dependent_fields=True just results in an empty list because no grouped input fields are specified.
        assert internal_customer_profile_task.pre_process_input_data(
            root_email_input, customer_feedback_input, group_dependent_fields=True
        ) == {
            "customer_identifiers.derived_emails": ["customer-1@example.com"],
            "customer_identifiers.internal_id": ["cust_001"],
            "fidesops_grouped_inputs": [],
        }

    def test_pre_process_input_flights_collection(
        self, make_graph_task, combined_traversal_node_dict
    ):
        """
        Array of strings used to locate record with matching value in nested array of strings

        Flights node has one input:
        mongo_test.customer_details.travel_identifiers -> mongo_test.passenger_information.passenger_ids
        """
        node = combined_traversal_node_dict[CollectionAddress("mongo_test", "flights")]
        task = make_graph_task(node)
        truncated_customer_details_output = [
            {
                "_id": ObjectId("61f422e0ddc2559e0c300e95"),
                "travel_identifiers": ["A111-11111", "B111-11111", "D111-11111"],
            },
            {
                "_id": ObjectId("61f422e0ddc2559e0c300e95"),
                "travel_identifiers": ["C111-11111", "D111-11111"],
            },
        ]
        assert task.pre_process_input_data(truncated_customer_details_output) == {
            "passenger_information.passenger_ids": [
                "A111-11111",
                "B111-11111",
                "D111-11111",
                "C111-11111",
            ],
            "fidesops_grouped_inputs": [],
        }

    def test_pre_process_input_aircraft_collection(
        self, make_graph_task, combined_traversal_node_dict
    ):
        """
        Integer used to locate record with matching value in array of integers

        Aircraft node has one input:
        mongo_test:flights.plane -> mongo_test:aircraft.planes
        """
        node = combined_traversal_node_dict[CollectionAddress("mongo_test", "aircraft")]
        task = make_graph_task(node)
        truncated_flights_output = [
            {"pilots": ["1", "2"], "plane": 10002.0},
            {"pilots": ["3", "4"], "plane": 101010},
        ]
        assert task.pre_process_input_data(truncated_flights_output) == {
            "planes": [10002, 101010],
            "fidesops_grouped_inputs": [],
        }

    def test_pre_process_input_employee_collection(
        self, make_graph_task, combined_traversal_node_dict
    ):
        """
        Array of integers used to locate record with matching integer

        Mongo employee node has two inputs:
        root.email -> mongo_test.employee.email
        mongo_test.flights.pilots -> mongo_test.employee.id
        """
        node = combined_traversal_node_dict[CollectionAddress("mongo_test", "employee")]
        task = make_graph_task(node)
        root_email_input = [{"email": "customer-1@example.com"}]
        truncated_flights_output = [
            {"pilots": ["1", "2"], "plane": 10002.0},
            {"pilots": ["3", "4"], "plane": 101010},
        ]
        assert task.pre_process_input_data(
            root_email_input, truncated_flights_output
        ) == {
            "id": ["1", "2", "3", "4"],
            "email": ["customer-1@example.com"],
            "fidesops_grouped_inputs": [],
        }

    def test_pre_process_input_conversation_collection(
        self, make_graph_task, combined_traversal_node_dict
    ):
        """
        Array of objects of strings used to locate record within array of objects of scalars

        Mongo conversation node has one input:
        mongo_test:customer_details.comments.comment_id -> mongo_test:conversations.thread.comment
        """
        node = combined_traversal_node_dict[
            CollectionAddress("mongo_test", "conversations")
        ]
        task = make_graph_task(node)
        truncated_customer_details_output = [
            {
                "comments": [
                    {"comment_id": "com_0001"},
                    {"comment_id": "com_0003"},
                    {"comment_id": "com_0005"},
                ]
            },
            {"comments": [{"comment_id": "com_0007"}]},
        ]

        assert task.pre_process_input_data(truncated_customer_details_output) == {
            "thread.comment": ["com_0001", "com_0003", "com_0005", "com_0007"],
            "fidesops_grouped_inputs": [],
        }

    def test_pre_process_input_data_group_dependent_fields(self, db):
        """Test processing inputs where several reference fields and an identity field have
        been marked as dependent.
        """
        traversal_with_grouped_inputs = traversal_paired_dependency()
        n = traversal_with_grouped_inputs.traversal_node_dict[
            CollectionAddress("mysql", "User")
        ]
        request_task = n.to_mock_request_task()
        task = MockSqlTask(
            TaskResources(EMPTY_REQUEST, Policy(), connection_configs, request_task, db)
        )

        project_output = [
            {
                "organization_id": "12345",
                "project_id": "abcde",
                "project_name": "Sample project",
            },
            {
                "organization_id": "54321",
                "project_id": "fghij",
                "project_name": "Meteor project",
            },
            {
                "organization_id": "54321",
                "project_id": "klmno",
                "project_name": "Saturn project",
            },
        ]

        identity_output = [{"email": "email@gmail.com"}]
        # Typical output - project ids and organization ids would be completely independent from each other
        assert task.pre_process_input_data(identity_output, project_output) == {
            "email": ["email@gmail.com"],
            "project": ["abcde", "fghij", "klmno"],
            "organization": ["12345", "54321"],
            "fidesops_grouped_inputs": [],
        }

        # With group_dependent_fields = True.  Fields are grouped together under a key that shouldn't overlap
        # with actual table keys "fidesops_grouped_inputs"
        assert task.pre_process_input_data(
            identity_output, project_output, group_dependent_fields=True
        ) == {
            "fidesops_grouped_inputs": [
                {
                    "project": ["abcde"],
                    "organization": ["12345"],
                    "email": ["email@gmail.com"],
                },
                {
                    "project": ["fghij"],
                    "organization": ["54321"],
                    "email": ["email@gmail.com"],
                },
                {
                    "project": ["klmno"],
                    "organization": ["54321"],
                    "email": ["email@gmail.com"],
                },
            ]
        }


class TestPostProcessInputData:
    def test_post_process_input_data_filter_match(
        self, combined_traversal_node_dict, make_graph_task
    ):
        node = combined_traversal_node_dict[CollectionAddress("mongo_test", "flights")]
        task = make_graph_task(node)

        node_inputs = {
            "passenger_information.passenger_ids": [
                "A111-11111",
                "B111-11111",
                "C111-11111",
            ]
        }

        assert task.post_process_input_data(node_inputs) == {
            FieldPath("passenger_information", "passenger_ids"): [
                "A111-11111",
                "B111-11111",
                "C111-11111",
            ]
        }

    def test_post_process_input_data_return_all(
        self, combined_traversal_node_dict, make_graph_task
    ):
        node = combined_traversal_node_dict[
            CollectionAddress("mongo_test", "internal_customer_profile")
        ]
        task = make_graph_task(node)

        node_inputs = {
            "customer_identifiers.derived_phone": ["403-204-2933", "403-204-2934"],
            "customer_identifiers.internal_id": ["123456", "483822"],
        }

        # Derived phone field should have no filtering, but internal_id should have filtering
        assert task.post_process_input_data(node_inputs) == {
            FieldPath("customer_identifiers", "derived_phone"): None,
            FieldPath("customer_identifiers", "internal_id"): ["123456", "483822"],
        }

    def test_post_process_input_data_return_all_array_of_objects(
        self, combined_traversal_node_dict, make_graph_task
    ):
        node = combined_traversal_node_dict[CollectionAddress("mongo_test", "rewards")]
        task = make_graph_task(node)

        node_inputs = {
            "owner.phone": ["403-204-2933", "403-204-2934"],
            "not_an_input_field_on_this_node": ["123456", "483822"],
        }

        # Owner.phone id values should have no filtering
        assert task.post_process_input_data(node_inputs) == {
            FieldPath("owner", "phone"): None
        }

    def test_post_process_type_coercion(
        self, combined_traversal_node_dict, make_graph_task
    ):
        node = combined_traversal_node_dict[CollectionAddress("mongo_test", "aircraft")]
        task = make_graph_task(node)

        node_inputs = {"planes": [123, 124]}

        # Planes type is string, so incoming data is coerced into a string where possible
        assert task.post_process_input_data(node_inputs) == {
            FieldPath("planes"): ["123", "124"]
        }


def test_sql_dry_run_queries(db) -> None:
    traversal = sample_traversal()
    env = collect_queries(
        traversal,
        TaskResources(
            EMPTY_REQUEST, Policy(), connection_configs, EMPTY_REQUEST_TASK, db
        ),
    )

    assert (
        env[CollectionAddress("mysql", "Customer")]
        == 'SELECT customer_id, name, email, contact_address_id FROM "Customer" WHERE (email = ?)'
    )

    assert (
        env[CollectionAddress("mysql", "User")]
        == 'SELECT id, user_id, name FROM "User" WHERE (user_id = ?)'
    )

    assert (
        env[CollectionAddress("postgres", "Order")]
        == 'SELECT order_id, customer_id, shipping_address_id, billing_address_id FROM "Order" WHERE (customer_id IN (?, ?))'
    )

    assert (
        env[CollectionAddress("mysql", "Address")]
        == 'SELECT id, street, city, state, zip FROM "Address" WHERE (id IN (?, ?))'
    )

    assert (
        env[CollectionAddress("mssql", "Address")]
        == "SELECT id, street, city, state, zip FROM Address WHERE id IN (:id_in_stmt_generated_0, :id_in_stmt_generated_1)"
    )


def test_mongo_dry_run_queries(db) -> None:
    from .traversal_data import integration_db_graph

    traversal = Traversal(integration_db_graph("postgres"), {"email": ["x"]})
    env = collect_queries(
        traversal,
        TaskResources(
            EMPTY_REQUEST,
            Policy(),
            [
                ConnectionConfig(key="mysql", connection_type=ConnectionType.mongodb),
                ConnectionConfig(
                    key="postgres", connection_type=ConnectionType.mongodb
                ),
            ],
            EMPTY_REQUEST_TASK,
            db,
        ),
    )

    assert (
        env[CollectionAddress("postgres", "customer")]
        == "db.postgres.customer.find({'email': ?}, {'address_id': 1, 'email': 1, 'id': 1, 'name': 1})"
    )

    assert (
        env[CollectionAddress("postgres", "orders")]
        == "db.postgres.orders.find({'customer_id': {'$in': [?, ?]}}, {'customer_id': 1, 'id': 1, 'payment_card_id': 1, 'shipping_address_id': 1})"
    )

    assert (
        env[CollectionAddress("postgres", "address")]
        == "db.postgres.address.find({'id': {'$in': [?, ?]}}, {'city': 1, 'id': 1, 'state': 1, 'street': 1, 'zip': 1})"
    )


class TestBuildAffectedFieldLogs:
    @pytest.fixture(scope="function")
    def node_fixture(self):
        t = sample_traversal()

        postgres_order_node = t.traversal_node_dict[
            CollectionAddress("postgres", "Order")
        ]
        dataset = postgres_order_node.node.dataset

        field([dataset], "postgres", "Order", "customer_id").data_categories = [
            "user.name"
        ]
        field([dataset], "postgres", "Order", "shipping_address_id").data_categories = [
            "system.operations"
        ]
        field([dataset], "postgres", "Order", "order_id").data_categories = [
            "system.operations"
        ]
        field([dataset], "postgres", "Order", "billing_address_id").data_categories = [
            "user.contact"
        ]
        return postgres_order_node

    def test_build_affected_field_logs(self, db, node_fixture):
        policy = erasure_policy(db, "user.name", "system.operations")

        formatted_for_logs = build_affected_field_logs(
            node_fixture.node, policy, action_type=ActionType.erasure
        )

        # Only fields for data categories user.name and system.operations which were specified on the Policy, made it to the logs for this node
        assert sorted(formatted_for_logs, key=lambda d: d["field_name"]) == [
            {
                "path": "postgres:Order:customer_id",
                "field_name": "customer_id",
                "data_categories": ["user.name"],
            },
            {
                "path": "postgres:Order:order_id",
                "field_name": "order_id",
                "data_categories": ["system.operations"],
            },
            {
                "path": "postgres:Order:shipping_address_id",
                "field_name": "shipping_address_id",
                "data_categories": ["system.operations"],
            },
        ]

    def test_build_affected_field_logs_no_data_categories_on_policy(
        self, db, node_fixture
    ):
        no_categories_policy = erasure_policy(db)
        formatted_for_logs = build_affected_field_logs(
            node_fixture.node,
            no_categories_policy,
            action_type=ActionType.erasure,
        )
        # No data categories specified on policy, so no fields affected
        assert formatted_for_logs == []

    def test_build_affected_field_logs_no_matching_data_categories(
        self, db, node_fixture
    ):
        d_categories_policy = erasure_policy(db, "user.demographic")
        formatted_for_logs = build_affected_field_logs(
            node_fixture.node,
            d_categories_policy,
            action_type=ActionType.erasure,
        )
        # No matching data categories specified on policy, so no fields affected
        assert formatted_for_logs == []

    def test_build_affected_field_logs_no_data_categories_for_action_type(
        self, db, node_fixture
    ):
        policy = erasure_policy(db, "user.name", "system.operations")
        formatted_for_logs = build_affected_field_logs(
            node_fixture.node,
            policy,
            action_type=ActionType.access,
        )
        # We only have data categories specified on an erasure policy, and we're looking for access action type
        assert formatted_for_logs == []

    def test_multiple_rules_targeting_same_field(self, db, node_fixture):
        policy = erasure_policy(db, "user.name")

        rule_1 = Rule(
            action_type=ActionType.erasure,
            targets=[RuleTarget(data_category="user.name")],
            masking_strategy={
                "strategy": "null_rewrite",
                "configuration": {},
            },
            policy_id=policy.id,
        )

        target_1 = RuleTarget(data_category="user.name", rule_id=rule_1.id)

        rule_2 = Rule(
            action_type=ActionType.erasure,
            targets=[RuleTarget(data_category="user.name")],
            masking_strategy={
                "strategy": "null_rewrite",
                "configuration": {},
            },
            policy_id=policy.id,
        )

        target_2 = RuleTarget(data_category="user.name", rule_id=rule_2.id)

        formatted_for_logs = build_affected_field_logs(
            node_fixture.node, policy, action_type=ActionType.erasure
        )

        # No duplication of the matching customer_id field, even though multiple rules targeted data category user.name
        assert formatted_for_logs == [
            {
                "path": "postgres:Order:customer_id",
                "field_name": "customer_id",
                "data_categories": ["user.name"],
            }
        ]


class TestUpdateErasureMappingFromCache:
    @pytest.fixture(scope="function")
    def task_resource(self, privacy_request, policy, db, connection_config):
        tr = TaskResources(privacy_request, policy, [], EMPTY_REQUEST_TASK, db)
        tr.get_connector = lambda x: Connections.build_connector(connection_config)
        return tr

    @pytest.fixture(scope="function")
    def collect_tasks_fn(self, task_resource):
        def collect_tasks_fn(
            tn: TraversalNode, data: Dict[CollectionAddress, GraphTask]
        ) -> None:
            """Run the traversal, as an action creating a GraphTask for each traversal_node."""
            if not tn.is_root_node():
                task_resource.privacy_request_task = tn.to_mock_request_task()
                data[tn.address] = GraphTask(task_resource)

        return collect_tasks_fn

    @pytest.fixture(scope="function")
    def dsk(self, collect_tasks_fn) -> Dict[str, Any]:
        """
        Creates a Dask graph representing a dataset containing three collections (ds_1, ds_2, ds_3)
        where the erasure order is ds_3 -> ds_2 -> ds_1
        """
        t = [
            GraphDataset(
                name=f"dr_1",
                collections=[
                    Collection(name=f"ds_{i}", fields=generate_field_list(1))
                    for i in range(1, 4)
                ],
                connection_key="mock_connection_config_key",
            )
        ]

        # the collections are not dependent on each other for access
        field(t, "dr_1", "ds_1", "f1").identity = "email"
        field(t, "dr_1", "ds_2", "f1").identity = "email"
        field(t, "dr_1", "ds_3", "f1").identity = "email"
        collection(t, CollectionAddress("dr_1", "ds_2")).erase_after = [
            CollectionAddress("dr_1", "ds_1")
        ]
        collection(t, CollectionAddress("dr_1", "ds_3")).erase_after = [
            CollectionAddress("dr_1", "ds_2")
        ]
        graph: DatasetGraph = DatasetGraph(*t)
        traversal: Traversal = Traversal(graph, {"email": {"test_user@example.com"}})
        env: Dict[CollectionAddress, Any] = {}
        traversal.traverse(env, collect_tasks_fn)
        erasure_end_nodes = list(graph.nodes.keys())

        # the [] and [[]] values don't matter for this test, we just need to verify that they are not modified
        dsk: Dict[CollectionAddress, Any] = {
            k: (
                t.erasure_request,
                [],
                [[]],
                *_evaluate_erasure_dependencies(t, erasure_end_nodes),
            )
            for k, t in env.items()
        }
        dsk[TERMINATOR_ADDRESS] = (lambda x: x, *erasure_end_nodes)
        dsk[ROOT_COLLECTION_ADDRESS] = 0
        return dsk

    def test_update_erasure_mapping_from_cache_without_data(self, dsk, task_resource):
        task_resource.get_all_cached_erasures = lambda: {}  # represents an empty cache
        update_erasure_mapping_from_cache(dsk, task_resource)
        (task, retrieved_data, input_list, *erasure_prereqs) = dsk[
            CollectionAddress("dr_1", "ds_1")
        ]
        assert callable(task)
        assert task.__name__ == "erasure_request"
        assert retrieved_data == []
        assert input_list == [[]]
        assert erasure_prereqs == [ROOT_COLLECTION_ADDRESS]

    def test_update_erasure_mapping_from_cache_with_data(self, dsk, task_resource):
        task_resource.get_all_cached_erasures = lambda: {
            "dr_1:ds_1": 1
        }  # a cache with the results of the ds_1 collection erasure
        update_erasure_mapping_from_cache(dsk, task_resource)
        assert dsk[CollectionAddress("dr_1", "ds_1")] == 1


class TestFormatDataUseMapForCaching:
    def create_dataset(self, db, fides_key, connection_config):
        """
        Util to create dataset and dataset config used in fixtures
        """
        ds = Dataset(
            fides_key=fides_key,
            organization_fides_key="default_organization",
            name="Postgres Example Subscribers Dataset",
            collections=[
                {
                    "name": "subscriptions",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                            "fidesops_meta": {
                                "identity": "email",
                            },
                        },
                    ],
                },
            ],
        )
        ctl_dataset = CtlDataset(**ds.model_dump(mode="json"))

        db.add(ctl_dataset)
        db.commit()
        dataset_config = DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": fides_key,
                "ctl_dataset_id": ctl_dataset.id,
            },
        )
        return ctl_dataset, dataset_config

    @pytest.fixture(scope="function")
    def connection_config_no_system(self, db):
        """Connection config used for data_use_map testing, not associated with a system"""
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "name": str(uuid4()),
                "key": "connection_config_data_use_map_no_system",
                "connection_type": ConnectionType.timescale,
                "access": AccessLevel.write,
                "disabled": False,
            },
        )

        ctl_dataset, dataset_config = self.create_dataset(
            db, "postgres_example_subscriptions_dataset_no_system", connection_config
        )

        yield connection_config
        dataset_config.delete(db)
        ctl_dataset.delete(db)
        connection_config.delete(db)

    @pytest.fixture(scope="function")
    def connection_config_system(self, db, system):
        """Connection config used for data_use_map testing, associated with a system"""
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "name": str(uuid4()),
                "key": "connection_config_data_use_map",
                "connection_type": ConnectionType.timescale,
                "access": AccessLevel.write,
                "disabled": False,
                "system_id": system.id,
            },
        )

        ctl_dataset, dataset_config = self.create_dataset(
            db, "postgres_example_subscriptions_dataset", connection_config
        )

        yield connection_config
        dataset_config.delete(db)
        ctl_dataset.delete(db)
        connection_config.delete(db)

    @pytest.fixture(scope="function")
    def connection_config_system_multiple_decs(self, db, system_multiple_decs):
        """
        Connection config used for data_use_map testing, associated with a system
        that has multiple privacy declarations and data uses
        """
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "name": str(uuid4()),
                "key": "connection_config_data_use_map_system_multiple_decs",
                "connection_type": ConnectionType.timescale,
                "access": AccessLevel.write,
                "disabled": False,
                "system_id": system_multiple_decs.id,
            },
        )

        ctl_dataset, dataset_config = self.create_dataset(
            db,
            "postgres_example_subscriptions_dataset_multiple_decs",
            connection_config,
        )

        yield connection_config
        dataset_config.delete(db)
        ctl_dataset.delete(db)
        connection_config.delete(db)

    @pytest.mark.parametrize(
        "connection_config_fixtures,expected_data_use_map",
        [
            (
                [
                    "connection_config_no_system"
                ],  # connection config no system, no data uses
                {
                    "postgres_example_subscriptions_dataset_no_system:subscriptions": set()
                },
            ),
            (
                [
                    "connection_config_system"
                ],  # connection config associated with system and therefore data uses
                {
                    "postgres_example_subscriptions_dataset:subscriptions": {
                        "marketing.advertising"
                    },
                },
            ),
            (
                [
                    "connection_config_system_multiple_decs"
                ],  # system has multiple declarations, multiple data uses
                {
                    "postgres_example_subscriptions_dataset_multiple_decs:subscriptions": {
                        "marketing.advertising",
                        "third_party_sharing",
                    },
                },
            ),
            (
                [  # ensure map is populated correctly with multiple systems
                    "connection_config_no_system",
                    "connection_config_system_multiple_decs",
                ],
                {
                    "postgres_example_subscriptions_dataset_no_system:subscriptions": set(),
                    "postgres_example_subscriptions_dataset_multiple_decs:subscriptions": {
                        "marketing.advertising",
                        "third_party_sharing",
                    },
                },
            ),
        ],
    )
    def test_data_use_map(
        self,
        connection_config_fixtures,
        expected_data_use_map,
        db,
        privacy_request,
        policy,
        request,
    ):
        """
        Unit tests that confirm the output from function used to generate
        the `Collection` -> `DataUse` map that's cached during access request execution.
        """

        # load connection config fixtures
        connection_configs = []
        for config_fixture in connection_config_fixtures:
            connection_configs.append(request.getfixturevalue(config_fixture))

        # create a sample traversal with our current dataset state
        datasets = DatasetConfig.all(db=db)
        dataset_graphs = [dataset_config.get_graph() for dataset_config in datasets]
        dataset_graph = DatasetGraph(*dataset_graphs)
        traversal: Traversal = Traversal(
            dataset_graph, {"email": {"test_user@example.com"}}
        )
        env: Dict[CollectionAddress, Any] = {}
        task_resources = TaskResources(
            privacy_request, policy, connection_configs, EMPTY_REQUEST_TASK, db
        )

        # perform the traversal to populate our `env` dict
        def collect_tasks_fn(
            tn: TraversalNode, data: Dict[CollectionAddress, GraphTask]
        ) -> None:
            """Run the traversal, as an action creating a GraphTask for each traversal_node."""
            if not tn.is_root_node():
                task_resources.privacy_request_task = tn.to_mock_request_task()
                data[tn.address] = GraphTask(task_resources)

        traversal.traverse(
            env,
            collect_tasks_fn,
        )

        # ensure that the generated data_use_map looks as expected based on `env` dict
        assert (
            format_data_use_map_for_caching(
                {
                    coll_address: gt.execution_node.connection_key
                    for (coll_address, gt) in env.items()
                },
                connection_configs,
            )
            == expected_data_use_map
        )


class TestGraphTaskAffectedConsentSystems:
    @pytest.fixture()
    def mock_graph_task(
        self,
        db,
        saas_example_connection_config,
        privacy_request_with_consent_policy,
    ):
        task_resources = TaskResources(
            privacy_request_with_consent_policy,
            privacy_request_with_consent_policy.policy,
            [saas_example_connection_config],
            EMPTY_REQUEST_TASK,
            db,
        )
        tn = TraversalNode(generate_node("a", "b", "c", "c2"))
        tn.node.dataset.connection_key = saas_example_connection_config.key
        task_resources.privacy_request_task = tn.to_mock_request_task()
        return GraphTask(task_resources)

    @mock.patch(
        "fides.api.service.connectors.saas_connector.SaaSConnector.run_consent_request"
    )
    def test_skipped_consent_task_for_connector(
        self,
        mock_run_consent_request,
        mock_graph_task,
        db,
        privacy_request_with_consent_policy,
        privacy_preference_history,
        privacy_preference_history_us_ca_provide,
    ):
        """Test that all privacy preferences for a consent connector get marked as skipped if SkippingConsentPropagation gets called"""
        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history_us_ca_provide.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)
        privacy_preference_history_us_ca_provide.save(db)

        mock_run_consent_request.side_effect = SkippingConsentPropagation(
            "No preferences are relevant"
        )

        ret = mock_graph_task.consent_request({"email": "customer-1@example.com"})
        assert ret is False

        db.refresh(privacy_preference_history)
        db.refresh(privacy_preference_history_us_ca_provide)

        assert privacy_preference_history.affected_system_status == {
            "saas_connector_example": "skipped"
        }
        assert privacy_preference_history_us_ca_provide.affected_system_status == {
            "saas_connector_example": "skipped"
        }

        logs = (
            db.query(ExecutionLog)
            .filter(
                ExecutionLog.privacy_request_id
                == privacy_request_with_consent_policy.id
            )
            .order_by(ExecutionLog.created_at.desc())
        )
        assert logs.first().status == ExecutionLogStatus.skipped

    @mock.patch("fides.api.task.graph_task.mark_current_and_downstream_nodes_as_failed")
    @mock.patch(
        "fides.api.service.connectors.saas_connector.SaaSConnector.run_consent_request"
    )
    def test_errored_consent_task_for_connector_no_relevant_preferences(
        self,
        mock_run_consent_request,
        mark_current_and_downstream_nodes_as_failed_mock,
        saas_example_connection_config,
        mock_graph_task,
        db,
        privacy_request_with_consent_policy,
        privacy_preference_history,
        privacy_preference_history_us_ca_provide,
    ):
        """Test privacy preferences only marked as errored if they have pending logs"""
        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history_us_ca_provide.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)
        privacy_preference_history_us_ca_provide.save(db)

        mock_run_consent_request.side_effect = BaseException("Request failed")
        cache_initial_status_and_identities_for_consent_reporting(
            db,
            privacy_request_with_consent_policy,
            saas_example_connection_config,
            relevant_preferences=[privacy_preference_history_us_ca_provide],
            relevant_user_identities={"email": "customer-1@example.com"},
        )
        with pytest.raises(BaseException) as exc:
            ret = mock_graph_task.consent_request({"email": "customer-1@example.com"})
            assert ret is False

        assert str(exc.value) == "Request failed"

        db.refresh(privacy_preference_history)
        db.refresh(privacy_preference_history_us_ca_provide)

        assert privacy_preference_history.affected_system_status == {
            "saas_connector_example": "skipped"
        }
        assert privacy_preference_history_us_ca_provide.affected_system_status == {
            "saas_connector_example": "error"
        }

        logs = (
            db.query(ExecutionLog)
            .filter(
                ExecutionLog.privacy_request_id
                == privacy_request_with_consent_policy.id
            )
            .order_by(ExecutionLog.created_at.desc())
        )
        assert logs.first().status == ExecutionLogStatus.error
        assert mark_current_and_downstream_nodes_as_failed_mock.called


class TestFilterByEnabledActions:
    def test_filter_by_enabled_actions_enabled_actions_none(self):
        access_results = {
            "dataset1:collection": "data",
            "dataset2:collection": "data",
        }
        connection_configs = [
            ConnectionConfig(
                datasets=[
                    DatasetConfig(fides_key="dataset1"),
                ],
                enabled_actions=None,
            ),
            ConnectionConfig(
                datasets=[DatasetConfig(fides_key="dataset2")],
                enabled_actions=None,
            ),
        ]

        assert filter_by_enabled_actions(access_results, connection_configs) == {
            "dataset1:collection": "data",
            "dataset2:collection": "data",
        }

    def test_filter_by_enabled_actions_access_enabled(self):
        access_results = {
            "dataset1:collection": "data",
            "dataset2:collection": "data",
        }
        connection_configs = [
            ConnectionConfig(
                datasets=[
                    DatasetConfig(fides_key="dataset1"),
                ],
                enabled_actions=[ActionType.access],
            ),
            ConnectionConfig(
                datasets=[DatasetConfig(fides_key="dataset2")],
                enabled_actions=[ActionType.access],
            ),
        ]

        assert filter_by_enabled_actions(access_results, connection_configs) == {
            "dataset1:collection": "data",
            "dataset2:collection": "data",
        }

    def test_filter_by_enabled_actions_only_erasure(self):
        access_results = {
            "dataset1:collection": "data",
            "dataset2:collection": "data",
        }
        connection_configs = [
            ConnectionConfig(
                datasets=[
                    DatasetConfig(fides_key="dataset1"),
                ],
                enabled_actions=[ActionType.erasure],
            ),
            ConnectionConfig(
                datasets=[DatasetConfig(fides_key="dataset2")],
                enabled_actions=[ActionType.erasure],
            ),
        ]

        assert filter_by_enabled_actions(access_results, connection_configs) == {}

    def test_filter_by_enabled_actions_mixed_actions(self):
        access_results = {
            "dataset1:collection": "data",
            "dataset2:collection": "data",
        }
        connection_configs = [
            ConnectionConfig(
                datasets=[
                    DatasetConfig(fides_key="dataset1"),
                ],
                enabled_actions=[ActionType.access],
            ),
            ConnectionConfig(
                datasets=[DatasetConfig(fides_key="dataset2")],
                enabled_actions=[ActionType.erasure],
            ),
        ]

        assert filter_by_enabled_actions(access_results, connection_configs) == {
            "dataset1:collection": "data",
        }


class TestGraphTaskLogging:
    @pytest.fixture(scope="function")
    def graph_task(self, privacy_request, policy, db):
        resources = TaskResources(
            privacy_request,
            policy,
            [
                ConnectionConfig(
                    key="mock_connection_config_key_a",
                    connection_type=ConnectionType.postgres,
                )
            ],
            EMPTY_REQUEST_TASK,
            db,
        )
        tn = TraversalNode(generate_node("a", "b", "c"))
        rq = tn.to_mock_request_task()
        rq.action_type = ActionType.access
        rq.status = ExecutionLogStatus.pending
        rq.id = str(uuid.uuid4())
        db.add(rq)
        db.commit()

        resources.privacy_request_task = rq
        return GraphTask(resources)

    def test_log_start(self, graph_task, db, privacy_request):
        graph_task.log_start(action_type=ActionType.access)

        assert graph_task.request_task.status == ExecutionLogStatus.in_processing

        execution_log = (
            db.query(ExecutionLog)
            .filter(
                ExecutionLog.privacy_request_id == privacy_request.id,
                ExecutionLog.collection_name == "b",
                ExecutionLog.dataset_name == "a",
                ExecutionLog.action_type == ActionType.access,
            )
            .first()
        )
        assert execution_log.status == ExecutionLogStatus.in_processing

    def test_log_retry(self, graph_task, db, privacy_request):
        graph_task.log_retry(action_type=ActionType.access)

        assert graph_task.request_task.status == ExecutionLogStatus.retrying

        execution_log = (
            db.query(ExecutionLog)
            .filter(
                ExecutionLog.privacy_request_id == privacy_request.id,
                ExecutionLog.collection_name == "b",
                ExecutionLog.dataset_name == "a",
                ExecutionLog.action_type == ActionType.access,
            )
            .first()
        )
        assert execution_log.status == ExecutionLogStatus.retrying

    def test_log_skipped(self, graph_task, db, privacy_request):
        graph_task.log_skipped(action_type=ActionType.access, ex="Skipping node")

        assert graph_task.request_task.status == ExecutionLogStatus.skipped
        assert graph_task.request_task.consent_sent is None, "Not applicable for access"

        execution_log = (
            db.query(ExecutionLog)
            .filter(
                ExecutionLog.privacy_request_id == privacy_request.id,
                ExecutionLog.collection_name == "b",
                ExecutionLog.dataset_name == "a",
                ExecutionLog.action_type == ActionType.access,
            )
            .first()
        )
        assert execution_log.status == ExecutionLogStatus.skipped

        graph_task.log_skipped(action_type=ActionType.consent, ex="Skipping node")
        assert graph_task.request_task.consent_sent is False

    @mock.patch("fides.api.task.graph_task.mark_current_and_downstream_nodes_as_failed")
    def test_log_end_error(
        self,
        mark_current_and_downstream_nodes_as_failed_mock,
        graph_task,
        db,
        privacy_request,
    ):
        graph_task.log_end(action_type=ActionType.access, ex=Exception("Key Error"))

        assert graph_task.request_task.status == ExecutionLogStatus.error

        assert mark_current_and_downstream_nodes_as_failed_mock.called
        execution_log = (
            db.query(ExecutionLog)
            .filter(
                ExecutionLog.privacy_request_id == privacy_request.id,
                ExecutionLog.collection_name == "b",
                ExecutionLog.dataset_name == "a",
                ExecutionLog.action_type == ActionType.access,
            )
            .first()
        )

        assert execution_log.status == ExecutionLogStatus.error

    @mock.patch("fides.api.task.graph_task.mark_current_and_downstream_nodes_as_failed")
    def test_log_end_complete(
        self,
        mark_current_and_downstream_nodes_as_failed_mock,
        graph_task,
        db,
        privacy_request,
    ):
        graph_task.log_end(action_type=ActionType.access)

        assert graph_task.request_task.status == ExecutionLogStatus.complete

        assert not mark_current_and_downstream_nodes_as_failed_mock.called
        execution_log = (
            db.query(ExecutionLog)
            .filter(
                ExecutionLog.privacy_request_id == privacy_request.id,
                ExecutionLog.collection_name == "b",
                ExecutionLog.dataset_name == "a",
                ExecutionLog.action_type == ActionType.access,
            )
            .first()
        )

        assert execution_log.status == ExecutionLogStatus.complete
