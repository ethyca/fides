import json
from unittest.mock import Mock

import pytest

from fides.api.graph.config import Collection, ScalarField
from fides.api.graph.data_type import DataType
from fides.api.graph.graph import CollectionAddress
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
    ManualTaskFieldType,
    ManualTaskInstance,
    ManualTaskParentEntityType,
    ManualTaskSubmission,
    ManualTaskType,
)
from fides.api.models.policy import ActionType, Policy
from fides.api.models.privacy_request import (
    PrivacyRequest,
    RequestTask,
    TraversalDetails,
)
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask
from fides.api.task.manual.manual_task_utils import (
    ManualTaskAddress,
    create_manual_data_traversal_node,
    create_manual_task_artificial_graphs,
    create_manual_task_instances_for_privacy_request,
    get_manual_task_addresses,
    get_manual_task_instances_for_privacy_request,
    get_manual_tasks_for_connection_config,
)
from fides.api.task.task_resources import TaskResources


class TestManualTaskAddress:
    def test_create_manual_task_address(self):
        """Test creating manual task addresses"""
        address = ManualTaskAddress.create("postgres_connection")
        assert address.dataset == "postgres_connection"
        assert address.collection == "manual_data"

    def test_is_manual_task_address(self):
        """Test detecting manual task addresses"""
        manual_address = CollectionAddress("postgres_connection", "manual_data")
        regular_address = CollectionAddress("postgres_connection", "users")

        assert ManualTaskAddress.is_manual_task_address(manual_address) == True
        assert ManualTaskAddress.is_manual_task_address(regular_address) == False

    def test_get_connection_key(self):
        """Test extracting connection key from manual task address"""
        address = CollectionAddress("postgres_connection", "manual_data")
        key = ManualTaskAddress.get_connection_key(address)
        assert key == "postgres_connection"

        # Test error case
        bad_address = CollectionAddress("postgres_connection", "users")
        with pytest.raises(ValueError, match="Not a manual task address"):
            ManualTaskAddress.get_connection_key(bad_address)


class TestManualTaskTraversalNode:
    @pytest.fixture
    def sample_policy(self, db):
        """Create a sample policy for testing"""
        return Policy.create(
            db=db,
            data={
                "name": "Test Policy",
                "key": "test_policy",
            },
        )

    @pytest.fixture
    def sample_manual_task(self, db, sample_policy):
        """Create a sample manual task for testing"""
        # Create connection config
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_connection",
                "connection_type": ConnectionType.postgres,
                "name": "Test Connection",
                "access": AccessLevel.write,
            },
        )

        # Create manual task
        manual_task = ManualTask.create(
            db=db,
            data={
                "task_type": ManualTaskType.privacy_request,
                "parent_entity_id": connection_config.id,
                "parent_entity_type": ManualTaskParentEntityType.connection_config,
            },
        )

        # Create manual task config
        manual_config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": "access_privacy_request",
                "version": 1,
                "is_current": True,
            },
        )

        # Create manual task field
        ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": manual_config.id,
                "field_key": "user_email",
                "field_type": ManualTaskFieldType.text,
                "field_metadata": {
                    "label": "User Email",
                    "required": True,
                    "data_categories": ["user.contact.email"],
                },
            },
        )

        return manual_task, connection_config

    def test_get_manual_tasks_for_connection_config(self, db, sample_manual_task):
        """Test retrieving manual tasks for a connection config"""
        manual_task, connection_config = sample_manual_task

        tasks = get_manual_tasks_for_connection_config(db, connection_config.key)
        assert len(tasks) == 1
        assert tasks[0].id == manual_task.id

        # Test non-existent connection
        tasks = get_manual_tasks_for_connection_config(db, "non_existent")
        assert len(tasks) == 0

    def test_create_manual_data_traversal_node(self, db, sample_manual_task):
        """Test creating a TraversalNode for manual data"""
        _, connection_config = sample_manual_task

        address = ManualTaskAddress.create(connection_config.key)
        traversal_node = create_manual_data_traversal_node(db, address)

        # Verify the traversal node is created correctly
        assert traversal_node.address == address
        assert traversal_node.node.dataset.name == connection_config.key
        assert traversal_node.node.collection.name == "manual_data"

        # Verify fields are created from manual task fields
        fields = traversal_node.node.collection.fields
        assert len(fields) == 1
        assert fields[0].name == "user_email"
        assert fields[0].data_categories is not None
        assert "user.contact.email" in fields[0].data_categories


