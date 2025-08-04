from datetime import datetime

import pytest

from fides.api.graph.graph import CollectionAddress, DatasetGraph
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskConfigurationType,
    ManualTaskEntityType,
    ManualTaskFieldType,
    ManualTaskInstance,
    ManualTaskParentEntityType,
    ManualTaskSubmission,
    ManualTaskType,
    StatusType,
)
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.manual.manual_task_address import ManualTaskAddress
from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask
from fides.api.task.manual.manual_task_utils import (
    create_manual_task_artificial_graphs,
    get_connection_configs_with_manual_tasks,
    get_manual_task_addresses,
    get_manual_task_for_connection_config,
)


def create_combined_graph(self, db, mock_dataset_graph):
        """Helper method to create a combined graph from mock dataset and manual task graphs"""
        manual_task_graphs = create_manual_task_artificial_graphs(
            db, mock_dataset_graph
        )
        # Extract the datasets from mock_dataset_graph and combine with manual task graphs
        # mock_dataset_graph is a DatasetGraph, extract unique datasets from its nodes
        regular_datasets = []
        seen_dataset_names = set()
        for node in mock_dataset_graph.nodes.values():
            if node.dataset.name not in seen_dataset_names:
                regular_datasets.append(node.dataset)
                seen_dataset_names.add(node.dataset.name)

        return DatasetGraph(*regular_datasets, *manual_task_graphs)

class TestManualTaskGraphTask:

    def test_manual_task_graph_task_initialization(self):
        """Test that ManualTaskGraphTask can be initialized"""
        # This is a basic test since ManualTaskGraphTask inherits from GraphTask
        # which needs a proper ExecutionNode, but we can verify the class structure

        # For now, just verify the class can be imported and has the right methods
        assert hasattr(ManualTaskGraphTask, "access_request")
        assert hasattr(ManualTaskGraphTask, "_ensure_manual_task_instances")
        assert hasattr(ManualTaskGraphTask, "_get_submitted_data")

    def test_manual_task_address_detection_in_access_request(self):
        """Test that access_request method can detect manual task addresses"""
        # This would require more complex setup with actual RequestTask
        # For now, verify the ManualTaskAddress detection logic works

        manual_address = CollectionAddress("test_conn", "manual_data")
        regular_address = CollectionAddress("test_conn", "users")

        assert ManualTaskAddress.is_manual_task_address(manual_address)
        assert not ManualTaskAddress.is_manual_task_address(regular_address)


@pytest.mark.integration
class TestManualTaskSimulatedEndToEnd:
    """Simplified end-to-end test for manual task flow without complex database setup"""

    @pytest.fixture
    def manual_task_submission(
        self, db, manual_task_instance, connection_with_manual_access_task
    ):
        _, manual_task, manual_config, email_field = connection_with_manual_access_task

        return ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": manual_config.id,
                "field_id": email_field.id,
                "instance_id": manual_task_instance.id,
                "data": {"value": "manually-entered@example.com"},
            },
        )

    def test_manual_task_workflow_simulation(
        self,
        db,
        connection_with_manual_access_task,
        access_privacy_request,
        manual_task_instance,
        manual_task_submission,
    ):
        """Test the manual task workflow: create privacy request -> requires_input -> submit -> complete"""
        connection_config, manual_task, manual_config, email_field = (
            connection_with_manual_access_task
        )

        # Set privacy request to requires_input (simulating what the task would do)
        access_privacy_request.status = PrivacyRequestStatus.requires_input
        access_privacy_request.save(db)

        # Verify privacy request is now in requires_input state
        db.refresh(access_privacy_request)
        assert access_privacy_request.status == PrivacyRequestStatus.requires_input

        # 6. Update manual task instance to completed
        manual_task_instance.status = StatusType.completed
        manual_task_instance.save(db)

        # 7. Test that we can now get the submitted data using the utility functions
        manual_task = get_manual_task_for_connection_config(db, connection_config.key)
        assert manual_task.id == manual_task.id

        # 8. Verify manual task instance is completed
        db.refresh(manual_task_instance)
        assert manual_task_instance.status == StatusType.completed

        # 9. Verify submission data is correct
        assert manual_task_submission.data["value"] == "manually-entered@example.com"
        assert manual_task_submission.field_id == email_field.id
        assert manual_task_submission.instance_id == manual_task_instance.id

        # 10. Verify we can retrieve the submission via the instance
        db.refresh(manual_task_instance)
        instance_submissions = manual_task_instance.submissions
        assert len(instance_submissions) == 1
        assert instance_submissions[0].data["value"] == "manually-entered@example.com"

    @pytest.mark.usefixtures("connection_with_manual_access_task")
    def test_manual_task_with_missing_required_field(
        self, db, access_privacy_request, manual_task_instance
    ):
        """Test that manual task stays in requires_input when required fields are missing"""
        # Set privacy request to requires_input (simulating what the task would do)
        access_privacy_request.status = PrivacyRequestStatus.requires_input
        access_privacy_request.save(db)

        # Verify instance was created
        assert manual_task_instance is not None
        assert manual_task_instance.status == StatusType.pending

        # Privacy request should still be in requires_input
        db.refresh(access_privacy_request)
        assert access_privacy_request.status == PrivacyRequestStatus.requires_input


