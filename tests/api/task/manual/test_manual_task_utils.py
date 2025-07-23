import uuid

import pytest
from sqlalchemy.orm import Session

from fides.api.graph.config import CollectionAddress
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.manual_task import ManualTask
from fides.api.models.manual_task.conditional_dependency import (
    ManualTaskConditionalDependency,
    ManualTaskConditionalDependencyType,
)
from fides.api.task.manual.manual_task_utils import (
    ManualTaskAddress,
    create_manual_data_traversal_node,
    create_manual_task_artificial_graphs,
)


class TestManualTaskUtilsConditionalDependencies:
    """Test manual task utils functionality with conditional dependencies"""

    @pytest.mark.usefixtures("condition_gt_18", "condition_eq_active")
    def test_create_manual_data_traversal_node_with_conditional_dependencies(
        self, db: Session, connection_with_manual_access_task
    ):
        """Test that conditional dependency field addresses are included in traversal node fields"""
        connection_config, _, _, _ = connection_with_manual_access_task

        # Create traversal node
        address = ManualTaskAddress.create(connection_config.key)
        traversal_node = create_manual_data_traversal_node(db, address)

        # Get the collection from the traversal node
        collection = traversal_node.node.collection

        # Verify that both regular fields and conditional dependency fields are included
        field_names = [field.name for field in collection.fields]

        # Should include the regular field
        assert "user_email" in field_names

        # Should include conditional dependency fields (extracted field names)
        assert "age" in field_names  # from "user.profile.age"
        assert "status" in field_names  # from "billing.subscription.status"

    @pytest.mark.usefixtures("connection_with_manual_access_task", "condition_gt_18")
    def test_manual_task_dependencies_on_regular_tasks(
        self, db: Session, connection_with_manual_access_task
    ):
        """Test that manual tasks establish dependencies on regular tasks when conditional dependencies reference their fields"""
        connection_config, manual_task, _, _ = connection_with_manual_access_task

        # Create artificial graphs
        graphs = create_manual_task_artificial_graphs(db)

        # Should have one graph for the manual task
        assert len(graphs) == 1

        graph = graphs[0]

        # Should have one collection per manual task
        assert len(graph.collections) == 1

        collection = graph.collections[0]

        # Verify that the collection has dependencies on regular tasks
        # The condition_gt_18 fixture references "user.profile.age" which should
        # create a dependency on the "customer" collection from "postgres_example"
        assert len(collection.after) > 0

        # Check that the dependency includes the expected collection
        expected_dependency = CollectionAddress("postgres_example", "customer")
        assert expected_dependency in collection.after

        # Verify the collection name includes the manual task ID
        expected_collection_name = f"manual_data_{manual_task.id}"
        assert collection.name == expected_collection_name

    @pytest.mark.usefixtures("connection_with_manual_access_task", "group_condition")
    def test_manual_task_dependencies_from_group_conditions(
        self, db: Session, connection_with_manual_access_task
    ):
        """Test that manual tasks establish dependencies from group conditional dependencies"""
        connection_config, manual_task, _, _ = connection_with_manual_access_task

        # Create artificial graphs
        graphs = create_manual_task_artificial_graphs(db)

        # Should have one graph for the manual task
        assert len(graphs) == 1

        graph = graphs[0]

        # Should have one collection per manual task
        assert len(graph.collections) == 1

        collection = graph.collections[0]

        # Verify that the collection has dependencies on regular tasks
        # The group_condition fixture references both "user.profile.age" and "billing.subscription.status"
        # which should create dependencies on both "customer" and "payment_card" collections
        assert len(collection.after) >= 2

        # Check that the dependencies include the expected collections
        expected_dependencies = {
            CollectionAddress("postgres_example", "customer"),
            CollectionAddress("postgres_example", "payment_card"),
        }
        assert expected_dependencies.issubset(collection.after)

        # Verify the collection name includes the manual task ID
        expected_collection_name = f"manual_data_{manual_task.id}"
        assert collection.name == expected_collection_name

    @pytest.mark.usefixtures(
        "connection_with_manual_access_task", "nested_group_condition"
    )
    def test_conditional_dependency_nested_group_fields_extraction(
        self,
        db: Session,
    ):
        """Test that field addresses are extracted from nested group conditional dependencies"""

        # Create artificial graphs
        graphs = create_manual_task_artificial_graphs(db)

        # Should have one graph for the manual task
        assert len(graphs) == 1

        graph = graphs[0]
        collection = graph.collections[0]

        # Verify that field addresses from nested group children are included
        field_names = [field.name for field in collection.fields]

        # Should include conditional dependency fields from nested group children
        assert "role" in field_names  # from "user.role"
        assert "age" in field_names  # from "user.profile.age"
        assert "status" in field_names  # from "billing.subscription.status"

    @pytest.mark.usefixtures(
        "connection_with_manual_access_task", "condition_gt_18", "condition_age_lt_65"
    )
    def test_no_duplicate_fields_from_conditional_dependencies(
        self, db: Session, manual_task: ManualTask
    ):
        """Test that duplicate field addresses don't create duplicate fields"""

        # Create artificial graphs
        graphs = create_manual_task_artificial_graphs(db)

        # Should have one graph for the manual task
        assert len(graphs) == 1

        graph = graphs[0]
        collection = graph.collections[0]

        # Verify that only one field is created for the duplicate field_address
        field_names = [field.name for field in collection.fields]
        age_fields = [name for name in field_names if name == "age"]

        assert len(age_fields) == 1  # Should only have one "age" field

    @pytest.mark.usefixtures("connection_with_manual_access_task")
    def test_multiple_manual_tasks_get_separate_collections(
        self, db: Session, connection_with_manual_access_task
    ):
        """Test that multiple manual tasks get separate collections with their own dependencies"""
        connection_config, manual_task, _, _ = connection_with_manual_access_task

        # Create a second connection config and manual task
        second_connection_config = ConnectionConfig.create(
            db=db,
            data={
                "name": "Second Manual Task Connection",
                "key": f"manual_second_{uuid.uuid4()}",
                "connection_type": ConnectionType.manual_task,
                "access": AccessLevel.write,
            },
        )

        # Create a second manual task with different conditional dependencies
        second_manual_task = ManualTask.create(
            db=db,
            data={
                "task_type": "privacy_request",
                "parent_entity_id": second_connection_config.id,
                "parent_entity_type": "connection_config",
            },
        )

        # Add a conditional dependency to the second task
        ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": second_manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.leaf,
                "field_address": "billing.subscription.status",
                "operator": "eq",
                "value": "active",
                "sort_order": 1,
            },
        )

        try:
            # Create artificial graphs
            graphs = create_manual_task_artificial_graphs(db)

            # Should have two graphs (one for each connection config)
            assert len(graphs) == 2

            # Find the graphs for each connection
            first_graph = next(g for g in graphs if g.name == connection_config.key)
            second_graph = next(
                g for g in graphs if g.name == second_connection_config.key
            )

            # Each graph should have one collection
            assert len(first_graph.collections) == 1
            assert len(second_graph.collections) == 1

            # Verify each collection has the correct name and dependencies
            first_collection = first_graph.collections[0]
            second_collection = second_graph.collections[0]

            expected_first_name = f"manual_data_{manual_task.id}"
            expected_second_name = f"manual_data_{second_manual_task.id}"

            assert first_collection.name == expected_first_name
            assert second_collection.name == expected_second_name

            # First task has no conditional dependencies, so no dependencies
            assert len(first_collection.after) == 0

            # Second task has conditional dependency on billing.subscription.status, so depends on payment_card
            assert len(second_collection.after) == 1
            expected_dependency = CollectionAddress("postgres_example", "payment_card")
            assert expected_dependency in second_collection.after

        finally:
            # Clean up
            second_manual_task.delete(db)
            second_connection_config.delete(db)