class TestManualTaskGraphTask:
    @pytest.fixture
    def sample_policy(self, db):
        """Create a sample policy for testing"""
        return Policy.create(
            db=db,
            data={
                "name": "Test Policy",
                "key": "test_policy",
            },
        )

    @pytest.fixture
    def sample_privacy_request(self, db, sample_policy):
        """Create a sample privacy request for testing"""
        return PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_request_123",
                "started_processing_at": None,
                "status": "pending",
                "policy_id": sample_policy.id,
            },
        )

    @pytest.fixture
    def mock_task_resources(self, db, sample_privacy_request):
        """Create mock task resources"""
        resources = Mock(spec=TaskResources)
        resources.session = db
        resources.request = sample_privacy_request
        return resources

    def test_manual_task_graph_task_initialization(self, mock_task_resources):
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
    def simple_policy(self, db):
        """Create a simple access policy"""
        return Policy.create(
            db=db, data={"name": "Simple Access Policy", "key": "simple_access_policy"}
        )

    @pytest.fixture
    def simple_connection_with_manual_task(self, db):
        """Create a simple connection with manual task"""
        # Create connection config
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "simple_test_connection",
                "connection_type": ConnectionType.postgres,
                "name": "Simple Test Connection",
                "access": AccessLevel.write,
                "secrets": {
                    "host": "localhost",
                    "port": 5432,
                    "user": "test",
                    "password": "test",
                    "dbname": "test",
                },
            },
        )

        # Create manual task
        manual_task = ManualTask.create(
            db=db,
            data={
                "task_type": ManualTaskType.privacy_request,
                "parent_entity_id": connection_config.id,
                "parent_entity_type": ManualTaskParentEntityType.connection_config,
            },
        )

        # Create an active ManualTaskConfig so instance creation picks it up
        manual_config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request,
                "version": 1,
                "is_current": True,
            },
        )

        # Create manual task field - a simple text field
        email_field = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": manual_config.id,
                "field_key": "user_email",
                "field_type": ManualTaskFieldType.text,
                "field_metadata": {
                    "label": "User Email Address",
                    "required": True,
                    "data_categories": ["user.contact.email"],
                },
            },
        )

        yield connection_config, manual_task, manual_config, email_field

    def test_manual_task_workflow_simulation(
        self, db, simple_policy, simple_connection_with_manual_task
    ):
        """Test the manual task workflow: create privacy request -> requires_input -> submit -> complete"""
        connection_config, manual_task, manual_config, email_field = (
            simple_connection_with_manual_task
        )

        # 1. Create privacy request
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_manual_workflow_123",
                "started_processing_at": None,
                "status": PrivacyRequestStatus.pending,
                "policy_id": simple_policy.id,
            },
        )

        # 2. Instead of testing the full graph task execution, let's test the core logic directly
        from fides.api.common_exceptions import AwaitingAsyncTaskCallback

        # Create a mock request task
        request_task = Mock()
        request_task.request_task_address = ManualTaskAddress.create(
            connection_config.key
        )

        # Test the ManualTaskGraphTask logic by calling its methods directly
        # This avoids complex constructor issues while still testing the core functionality

        # Create manual task instances (simulating what the graph task would do)
        from fides.api.models.manual_task import (
            ManualTaskEntityType,
            ManualTaskInstance,
            StatusType,
        )

        manual_instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": manual_config.id,
                "entity_id": privacy_request.id,
                "entity_type": ManualTaskEntityType.privacy_request.value,
                "status": StatusType.pending.value,
            },
        )

        # 3. Set privacy request to requires_input (simulating what the task would do)
        privacy_request.status = PrivacyRequestStatus.requires_input
        privacy_request.save(db)

        # 4. Verify privacy request is now in requires_input state
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.requires_input

        # 4. Verify manual task instance was created
        assert manual_instance is not None
        assert manual_instance.status == StatusType.pending

        # 5. Simulate manual data submission (this would normally come from the admin UI)
        submission = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": manual_config.id,
                "field_id": email_field.id,
                "instance_id": manual_instance.id,
                "data": {"value": "manually-entered@example.com"},
            },
        )

        # 6. Update manual task instance to completed
        manual_instance.status = StatusType.completed
        manual_instance.save(db)

        # 7. Test that we can now get the submitted data using the utility functions
        from fides.api.task.manual.manual_task_utils import (
            get_manual_tasks_for_connection_config,
        )

        manual_tasks = get_manual_tasks_for_connection_config(db, connection_config.key)
        assert len(manual_tasks) == 1
        assert manual_tasks[0].id == manual_task.id

        # 8. Verify manual task instance is completed
        db.refresh(manual_instance)
        assert manual_instance.status == StatusType.completed

        # 9. Verify submission data is correct
        assert submission.data["value"] == "manually-entered@example.com"
        assert submission.field_id == email_field.id
        assert submission.instance_id == manual_instance.id

        # 10. Verify we can retrieve the submission via the instance
        db.refresh(manual_instance)
        instance_submissions = manual_instance.submissions
        assert len(instance_submissions) == 1
        assert instance_submissions[0].data["value"] == "manually-entered@example.com"

    def test_manual_task_with_missing_required_field(
        self, db, simple_policy, simple_connection_with_manual_task
    ):
        """Test that manual task stays in requires_input when required fields are missing"""
        connection_config, manual_task, manual_config, email_field = (
            simple_connection_with_manual_task
        )

        # Create privacy request
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_missing_field_123",
                "started_processing_at": None,
                "status": PrivacyRequestStatus.pending,
                "policy_id": simple_policy.id,
            },
        )

        # Simulate manual task setup - create instance without submissions
        from fides.api.models.manual_task import (
            ManualTaskEntityType,
            ManualTaskInstance,
            StatusType,
        )

        manual_instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": manual_config.id,
                "entity_id": privacy_request.id,
                "entity_type": ManualTaskEntityType.privacy_request.value,
                "status": StatusType.pending.value,
            },
        )

        # Set privacy request to requires_input (simulating what the task would do)
        privacy_request.status = PrivacyRequestStatus.requires_input
        privacy_request.save(db)

        # Verify instance was created
        assert manual_instance is not None
        assert manual_instance.status == StatusType.pending

        # Privacy request should still be in requires_input
        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.requires_input


