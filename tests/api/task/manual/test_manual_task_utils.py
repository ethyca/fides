import pytest
from sqlalchemy.orm import Session

from fides.api.models.manual_task import ManualTask
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
    def test_create_manual_task_artificial_graphs_with_conditional_dependencies(
        self,
        db: Session,
    ):
        """Test that conditional dependency field addresses are included in artificial graphs"""
        # Create artificial graphs
        graphs = create_manual_task_artificial_graphs(db)

        # Should have one graph for the manual task
        assert len(graphs) == 1

        graph = graphs[0]
        collection = graph.collections[0]

        # Verify that both regular fields and conditional dependency fields are included
        field_names = [field.name for field in collection.fields]

        # Should include the regular field
        assert "user_email" in field_names

        # Should include conditional dependency fields (extracted field names)
        assert "age" in field_names  # from "user.profile.age"

    @pytest.mark.usefixtures("connection_with_manual_access_task", "group_condition")
    def test_conditional_dependency_group_fields_extraction(
        self, db: Session, connection_with_manual_access_task
    ):
        """Test that field addresses are extracted from group conditional dependencies"""
        # Create artificial graphs
        graphs = create_manual_task_artificial_graphs(db)

        # Should have one graph for the manual task
        assert len(graphs) == 1

        graph = graphs[0]
        collection = graph.collections[0]

        # Verify that field addresses from group children are included
        field_names = [field.name for field in collection.fields]

        # Should include conditional dependency fields from group children
        assert "age" in field_names  # from "user.profile.age"
        assert "status" in field_names  # from "billing.subscription.status"

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
