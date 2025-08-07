import uuid

import pytest
from pytest import param
from sqlalchemy.orm import Session

from fides.api.common_exceptions import FidesopsException
from fides.api.graph.config import CollectionAddress, FieldAddress, ScalarField
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
from fides.api.task.manual.manual_task_address import ManualTaskAddress
from fides.api.task.manual.manual_task_utils import (
    create_collection_for_connection_key,
    create_conditional_dependency_scalar_fields,
    create_data_category_scalar_fields,
    create_manual_task_artificial_graphs,
    get_connection_configs_with_manual_tasks,
    get_manual_task_addresses,
    get_manual_task_for_connection_config,
)


class TestManualTaskUtilsHelperFunctions:
    """Test individual helper functions in manual_task_utils"""

    def test_get_connection_configs_with_manual_tasks(
        self, db: Session, connection_with_manual_access_task
    ):
        """Test getting connection configs that have manual tasks"""
        connection_config, _, _, _ = connection_with_manual_access_task

        # Get connection configs with manual tasks
        configs = get_connection_configs_with_manual_tasks(db)

        # Should include our connection config
        assert len(configs) >= 1
        assert connection_config in configs

        # Verify the connection config has the expected properties
        found_config = next(c for c in configs if c.id == connection_config.id)
        assert found_config.key == connection_config.key
        assert found_config.connection_type == ConnectionType.manual_task
        assert found_config.disabled is False

    def test_get_connection_configs_with_manual_tasks_excludes_disabled(
        self, db: Session, connection_config
    ):
        """Test that disabled connection configs are excluded"""
        # Create a manual task for the connection config
        manual_task = ManualTask.create(
            db=db,
            data={
                "task_type": "privacy_request",
                "parent_entity_id": connection_config.id,
                "parent_entity_type": "connection_config",
            },
        )

        # Disable the connection config
        connection_config.disabled = True
        db.commit()

        try:
            # Get connection configs with manual tasks
            configs = get_connection_configs_with_manual_tasks(db)

            # Should not include the disabled connection config
            assert connection_config not in configs
        finally:
            # Clean up
            manual_task.delete(db)

    def test_get_manual_task_addresses(
        self, db: Session, connection_with_manual_access_task
    ):
        """Test getting manual task addresses"""
        connection_config, _, _, _ = connection_with_manual_access_task

        # Get manual task addresses
        addresses = get_manual_task_addresses(db)

        # Should include our connection config's address
        assert len(addresses) >= 1

        # Find our connection config's address
        expected_address = ManualTaskAddress.create(connection_config.key)
        assert expected_address in addresses

        # Verify the address format
        found_address = next(a for a in addresses if a.dataset == connection_config.key)
        assert found_address.collection == ManualTaskAddress.MANUAL_DATA_COLLECTION

    def test_get_manual_task_for_connection_config(
        self, db: Session, connection_with_manual_access_task
    ):
        """Test getting manual task for a specific connection config"""
        connection_config, manual_task, _, _ = connection_with_manual_access_task

        # Get manual task for the connection config
        found_task = get_manual_task_for_connection_config(db, connection_config.key)

        # Should find the manual task
        assert found_task is not None
        assert found_task.id == manual_task.id
        assert found_task.parent_entity_id == connection_config.id
        assert found_task.parent_entity_type == "connection_config"

    def test_get_manual_task_for_connection_config_not_found(self, db: Session):
        """Test getting manual task for non-existent connection config"""
        # Try to get manual task for non-existent connection config
        found_task = get_manual_task_for_connection_config(db, "non_existent_key")

        # Should return None
        assert found_task is None

    def test_create_data_category_scalar_fields(
        self, connection_with_manual_access_task
    ):
        """Test creating scalar fields from manual task data categories"""
        _, manual_task, _, _ = connection_with_manual_access_task

        # Create scalar fields
        fields = create_data_category_scalar_fields(manual_task)

        # Should have fields from the manual task config
        assert len(fields) >= 1

        # Find the expected field
        expected_field = next((f for f in fields if f.name == "user_email"), None)
        assert expected_field is not None
        assert expected_field.data_categories == ["user.contact.email"]

    def test_create_data_category_scalar_fields_no_configs(self, manual_task):
        """Test creating scalar fields when manual task has no configs"""
        # Create scalar fields for manual task with no configs
        fields = create_data_category_scalar_fields(manual_task)

        # Should return empty list
        assert fields == []

    def test_create_conditional_dependency_scalar_fields(self):
        """Test creating scalar fields from conditional dependency field addresses"""
        field_addresses = {
            "postgres_example:customer:profile.age",
            "postgres_example:payment_card:subscription.status",
            "postgres_example:customer:email",
        }

        # Create scalar fields
        fields = create_conditional_dependency_scalar_fields(field_addresses)

        # Should have one field per field address
        assert len(fields) == 3

        # Verify each field
        field_names = {field.name for field in fields}
        assert field_names == field_addresses

        # Verify data categories are empty for conditional dependency fields
        for field in fields:
            assert field.data_categories == []

    def test_create_conditional_dependency_scalar_fields_empty(self):
        """Test creating scalar fields with empty field addresses"""
        # Create scalar fields with empty set
        fields = create_conditional_dependency_scalar_fields(set())

        # Should return empty list
        assert fields == []