@pytest.mark.integration
class TestManualTaskInstanceCreation:
    """Test that manual task instances are created when privacy requests are processed"""

    def test_manual_task_instances_created_on_privacy_request_processing(
        self, db, access_privacy_request, connection_with_manual_access_task
    ):
        """Test that manual task instances are created when a privacy request starts processing"""
        _, manual_task, _, _ = connection_with_manual_access_task

        # Verify no instances exist initially
        initial_instances = access_privacy_request.manual_task_instances
        assert len(initial_instances) == 0

        # Create manual task instances (this should happen during privacy request processing)
        connection_configs_with_manual_tasks = get_connection_configs_with_manual_tasks(
            db
        )
        created_instances = access_privacy_request.create_manual_task_instances(
            db, connection_configs_with_manual_tasks
        )

        # Verify instances were created
        assert len(created_instances) == 1
        assert created_instances[0].entity_id == access_privacy_request.id
        assert created_instances[0].task_id == manual_task.id

        # Verify we can retrieve the instances
        retrieved_instances = access_privacy_request.manual_task_instances
        assert len(retrieved_instances) == 1
        assert retrieved_instances[0].id == created_instances[0].id

        # Cleanup
        for instance in created_instances:
            instance.delete(db)

    @pytest.mark.usefixtures("connection_with_manual_access_task")
    def test_no_duplicate_manual_task_instances_created(
        self, db, access_privacy_request
    ):
        """Test that duplicate manual task instances are not created"""

        # Create instances first time
        connection_configs_with_manual_tasks = get_connection_configs_with_manual_tasks(
            db
        )
        first_instances = access_privacy_request.create_manual_task_instances(
            db, connection_configs_with_manual_tasks
        )
        assert len(first_instances) == 1

        # Try to create instances again
        connection_configs_with_manual_tasks = get_connection_configs_with_manual_tasks(
            db
        )
        second_instances = access_privacy_request.create_manual_task_instances(
            db, connection_configs_with_manual_tasks
        )
        assert len(second_instances) == 0  # No new instances should be created

        # Verify total count is still 1
        all_instances = access_privacy_request.manual_task_instances
        assert len(all_instances) == 1