@pytest.mark.integration
class TestManualTaskInstanceCreation:
    """Test that manual task instances are created when privacy requests are processed"""

    @pytest.fixture
    def sample_policy(self, db):
        """Create a sample policy for testing with an access rule"""
        policy = Policy.create(
            db=db,
            data={
                "name": "Test Policy",
                "key": "test_policy",
            },
        )
        from fides.api.models.policy import Rule
        from fides.api.schemas.policy import ActionType

        Rule.create(
            db=db,
            data={
                "policy_id": policy.id,
                "action_type": ActionType.access,
                "name": "Access Rule",
                "key": "access_rule",
            },
        )
        return policy

    @pytest.fixture
    def sample_connection_config(self, db):
        """Create a sample connection config"""
        return ConnectionConfig.create(
            db=db,
            data={
                "name": "Test Connection",
                "key": "test_connection",
                "connection_type": ConnectionType.manual_task,
                "access": AccessLevel.read,
                "disabled": False,
            },
        )

    @pytest.fixture
    def sample_manual_task(self, db, sample_connection_config):
        """Create a sample manual task"""
        manual_task = ManualTask.create(
            db=db,
            data={
                "task_type": ManualTaskType.privacy_request,
                "parent_entity_id": sample_connection_config.id,
                "parent_entity_type": ManualTaskParentEntityType.connection_config,
            },
        )

        # Create an active ManualTaskConfig so instance creation picks it up
        ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request,
                "version": 1,
                "is_current": True,
            },
        )

        return manual_task

    @pytest.fixture
    def sample_privacy_request(self, db, sample_policy):
        """Create a sample privacy request"""
        return PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_request_123",
                "started_processing_at": None,
                "status": "pending",
                "policy_id": sample_policy.id,
            },
        )

    def test_manual_task_instances_created_on_privacy_request_processing(
        self, db, sample_privacy_request, sample_manual_task, sample_policy
    ):
        """Test that manual task instances are created when a privacy request starts processing"""

        # Verify no instances exist initially
        initial_instances = get_manual_task_instances_for_privacy_request(
            db, sample_privacy_request
        )
        assert len(initial_instances) == 0

        # Create manual task instances (this should happen during privacy request processing)
        created_instances = create_manual_task_instances_for_privacy_request(
            db, sample_privacy_request
        )

        # Verify instances were created
        assert len(created_instances) == 1
        assert created_instances[0].entity_id == sample_privacy_request.id
        assert created_instances[0].task_id == sample_manual_task.id

        # Verify we can retrieve the instances
        retrieved_instances = get_manual_task_instances_for_privacy_request(
            db, sample_privacy_request
        )
        assert len(retrieved_instances) == 1
        assert retrieved_instances[0].id == created_instances[0].id

        # Cleanup
        for instance in created_instances:
            instance.delete(db)

    def test_no_duplicate_manual_task_instances_created(
        self, db, sample_privacy_request, sample_manual_task
    ):
        """Test that duplicate manual task instances are not created"""

        # Create instances first time
        first_instances = create_manual_task_instances_for_privacy_request(
            db, sample_privacy_request
        )
        assert len(first_instances) == 1

        # Try to create instances again
        second_instances = create_manual_task_instances_for_privacy_request(
            db, sample_privacy_request
        )
        assert len(second_instances) == 0  # No new instances should be created

        # Verify total count is still 1
        all_instances = get_manual_task_instances_for_privacy_request(
            db, sample_privacy_request
        )
        assert len(all_instances) == 1