class TestManualTaskUtilsAddressParsing:
    """Test address parsing helper functions"""

    def test_create_collection_for_connection_key_no_manual_task(self, db: Session):
        """Test creating collection for connection key with no manual task"""
        # Try to create collection for non-existent connection key
        collection = create_collection_for_connection_key(db, "non_existent_key")

        # Should return None when no manual task exists
        assert collection is None

    def test_create_collection_for_connection_key_no_fields(
        self, db: Session, connection_config
    ):
        """Test creating collection for connection key with no fields"""
        # Create manual task without any configs or conditional dependencies
        manual_task = ManualTask.create(
            db=db,
            data={
                "task_type": "privacy_request",
                "parent_entity_id": connection_config.id,
                "parent_entity_type": "connection_config",
            },
        )

        try:
            # Create collection for the connection key
            collection = create_collection_for_connection_key(
                db,
                connection_config.key,
            )

            # Should return None when no fields are available
            assert collection is None

        finally:
            # Clean up
            manual_task.delete(db)


class TestManualTaskUtilsConditionalDependencies:
    """Test manual task utils functionality with conditional dependencies"""

    @pytest.mark.usefixtures("connection_with_manual_access_task", "condition_gt_18")
    def test_manual_task_dependencies_on_regular_tasks(
        self, db: Session, connection_with_manual_access_task
    ):
        """Test that manual tasks establish dependencies on regular tasks when conditional dependencies reference their fields"""
        connection_config, manual_task, _, _ = connection_with_manual_access_task

        # Create artificial graphs with the mock dataset graph
        graphs = create_manual_task_artificial_graphs(db)

        # Should have one graph for the manual task
        assert len(graphs) == 1

        graph = graphs[0]

        # Should have one collection per manual task
        assert len(graph.collections) == 1

        collection = graph.collections[0]

        # Verify that the collection has scalar fields with references to regular tasks
        # The condition_gt_18 fixture references "customer.profile.age" which should
        # create a scalar field with a reference to the "customer" collection from "postgres_example"
        assert len(collection.fields) > 0

        # Check that there's a scalar field with the expected reference
        expected_field_name = "postgres_example:customer:profile.age"
        expected_reference = FieldAddress("postgres_example", "customer", "profile.age")

        field_with_reference = None
        for field in collection.fields:
            if field.name == expected_field_name:
                field_with_reference = field
                break

        assert (
            field_with_reference is not None
        ), f"Expected field '{expected_field_name}' not found"
        assert len(field_with_reference.references) == 1
        assert field_with_reference.references[0][0] == expected_reference
        assert field_with_reference.references[0][1] == "from"

        # Verify the collection name uses the standard manual data collection name
        expected_collection_name = "manual_data"
        assert collection.name == expected_collection_name

    @pytest.mark.usefixtures("connection_with_manual_access_task", "group_condition")
    def test_manual_task_dependencies_from_group_conditions(
        self, db: Session, connection_with_manual_access_task
    ):
        """Test that manual tasks establish dependencies from group conditional dependencies"""
        connection_config, manual_task, _, _ = connection_with_manual_access_task

        # Create artificial graphs with the mock dataset graph
        graphs = create_manual_task_artificial_graphs(db)

        # Should have one graph for the manual task
        assert len(graphs) == 1

        graph = graphs[0]

        # Should have one collection per manual task
        assert len(graph.collections) == 1

        collection = graph.collections[0]

        # Verify that the collection has scalar fields with references to regular tasks
        # The group_condition fixture references both "customer.profile.age" and "payment_card.subscription.status"
        # which should create scalar fields with references to both "customer" and "payment_card" collections
        assert len(collection.fields) >= 2

        # Check that the scalar fields include the expected references
        expected_references = {
            FieldAddress("postgres_example", "customer", "profile.age"),
            FieldAddress("postgres_example", "payment_card", "subscription.status"),
        }

        found_references = set()
        for field in collection.fields:
            for ref, direction in field.references:
                found_references.add(ref)

        assert expected_references.issubset(found_references)

        # Verify the collection name uses the standard manual data collection name
        expected_collection_name = "manual_data"
        assert collection.name == expected_collection_name

    @pytest.mark.usefixtures(
        "connection_with_manual_access_task", "nested_group_condition"
    )
    def test_conditional_dependency_nested_group_fields_extraction(
        self,
        db: Session,
    ):
        """Test that field addresses are extracted from nested group conditional dependencies"""

        # Create artificial graphs with the mock dataset graph
        graphs = create_manual_task_artificial_graphs(db)

        # Should have one graph for the manual task
        assert len(graphs) == 1

        graph = graphs[0]
        collection = graph.collections[0]

        # Verify that field addresses from nested group children are included
        field_names = [field.name for field in collection.fields]

        # Should include conditional dependency fields from nested group children
        assert "postgres_example:customer:role" in field_names  # from "customer.role"
        assert (
            "postgres_example:customer:profile.age" in field_names
        )  # from "customer.profile.age"
        assert (
            "postgres_example:payment_card:subscription.status" in field_names
        )  # from "payment_card.subscription.status"

    @pytest.mark.usefixtures(
        "connection_with_manual_access_task", "condition_gt_18", "condition_age_lt_65"
    )
    def test_no_duplicate_fields_from_conditional_dependencies(
        self, db: Session, manual_task: ManualTask
    ):
        """Test that duplicate field addresses don't create duplicate fields"""

        # Create artificial graphs with the mock dataset graph
        graphs = create_manual_task_artificial_graphs(db)

        # Should have one graph for the manual task
        assert len(graphs) == 1

        graph = graphs[0]
        collection = graph.collections[0]

        # Verify that only one field is created for the duplicate field_address
        # The conditional dependencies use "customer.profile.age" which should create a field named "customer.profile.age"
        field_names = [field.name for field in collection.fields]
        profile_age_fields = [
            name
            for name in field_names
            if name == "postgres_example:customer:profile.age"
        ]

        assert (
            len(profile_age_fields) == 1
        )  # Should only have one "customer.profile.age" field

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
                "field_address": "postgres_example:payment_card:billing.subscription.status",
                "operator": "eq",
                "value": "active",
                "sort_order": 1,
            },
        )

        try:
            # Create artificial graphs with the mock dataset graph
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

            # Since we use 1:1 relationship, both collections use the same standard name
            expected_collection_name = "manual_data"

            assert first_collection.name == expected_collection_name
            assert second_collection.name == expected_collection_name

            # First task has no conditional dependencies, so only the dsr input field is present
            assert len(first_collection.fields) == 1

            # Second task has conditional dependency on billing.subscription.status, so has scalar field with reference
            assert len(second_collection.fields) == 1
            field = second_collection.fields[0]
            assert (
                field.name
                == "postgres_example:payment_card:billing.subscription.status"
            )
            assert len(field.references) == 1
            expected_reference = FieldAddress(
                "postgres_example", "payment_card", "billing.subscription.status"
            )
            assert field.references[0][0] == expected_reference
            assert field.references[0][1] == "from"

        finally:
            # Clean up
            second_manual_task.delete(db)
            second_connection_config.delete(db)