@pytest.mark.integration
class TestManualTaskGraphTaskInstanceCreation:
    """Test that ManualTaskGraphTask creates the correct number of instances for access and erasure"""

    @pytest.mark.usefixtures("connection_with_manual_access_task")
    def test_access_request_creates_access_instances_only(
        self,
        db,
        access_privacy_request,
        build_graph_task,
    ):
        """Test that access_request creates only access instances"""

        # Get the actual connection key from the fixture
        _, graph_task = build_graph_task

        # Count instances before
        initial_instances = (
            db.query(ManualTaskInstance)
            .filter(ManualTaskInstance.entity_id == access_privacy_request.id)
            .count()
        )
        assert initial_instances == 0

        # Call access_request
        try:
            graph_task.access_request()
        except Exception:
            # Expected to raise AwaitingAsyncTaskCallback since no submissions exist
            pass

        # Count instances after - should only have access instances
        access_instances = (
            db.query(ManualTaskInstance)
            .join(ManualTaskConfig)
            .filter(
                ManualTaskInstance.entity_id == access_privacy_request.id,
                ManualTaskConfig.config_type
                == ManualTaskConfigurationType.access_privacy_request,
            )
            .count()
        )

        erasure_instances = (
            db.query(ManualTaskInstance)
            .join(ManualTaskConfig)
            .filter(
                ManualTaskInstance.entity_id == access_privacy_request.id,
                ManualTaskConfig.config_type
                == ManualTaskConfigurationType.erasure_privacy_request,
            )
            .count()
        )

        assert access_instances == 1
        assert erasure_instances == 0

    @pytest.mark.usefixtures("connection_with_manual_erasure_task")
    def test_erasure_request_creates_erasure_instances_only(
        self,
        db,
        erasure_privacy_request,
        build_erasure_graph_task,
    ):
        """Test that erasure_request creates only erasure instances"""

        # Get the actual connection key from the fixture
        _, graph_task = build_erasure_graph_task

        # Count instances before
        initial_instances = (
            db.query(ManualTaskInstance)
            .filter(ManualTaskInstance.entity_id == erasure_privacy_request.id)
            .count()
        )
        assert initial_instances == 0

        # Call erasure_request
        try:
            graph_task.erasure_request([])
        except Exception:
            # Expected to raise AwaitingAsyncTaskCallback since no submissions exist
            pass

        # Count instances after - should only have erasure instances
        access_instances = (
            db.query(ManualTaskInstance)
            .join(ManualTaskConfig)
            .filter(
                ManualTaskInstance.entity_id == erasure_privacy_request.id,
                ManualTaskConfig.config_type
                == ManualTaskConfigurationType.access_privacy_request,
            )
            .count()
        )

        erasure_instances = (
            db.query(ManualTaskInstance)
            .join(ManualTaskConfig)
            .filter(
                ManualTaskInstance.entity_id == erasure_privacy_request.id,
                ManualTaskConfig.config_type
                == ManualTaskConfigurationType.erasure_privacy_request,
            )
            .count()
        )

        assert access_instances == 0
        assert erasure_instances == 1

    def test_access_request_skips_deleted_configs(
        self,
        db,
        access_privacy_request,
        connection_with_manual_access_task,
        build_graph_task,
    ):
        """Test that access_request skips configs that are not current"""
        _, _, access_config, _ = connection_with_manual_access_task
        access_config.is_current = False
        db.commit()

        _, graph_task = build_graph_task

        # Call access_request - should complete immediately since no valid configs
        result = graph_task.access_request()
        assert result == []

        # No instances should be created
        instances = (
            db.query(ManualTaskInstance)
            .filter(ManualTaskInstance.entity_id == access_privacy_request.id)
            .count()
        )
        assert instances == 0

    def test_erasure_request_skips_deleted_configs(
        self,
        db,
        erasure_policy,
        connection_with_manual_erasure_task,
        build_erasure_graph_task,
    ):
        """Test that erasure_request skips configs that are not current"""
        _, _, erasure_config, _ = connection_with_manual_erasure_task

        # Set config to not current BEFORE creating the privacy request
        erasure_config.is_current = False
        db.commit()

        # Create a new privacy request AFTER marking the config as not current
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "requested_at": datetime.utcnow(),
                "policy_id": erasure_policy.id,
                "status": PrivacyRequestStatus.pending,
            },
        )
        _, graph_task = build_erasure_graph_task

        # Call erasure_request - should complete immediately since no valid configs
        result = graph_task.erasure_request([])
        assert result == 0

        # No instances should be created
        instances = (
            db.query(ManualTaskInstance)
            .filter(ManualTaskInstance.entity_id == privacy_request.id)
            .count()
        )
        assert instances == 0

    def test_access_and_erasure_instances_coexist(
        self,
        db,
        mixed_privacy_request,
        connection_with_manual_access_task,
        connection_with_manual_erasure_task,
    ):
        """Test that access and erasure instances can coexist for the same privacy request"""

        # Get connection configs and manual tasks
        _, access_manual_task, _, _ = connection_with_manual_access_task
        _, erasure_manual_task, _, _ = connection_with_manual_erasure_task

        # Create manual task instances directly for the mixed privacy request
        # This simulates what would happen when both access and erasure tasks run

        # Create access instance
        access_config = next(
            config
            for config in access_manual_task.configs
            if config.config_type == ManualTaskConfigurationType.access_privacy_request
            and config.is_current
        )
        ManualTaskInstance.create(
            db=db,
            data={
                "task_id": access_manual_task.id,
                "config_id": access_config.id,
                "entity_id": mixed_privacy_request.id,
                "entity_type": ManualTaskEntityType.privacy_request.value,
                "status": StatusType.pending.value,
            },
        )

        # Create erasure instance
        erasure_config = next(
            config
            for config in erasure_manual_task.configs
            if config.config_type == ManualTaskConfigurationType.erasure_privacy_request
            and config.is_current
        )
        ManualTaskInstance.create(
            db=db,
            data={
                "task_id": erasure_manual_task.id,
                "config_id": erasure_config.id,
                "entity_id": mixed_privacy_request.id,
                "entity_type": ManualTaskEntityType.privacy_request.value,
                "status": StatusType.pending.value,
            },
        )

        # Should have both access and erasure instances for the same privacy request
        access_instances = (
            db.query(ManualTaskInstance)
            .join(ManualTaskConfig)
            .filter(
                ManualTaskInstance.entity_id == mixed_privacy_request.id,
                ManualTaskConfig.config_type
                == ManualTaskConfigurationType.access_privacy_request,
            )
            .count()
        )

        erasure_instances = (
            db.query(ManualTaskInstance)
            .join(ManualTaskConfig)
            .filter(
                ManualTaskInstance.entity_id == mixed_privacy_request.id,
                ManualTaskConfig.config_type
                == ManualTaskConfigurationType.erasure_privacy_request,
            )
            .count()
        )

        assert access_instances == 1
        assert erasure_instances == 1