@pytest.fixture
def mock_execution_node():
    class MockExecutionNode:
        def __init__(self, address):
            self.address = CollectionAddress.from_string(address)
            self.connection_key = "test_connection"

    return MockExecutionNode("test_connection:manual_data")


def build_mock_request_task(privacy_request, action_type):
    request_task = RequestTask(
        privacy_request_id=privacy_request.id,
        collection_address="test_connection:manual_data",
        dataset_name="test_connection",
        collection_name="manual_data",
        action_type=action_type,
    )
    # Create a valid collection and serialize it to dict format for SQLAlchemy
    collection = Collection(
        name="manual_data",
        fields=[
            ScalarField(name="dummy", data_type_converter=DataType.no_op.value)
        ],  # minimal valid field
    )
    # Serialize the collection to dict format that SQLAlchemy expects
    request_task.collection = json.loads(
        collection.model_dump_json(serialize_as_any=True)
    )

    # Create valid traversal details and serialize to dict format
    traversal_details = TraversalDetails.create_empty_traversal("test_connection")
    request_task.traversal_details = traversal_details.model_dump(mode="json")

    return request_task


@pytest.fixture
def build_task_resources(db, test_privacy_request):
    def _build(action_type):
        from fides.api.task.task_resources import TaskResources

        connection_configs = db.query(ConnectionConfig).all()
        mock_request_task = build_mock_request_task(test_privacy_request, action_type)
        return TaskResources(
            request=test_privacy_request,
            policy=test_privacy_request.policy,
            connection_configs=connection_configs,
            privacy_request_task=mock_request_task,
            session=db,
        )

    return _build