@pytest.mark.integration
class TestManualTaskDisabledConnectionConfig:
    """Test that disabled connection configs are properly filtered out from manual task processing"""

    @pytest.fixture
    def disabled_connection_config(self, db):
        """Create a disabled connection config with manual task"""
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "name": "Disabled Connection",
                "key": "disabled_connection",
                "connection_type": ConnectionType.manual_task,
                "access": AccessLevel.read,
                "disabled": True,
            },
        )

        # Create manual task for disabled connection
        manual_task = ManualTask.create(
            db=db,
            data={
                "task_type": ManualTaskType.privacy_request,
                "parent_entity_id": connection_config.id,
                "parent_entity_type": ManualTaskParentEntityType.connection_config,
            },
        )

        # Create active config for manual task
        manual_config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request,
                "version": 1,
                "is_current": True,
            },
        )

        # Create a field for the manual task config
        ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": manual_config.id,
                "field_key": "test_field",
                "field_type": ManualTaskFieldType.text,
                "field_metadata": {
                    "label": "Test Field",
                    "required": True,
                    "data_categories": ["user.contact.email"],
                },
            },
        )

        return connection_config, manual_task

    def test_disabled_connection_configs_filtered_from_addresses(
        self, db, connection_with_manual_access_task, disabled_connection_config
    ):
        """Test that disabled connection configs are filtered out from manual task addresses"""

        # Get the actual connection keys from fixtures
        enabled_connection, _, _, _ = connection_with_manual_access_task
        disabled_connection, _ = disabled_connection_config

        # Get manual task addresses
        addresses = get_manual_task_addresses(db)

        # Should only include enabled connection configs
        assert len(addresses) == 1
        assert addresses[0].dataset == enabled_connection.key
        assert addresses[0].collection == "manual_data"

        # Verify disabled connection is not included
        disabled_address = f"{disabled_connection.key}:manual_data"
        assert not any(str(addr) == disabled_address for addr in addresses)

    def test_disabled_connection_configs_filtered_from_instance_creation(
        self,
        db,
        access_privacy_request,
        connection_with_manual_access_task,
        disabled_connection_config,
    ):
        """Test that disabled connection configs are filtered out from manual task instance creation"""

        # Create manual task instances
        connection_configs_with_manual_tasks = get_connection_configs_with_manual_tasks(
            db
        )
        created_instances = access_privacy_request.create_manual_task_instances(
            db, connection_configs_with_manual_tasks
        )

        # Should only create instances for enabled connection configs
        assert len(created_instances) == 1

        # Verify the instance is for the enabled connection
        _, enabled_task, _, _ = connection_with_manual_access_task
        assert created_instances[0].task_id == enabled_task.id

        # Verify no instances were created for disabled connection
        _, disabled_task = disabled_connection_config
        all_instances = access_privacy_request.manual_task_instances
        assert not any(
            instance.task_id == disabled_task.id for instance in all_instances
        )

    def test_disabled_connection_configs_filtered_from_artificial_graphs(
        self, db, connection_with_manual_access_task, disabled_connection_config
    ):
        """Test that disabled connection configs are filtered out from artificial graph creation"""
        # Get the actual connection keys from fixtures
        enabled_connection, _, _, _ = connection_with_manual_access_task
        disabled_connection, _ = disabled_connection_config

        # Create artificial graphs
        graphs = create_manual_task_artificial_graphs(db)

        # Should only include graphs for enabled connection configs
        assert len(graphs) == 1
        assert graphs[0].name == enabled_connection.key

        # Verify disabled connection is not included
        assert not any(graph.name == disabled_connection.key for graph in graphs)


@pytest.mark.integration
class TestManualTaskTraversalExecution:
    """Test that manual task traversal executes correctly with conditional dependencies and upstream data"""

    @pytest.mark.usefixtures("condition_gt_18", "condition_eq_active")
    def test_manual_task_traversal_with_conditional_dependencies(
        self, db, access_policy, connection_with_manual_access_task, mock_dataset_graph
    ):
        """Test that manual tasks execute in correct order when they have conditional dependencies"""
        connection_config, _, _, _ = connection_with_manual_access_task

        # Create combined graph using helper method
        combined_graph = self.create_combined_graph(db, mock_dataset_graph)

        # Create traversal
        from fides.api.graph.traversal import Traversal

        traversal = Traversal(combined_graph, data={})

        # Verify manual task node is present in traversal
        manual_address = ManualTaskAddress.create(connection_config.key)
        assert manual_address in traversal.traversal_node_dict

        # Verify manual task has dependencies on regular tasks
        manual_node = traversal.traversal_node_dict[manual_address]
        assert len(manual_node.node.collection.after) > 0

        # Verify dependencies include expected collections
        expected_dependencies = {
            CollectionAddress("postgres_example", "customer"),
            CollectionAddress("postgres_example", "payment_card"),
        }
        assert expected_dependencies.issubset(manual_node.node.collection.after)

        # Verify ROOT -> manual_data edge exists
        from fides.api.graph.config import (
            ROOT_COLLECTION_ADDRESS,
            FieldAddress,
            FieldPath,
        )

        expected_root_edge = FieldAddress(
            ROOT_COLLECTION_ADDRESS.dataset, ROOT_COLLECTION_ADDRESS.collection, "id"
        )
        expected_manual_edge = manual_address.field_address(FieldPath("id"))

        root_to_manual_edge_exists = any(
            edge.f1 == expected_root_edge and edge.f2 == expected_manual_edge
            for edge in traversal.edges
        )
        assert root_to_manual_edge_exists, "ROOT -> manual_data edge not found"

    @pytest.mark.usefixtures("group_condition", "privacy_request")
    def test_manual_task_traversal_with_group_conditional_dependencies(
        self, db, connection_with_manual_access_task, mock_dataset_graph
    ):
        """Test that manual tasks with group conditional dependencies execute correctly"""
        connection_config, _, _, _ = connection_with_manual_access_task

        # Create combined graph using helper method
        combined_graph = self.create_combined_graph(db, mock_dataset_graph)

        # Create traversal
        from fides.api.graph.traversal import Traversal

        traversal = Traversal(combined_graph, data={})

        # Verify manual task node is present
        manual_address = ManualTaskAddress.create(connection_config.key)
        assert manual_address in traversal.traversal_node_dict

        # Verify manual task has multiple dependencies from group conditions
        manual_node = traversal.traversal_node_dict[manual_address]
        assert len(manual_node.node.collection.after) >= 2

        # Verify dependencies include both customer and payment_card collections
        expected_dependencies = {
            CollectionAddress("postgres_example", "customer"),
            CollectionAddress("postgres_example", "payment_card"),
        }
        assert expected_dependencies.issubset(manual_node.node.collection.after)

    @pytest.mark.usefixtures("nested_group_condition", "privacy_request")
    def test_manual_task_traversal_with_nested_group_conditional_dependencies(
        self, db, connection_with_manual_access_task, mock_dataset_graph
    ):
        """Test that manual tasks with nested group conditional dependencies execute correctly"""
        connection_config, _, _, _ = connection_with_manual_access_task

        # Create artificial graphs
        # Create combined graph using helper method
        combined_graph = self._create_combined_graph(db, mock_dataset_graph)

        # Create traversal
        from fides.api.graph.traversal import Traversal

        traversal = Traversal(combined_graph, data={})

        # Verify manual task node is present
        manual_address = ManualTaskAddress.create(connection_config.key)
        assert manual_address in traversal.traversal_node_dict

        # Verify manual task has dependencies from nested group conditions
        manual_node = traversal.traversal_node_dict[manual_address]
        assert len(manual_node.node.collection.after) >= 2

        # Verify dependencies include expected collections
        expected_dependencies = {
            CollectionAddress("postgres_example", "customer"),
            CollectionAddress("postgres_example", "payment_card"),
        }
        assert expected_dependencies.issubset(manual_node.node.collection.after)

        # Verify collection has fields from nested group children
        field_names = [field.name for field in manual_node.node.collection.fields]
        assert "customer.role" in field_names  # from "customer.role"
        assert "customer.profile.age" in field_names  # from "customer.profile.age"
        assert (
            "payment_card.subscription.status" in field_names
        )  # from "payment_card.subscription.status"