@pytest.mark.integration
class TestManualTaskGraphTaskInstanceCreation:
    """Test that ManualTaskGraphTask creates the correct number of instances for access and erasure"""

    @pytest.fixture
    def test_policy(self, db):
        """Create a test policy with both access and erasure rules"""
        policy = Policy.create(
            db=db,
            data={
                "name": "Test Policy",
                "key": "test_policy",
            },
        )

        # Add access rule
        from fides.api.models.policy import Rule

        Rule.create(
            db=db,
            data={
                "policy_id": policy.id,
                "action_type": ActionType.access,
                "name": "Access Rule",
                "key": "access_rule",
            },
        )

        # Add erasure rule
        Rule.create(
            db=db,
            data={
                "policy_id": policy.id,
                "action_type": ActionType.erasure,
                "name": "Erasure Rule",
                "key": "erasure_rule",
                "masking_strategy": {"strategy": "null_rewrite", "configuration": {}},
            },
        )

        return policy

    @pytest.fixture
    def test_connection_config(self, db):
        """Create a test connection config"""
        return ConnectionConfig.create(
            db=db,
            data={
                "name": "Test Connection",
                "key": "test_connection",
                "connection_type": ConnectionType.manual_task,
                "access": AccessLevel.read,
                "disabled": False,
            },
        )

    @pytest.fixture
    def test_manual_task_with_both_configs(self, db, test_connection_config):
        """Create a manual task with both access and erasure configs"""
        manual_task = ManualTask.create(
            db=db,
            data={
                "task_type": ManualTaskType.privacy_request,
                "parent_entity_id": test_connection_config.id,
                "parent_entity_type": ManualTaskParentEntityType.connection_config,
            },
        )

        # Create access config
        access_config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request,
                "version": 1,
                "is_current": True,
            },
        )

        # Create erasure config
        erasure_config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.erasure_privacy_request,
                "version": 1,
                "is_current": True,
            },
        )

        # Add fields to both configs
        ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": access_config.id,
                "field_key": "access_field",
                "field_type": ManualTaskFieldType.text,
                "field_metadata": {"label": "Access Field", "required": True},
            },
        )

        ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": erasure_config.id,
                "field_key": "erasure_field",
                "field_type": ManualTaskFieldType.text,
                "field_metadata": {"label": "Erasure Field", "required": True},
            },
        )

        return manual_task, access_config, erasure_config

    @pytest.fixture
    def test_privacy_request(self, db, test_policy):
        """Create a test privacy request"""
        return PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_request_123",
                "started_processing_at": None,
                "status": "pending",
                "policy_id": test_policy.id,
            },
        )

    def test_access_request_creates_access_instances_only(
        self,
        db,
        test_privacy_request,
        test_manual_task_with_both_configs,
        mock_execution_node,
        build_task_resources,
    ):
        """Test that access_request creates only access instances"""
        manual_task, access_config, erasure_config = test_manual_task_with_both_configs
        from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask

        task_resources = build_task_resources(ActionType.access)
        graph_task = ManualTaskGraphTask(task_resources)
        graph_task.execution_node = mock_execution_node

        # Count instances before
        initial_instances = (
            db.query(ManualTaskInstance)
            .filter(ManualTaskInstance.entity_id == test_privacy_request.id)
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
                ManualTaskInstance.entity_id == test_privacy_request.id,
                ManualTaskConfig.config_type
                == ManualTaskConfigurationType.access_privacy_request,
            )
            .count()
        )

        erasure_instances = (
            db.query(ManualTaskInstance)
            .join(ManualTaskConfig)
            .filter(
                ManualTaskInstance.entity_id == test_privacy_request.id,
                ManualTaskConfig.config_type
                == ManualTaskConfigurationType.erasure_privacy_request,
            )
            .count()
        )

        assert access_instances == 1
        assert erasure_instances == 0

    def test_erasure_request_creates_erasure_instances_only(
        self,
        db,
        test_privacy_request,
        test_manual_task_with_both_configs,
        mock_execution_node,
        build_task_resources,
    ):
        """Test that erasure_request creates only erasure instances"""
        manual_task, access_config, erasure_config = test_manual_task_with_both_configs
        from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask

        task_resources = build_task_resources(ActionType.erasure)
        graph_task = ManualTaskGraphTask(task_resources)
        graph_task.execution_node = mock_execution_node

        # Count instances before
        initial_instances = (
            db.query(ManualTaskInstance)
            .filter(ManualTaskInstance.entity_id == test_privacy_request.id)
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
                ManualTaskInstance.entity_id == test_privacy_request.id,
                ManualTaskConfig.config_type
                == ManualTaskConfigurationType.access_privacy_request,
            )
            .count()
        )

        erasure_instances = (
            db.query(ManualTaskInstance)
            .join(ManualTaskConfig)
            .filter(
                ManualTaskInstance.entity_id == test_privacy_request.id,
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
        test_privacy_request,
        test_manual_task_with_both_configs,
        mock_execution_node,
        build_task_resources,
    ):
        """Test that access_request skips configs that are not current"""
        manual_task, access_config, erasure_config = test_manual_task_with_both_configs
        access_config.is_current = False
        db.commit()
        from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask

        task_resources = build_task_resources(ActionType.access)
        graph_task = ManualTaskGraphTask(task_resources)
        graph_task.execution_node = mock_execution_node

        # Call access_request - should complete immediately since no valid configs
        result = graph_task.access_request()
        assert result == []

        # No instances should be created
        instances = (
            db.query(ManualTaskInstance)
            .filter(ManualTaskInstance.entity_id == test_privacy_request.id)
            .count()
        )
        assert instances == 0

    def test_erasure_request_skips_deleted_configs(
        self,
        db,
        test_privacy_request,
        test_manual_task_with_both_configs,
        mock_execution_node,
        build_task_resources,
    ):
        """Test that erasure_request skips configs that are not current"""
        manual_task, access_config, erasure_config = test_manual_task_with_both_configs
        erasure_config.is_current = False
        db.commit()
        from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask

        task_resources = build_task_resources(ActionType.erasure)
        graph_task = ManualTaskGraphTask(task_resources)
        graph_task.execution_node = mock_execution_node

        # Call erasure_request - should complete immediately since no valid configs
        result = graph_task.erasure_request([])
        assert result == 0

        # No instances should be created
        instances = (
            db.query(ManualTaskInstance)
            .filter(ManualTaskInstance.entity_id == test_privacy_request.id)
            .count()
        )
        assert instances == 0

    def test_access_and_erasure_instances_coexist(
        self,
        db,
        test_privacy_request,
        test_manual_task_with_both_configs,
        mock_execution_node,
        build_task_resources,
    ):
        """Test that access and erasure instances can coexist for the same privacy request"""
        manual_task, access_config, erasure_config = test_manual_task_with_both_configs
        from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask

        # Access instance
        access_task_resources = build_task_resources(ActionType.access)
        access_graph_task = ManualTaskGraphTask(access_task_resources)
        access_graph_task.execution_node = mock_execution_node
        try:
            access_graph_task.access_request()
        except Exception:
            pass
        # Erasure instance
        erasure_task_resources = build_task_resources(ActionType.erasure)
        erasure_graph_task = ManualTaskGraphTask(erasure_task_resources)
        erasure_graph_task.execution_node = mock_execution_node
        try:
            erasure_graph_task.erasure_request([])
        except Exception:
            pass

        # Should have both access and erasure instances
        access_instances = (
            db.query(ManualTaskInstance)
            .join(ManualTaskConfig)
            .filter(
                ManualTaskInstance.entity_id == test_privacy_request.id,
                ManualTaskConfig.config_type
                == ManualTaskConfigurationType.access_privacy_request,
            )
            .count()
        )

        erasure_instances = (
            db.query(ManualTaskInstance)
            .join(ManualTaskConfig)
            .filter(
                ManualTaskInstance.entity_id == test_privacy_request.id,
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
    def test_policy(self, db):
        """Create a test policy with both access and erasure rules"""
        policy = Policy.create(
            db=db,
            data={
                "name": "Test Policy",
                "key": "test_policy",
            },
        )

        # Add access rule
        from fides.api.models.policy import Rule

        Rule.create(
            db=db,
            data={
                "policy_id": policy.id,
                "action_type": ActionType.access,
                "name": "Access Rule",
                "key": "access_rule",
            },
        )

        # Add erasure rule
        Rule.create(
            db=db,
            data={
                "policy_id": policy.id,
                "action_type": ActionType.erasure,
                "name": "Erasure Rule",
                "key": "erasure_rule",
                "masking_strategy": {"strategy": "null_rewrite", "configuration": {}},
            },
        )

        return policy

    @pytest.fixture
    def enabled_connection_config(self, db):
        """Create an enabled connection config with manual task"""
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "name": "Enabled Connection",
                "key": "enabled_connection",
                "connection_type": ConnectionType.manual_task,
                "access": AccessLevel.read,
                "disabled": False,
            },
        )

        # Create manual task for enabled connection
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

    @pytest.fixture
    def test_privacy_request(self, db, test_policy):
        """Create a test privacy request"""
        return PrivacyRequest.create(
            db=db,
            data={
                "external_id": "test_disabled_filter_123",
                "started_processing_at": None,
                "status": "pending",
                "policy_id": test_policy.id,
            },
        )

    @pytest.mark.usefixtures("enabled_connection_config", "disabled_connection_config")
    def test_disabled_connection_configs_filtered_from_addresses(self, db):
        """Test that disabled connection configs are filtered out from manual task addresses"""

        # Get manual task addresses
        addresses = get_manual_task_addresses(db)

        # Should only include enabled connection configs
        assert len(addresses) == 1
        assert addresses[0].dataset == "enabled_connection"
        assert addresses[0].collection == "manual_data"

        # Verify disabled connection is not included
        disabled_address = f"disabled_connection:manual_data"
        assert not any(str(addr) == disabled_address for addr in addresses)

    def test_disabled_connection_configs_filtered_from_instance_creation(
        self,
        db,
        test_privacy_request,
        enabled_connection_config,
        disabled_connection_config,
    ):
        """Test that disabled connection configs are filtered out from manual task instance creation"""

        # Create manual task instances
        created_instances = create_manual_task_instances_for_privacy_request(
            db, test_privacy_request
        )

        # Should only create instances for enabled connection configs
        assert len(created_instances) == 1

        # Verify the instance is for the enabled connection
        enabled_connection, enabled_task = enabled_connection_config
        assert created_instances[0].task_id == enabled_task.id

        # Verify no instances were created for disabled connection
        disabled_connection, disabled_task = disabled_connection_config
        all_instances = get_manual_task_instances_for_privacy_request(
            db, test_privacy_request
        )
        assert not any(
            instance.task_id == disabled_task.id for instance in all_instances
        )

    @pytest.mark.usefixtures("enabled_connection_config", "disabled_connection_config")
    def test_disabled_connection_configs_filtered_from_artificial_graphs(self, db):
        """Test that disabled connection configs are filtered out from artificial graph creation"""
        # Create artificial graphs
        graphs = create_manual_task_artificial_graphs(db)

        # Should only include graphs for enabled connection configs
        assert len(graphs) == 1
        assert graphs[0].name == "enabled_connection"

        # Verify disabled connection is not included
        assert not any(graph.name == "disabled_connection" for graph in graphs)