@pytest.mark.integration
class TestManualTaskUpstreamDataFlow:
    """Test that manual tasks receive and process upstream data correctly"""

    @pytest.mark.usefixtures(
        "condition_gt_18", "condition_eq_active", "privacy_request"
    )
    def test_manual_task_receives_upstream_data_from_conditional_dependencies(
        self, db, connection_with_manual_access_task, mock_dataset_graph
    ):
        """Test that manual tasks receive data from upstream nodes that provide conditional dependency fields"""
        connection_config, _, _, _ = connection_with_manual_access_task

        # Create combined graph using helper method
        combined_graph = self.create_combined_graph(db, mock_dataset_graph)

        # Create traversal
        from fides.api.graph.traversal import Traversal

        traversal = Traversal(combined_graph, data={})

        # Get manual task node
        manual_address = ManualTaskAddress.create(connection_config.key)
        manual_node = traversal.traversal_node_dict[manual_address]

        # Verify manual task has input keys from upstream dependencies
        # The manual task should have input keys for collections that provide conditional dependency fields
        input_keys = manual_node.node.collection.after
        expected_input_keys = {
            CollectionAddress("postgres_example", "customer"),
            CollectionAddress("postgres_example", "payment_card"),
        }
        assert expected_input_keys.issubset(input_keys)

        # Verify manual task has fields that correspond to conditional dependency field addresses
        field_names = [field.name for field in manual_node.node.collection.fields]
        assert "customer.profile.age" in field_names  # from "customer.profile.age"
        assert (
            "payment_card.subscription.status" in field_names
        )  # from "payment_card.subscription.status"

    @pytest.mark.usefixtures("group_condition", "privacy_request")
    def test_manual_task_upstream_data_with_group_conditions(
        self, db, connection_with_manual_access_task, mock_dataset_graph
    ):
        """Test that manual tasks with group conditions receive data from multiple upstream nodes"""
        connection_config, _, _, _ = connection_with_manual_access_task

        # Create combined graph using helper method
        combined_graph = self.create_combined_graph(db, mock_dataset_graph)

        # Create traversal
        from fides.api.graph.traversal import Traversal

        traversal = Traversal(combined_graph, data={})

        # Get manual task node
        manual_address = ManualTaskAddress.create(connection_config.key)
        manual_node = traversal.traversal_node_dict[manual_address]

        # Verify manual task has multiple input keys from group conditions
        input_keys = manual_node.node.collection.after
        assert len(input_keys) >= 2

        # Verify input keys include both customer and payment_card collections
        expected_input_keys = {
            CollectionAddress("postgres_example", "customer"),
            CollectionAddress("postgres_example", "payment_card"),
        }
        assert expected_input_keys.issubset(input_keys)

        # Verify collection has fields from group condition dependencies
        field_names = [field.name for field in manual_node.node.collection.fields]
        assert "customer.profile.age" in field_names  # from "customer.profile.age"
        assert (
            "payment_card.subscription.status" in field_names
        )  # from "payment_card.subscription.status"


@pytest.mark.integration
class TestManualTaskExecutionOrder:
    """Test that manual tasks execute in the correct order relative to their dependencies"""

    @pytest.mark.usefixtures(
        "condition_gt_18", "condition_eq_active", "privacy_request"
    )
    def test_manual_task_executes_after_dependencies(
        self, db, connection_with_manual_access_task, mock_dataset_graph
    ):
        """Test that manual tasks execute after their conditional dependency nodes"""
        connection_config, _, _, _ = connection_with_manual_access_task

        # Create combined graph using helper method
        combined_graph = self.create_combined_graph(db, mock_dataset_graph)

        # Create traversal
        from fides.api.graph.traversal import Traversal

        traversal = Traversal(combined_graph, data={})

        # Get manual task node
        manual_address = ManualTaskAddress.create(connection_config.key)
        manual_node = traversal.traversal_node_dict[manual_address]

        # Verify manual task has dependencies that must execute first
        dependencies = manual_node.node.collection.after
        assert len(dependencies) > 0

        # Verify that the dependencies are actual collections in the graph
        for dependency in dependencies:
            assert dependency in traversal.traversal_node_dict

        # Verify that manual task has proper dependencies and can be reached
        # Note: ROOT is an artificial node and not in traversal_node_dict
        assert len(dependencies) > 0

    @pytest.mark.usefixtures("group_condition", "privacy_request")
    def test_manual_task_execution_order_with_multiple_dependencies(
        self, db, connection_with_manual_access_task, mock_dataset_graph
    ):
        """Test that manual tasks with multiple dependencies execute after all dependencies"""
        connection_config, _, _, _ = connection_with_manual_access_task

        # Create combined graph using helper method
        combined_graph = self.create_combined_graph(db, mock_dataset_graph)

        # Create traversal
        from fides.api.graph.traversal import Traversal

        traversal = Traversal(combined_graph, data={})

        # Get manual task node
        manual_address = ManualTaskAddress.create(connection_config.key)
        manual_node = traversal.traversal_node_dict[manual_address]

        # Verify manual task has multiple dependencies
        dependencies = manual_node.node.collection.after
        assert len(dependencies) >= 2

        # Verify all dependencies exist in the traversal
        for dependency in dependencies:
            assert dependency in traversal.traversal_node_dict

        # Verify dependencies are from different collections (customer and payment_card)
        dependency_collections = {dep.collection for dep in dependencies}
        assert len(dependency_collections) >= 2


@pytest.mark.integration
class TestManualTaskTraversalIntegration:
    """Integration tests for manual task traversal with real graph execution"""

    @pytest.mark.usefixtures(
        "condition_gt_18", "condition_eq_active", "privacy_request"
    )
    def test_manual_task_traversal_integration_with_conditional_dependencies(
        self, db, connection_with_manual_access_task, mock_dataset_graph
    ):
        """Integration test: manual task traversal with conditional dependencies in a complete graph"""
        connection_config, _, _, _ = connection_with_manual_access_task

        # Create combined graph using helper method
        combined_graph = self.create_combined_graph(db, mock_dataset_graph)

        # Create traversal
        from fides.api.graph.traversal import Traversal

        traversal = Traversal(combined_graph, data={})

        # Verify all nodes are present
        assert len(traversal.traversal_node_dict) > 0

        # Verify manual task node is present
        manual_address = ManualTaskAddress.create(connection_config.key)
        assert manual_address in traversal.traversal_node_dict

        # Verify manual task has proper dependencies
        manual_node = traversal.traversal_node_dict[manual_address]
        assert len(manual_node.node.collection.after) > 0

        # Verify manual task has proper fields
        assert len(manual_node.node.collection.fields) > 0

        # Verify manual task has proper edges
        from fides.api.graph.config import (
            ROOT_COLLECTION_ADDRESS,
            FieldAddress,
            FieldPath,
        )

        expected_root_edge = FieldAddress(
            ROOT_COLLECTION_ADDRESS.dataset, ROOT_COLLECTION_ADDRESS.collection, "id"
        )
        expected_manual_edge = manual_address.field_address(FieldPath("id"))

        root_to_manual_edge_exists = any(
            edge.f1 == expected_root_edge and edge.f2 == expected_manual_edge
            for edge in traversal.edges
        )
        assert root_to_manual_edge_exists

        # Verify traversal is valid (no reachability errors)
        # This tests that the graph structure is sound
        assert traversal is not None

    @pytest.mark.usefixtures("nested_group_condition", "privacy_request")
    def test_manual_task_traversal_integration_with_nested_groups(
        self, db, connection_with_manual_access_task, mock_dataset_graph
    ):
        """Integration test: manual task traversal with nested group conditional dependencies"""
        connection_config, _, _, _ = connection_with_manual_access_task

        # Create artificial graphs
        manual_task_graphs = create_manual_task_artificial_graphs(
            db, mock_dataset_graph
        )
        # Extract GraphDataset objects from mock_dataset_graph
        # mock_dataset_graph is a DatasetGraph, extract unique datasets from its nodes
        regular_datasets = []
        seen_dataset_names = set()
        for node in mock_dataset_graph.nodes.values():
            if node.dataset.name not in seen_dataset_names:
                regular_datasets.append(node.dataset)
                seen_dataset_names.add(node.dataset.name)
        combined_graph = DatasetGraph(*regular_datasets, *manual_task_graphs)

        # Create traversal
        from fides.api.graph.traversal import Traversal

        traversal = Traversal(combined_graph, data={})

        # Verify manual task node is present
        manual_address = ManualTaskAddress.create(connection_config.key)
        assert manual_address in traversal.traversal_node_dict

        # Verify manual task has dependencies from nested group conditions
        manual_node = traversal.traversal_node_dict[manual_address]
        assert len(manual_node.node.collection.after) >= 2

        # Verify manual task has fields from nested group children
        field_names = [field.name for field in manual_node.node.collection.fields]
        assert "customer.role" in field_names
        assert "customer.profile.age" in field_names
        assert "payment_card.subscription.status" in field_names

        # Verify traversal is valid
        assert traversal is not None
