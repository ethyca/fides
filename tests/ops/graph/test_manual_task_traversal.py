"""Tests for manual task traversal functionality."""

import pytest
from sqlalchemy.orm import Session

from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfig
from fides.api.models.policy import Policy
from fides.api.schemas.manual_tasks.manual_task_config import ManualTaskConfigurationType
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    MANUAL_TASK_COLLECTIONS,
    ManualTaskExecutionTiming,
    ManualTaskParentEntityType,
)
from fides.api.graph.traversal import Traversal


@pytest.fixture
def manual_task(db: Session, connection_config: ConnectionConfig) -> ManualTask:
    """Create a manual task for testing."""
    return ManualTask.create(
        db=db,
        data={
            "task_type": "privacy_request",
            "parent_entity_id": connection_config.id,
            "parent_entity_type": ManualTaskParentEntityType.connection_config,
        },
    )


@pytest.fixture
def pre_execution_config(db: Session, manual_task: ManualTask) -> ManualTaskConfig:
    """Create a pre-execution manual task config."""
    return ManualTaskConfig.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_type": ManualTaskConfigurationType.access_privacy_request,
            "execution_timing": ManualTaskExecutionTiming.pre_execution,
            "is_current": True,
        },
    )


@pytest.fixture
def post_execution_config(db: Session, manual_task: ManualTask) -> ManualTaskConfig:
    """Create a post-execution manual task config."""
    return ManualTaskConfig.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_type": ManualTaskConfigurationType.access_privacy_request,
            "execution_timing": ManualTaskExecutionTiming.post_execution,
            "is_current": True,
        },
    )


@pytest.fixture
def simple_dataset_graph() -> DatasetGraph:
    """Create a simple dataset graph for testing."""
    from fides.api.graph.config import Collection, Field, GraphDataset

    # Create a simple collection with identity data
    user_collection = Collection(
        name="users",
        fields=[
            Field(name="id", data_categories=["user.identifiable.contact.email"]),
            Field(name="email", data_categories=["user.identifiable.contact.email"]),
        ],
    )

    dataset = GraphDataset(
        name="test_dataset",
        collections=[user_collection],
        connection_key="test_connection",
    )

    return DatasetGraph(dataset)


class TestManualTaskTraversalHelpers:
    """Test the helper functions for manual task traversal."""

    def test_get_manual_tasks(self, db: Session, manual_task: ManualTask):
        """Test getting manual tasks from database."""
        traversal = Traversal(DatasetGraph(), {}, session=db)
        tasks = traversal._get_manual_tasks(db)

        assert len(tasks) >= 1
        task_ids = [task.id for task in tasks]
        assert manual_task.id in task_ids

    def test_get_manual_tasks_no_tasks(self, db: Session):
        """Test getting manual tasks when none exist."""
        traversal = Traversal(DatasetGraph(), {}, session=db)
        tasks = traversal._get_manual_tasks(db)
        assert len(tasks) == 0

    def test_get_connection_config_success(self, db: Session, manual_task: ManualTask, connection_config: ConnectionConfig):
        """Test successful connection config retrieval."""
        traversal = Traversal(DatasetGraph(), {}, session=db)
        result = traversal._get_connection_config(db, manual_task)

        assert result is not None
        assert result.id == connection_config.id
        assert result.key == connection_config.key

    def test_get_connection_config_not_found(self, db: Session):
        """Test connection config retrieval when not found."""
        # Create a manual task with non-existent connection config
        manual_task = ManualTask.create(
            db=db,
            data={
                "task_type": "privacy_request",
                "parent_entity_id": "non-existent-id",
                "parent_entity_type": ManualTaskParentEntityType.connection_config,
            },
        )

        traversal = Traversal(DatasetGraph(), {}, session=db)
        result = traversal._get_connection_config(db, manual_task)
        assert result is None

    def test_create_manual_node(self, simple_dataset_graph: DatasetGraph, connection_config: ConnectionConfig, post_execution_config: ManualTaskConfig):
        """Test creating a manual task node."""
        traversal = Traversal(simple_dataset_graph, {}, session=None)
        manual_address = traversal._create_manual_node(simple_dataset_graph, connection_config, post_execution_config)

        assert manual_address.dataset == connection_config.key
        assert manual_address.collection == "post_execution"
        assert manual_address in simple_dataset_graph.nodes

    def test_get_first_data_nodes(self, simple_dataset_graph: DatasetGraph):
        """Test getting first data nodes with identity data."""
        # Add identity key mapping
        simple_dataset_graph.identity_keys = {
            CollectionAddress("test_dataset", "users"): "email"
        }

        traversal = Traversal(simple_dataset_graph, {}, session=None)
        data = {"email": "test@example.com"}
        first_nodes = traversal._get_first_data_nodes(simple_dataset_graph, data)

        assert len(first_nodes) == 1
        assert first_nodes[0] == CollectionAddress("test_dataset", "users")

    def test_get_first_data_nodes_no_identity_data(self, simple_dataset_graph: DatasetGraph):
        """Test getting first data nodes when no identity data is provided."""
        # Add identity key mapping
        simple_dataset_graph.identity_keys = {
            CollectionAddress("test_dataset", "users"): "email"
        }

        traversal = Traversal(simple_dataset_graph, {}, session=None)
        data = {"other_field": "value"}
        first_nodes = traversal._get_first_data_nodes(simple_dataset_graph, data)

        assert len(first_nodes) == 0

    def test_get_data_nodes(self, simple_dataset_graph: DatasetGraph, connection_config: ConnectionConfig):
        """Test getting data nodes excluding manual task nodes."""
        traversal = Traversal(simple_dataset_graph, {}, session=None)
        manual_address = CollectionAddress(connection_config.key, "post_execution")

        data_nodes = traversal._get_data_nodes(simple_dataset_graph, manual_address)

        # Should include the users collection but not manual task nodes
        expected_nodes = [CollectionAddress("test_dataset", "users")]
        assert data_nodes == expected_nodes

    def test_get_data_nodes_excludes_manual_nodes(self, simple_dataset_graph: DatasetGraph, connection_config: ConnectionConfig):
        """Test that get_data_nodes excludes manual task nodes."""
        # Add a manual task node to the graph
        manual_address = CollectionAddress(connection_config.key, "post_execution")
        from fides.api.graph.config import Collection
        manual_collection = Collection(name="post_execution", fields=[])
        simple_dataset_graph.nodes[manual_address] = manual_collection

        traversal = Traversal(simple_dataset_graph, {}, session=None)
        data_nodes = traversal._get_data_nodes(simple_dataset_graph, manual_address)

        # Should not include the manual task node
        assert manual_address not in data_nodes


class TestManualTaskEdgeCreation:
    """Test manual task edge creation functionality."""

    def test_add_pre_execution_edges(self, simple_dataset_graph: DatasetGraph, connection_config: ConnectionConfig):
        """Test adding pre-execution edges."""
        # Add identity key mapping
        simple_dataset_graph.identity_keys = {
            CollectionAddress("test_dataset", "users"): "email"
        }

        traversal = Traversal(simple_dataset_graph, {}, session=None)
        manual_address = CollectionAddress(connection_config.key, "pre_execution")

        # Add the manual node to the graph first
        from fides.api.graph.config import Collection
        manual_collection = Collection(name="pre_execution", fields=[])
        simple_dataset_graph.nodes[manual_address] = manual_collection

        data = {"email": "test@example.com"}
        traversal._add_pre_execution_edges(simple_dataset_graph, data, manual_address)

        # Check that edges were created
        edges = list(simple_dataset_graph.edges)
        assert len(edges) >= 2  # Root to manual, manual to data nodes

    def test_add_post_execution_edges(self, simple_dataset_graph: DatasetGraph, connection_config: ConnectionConfig):
        """Test adding post-execution edges."""
        traversal = Traversal(simple_dataset_graph, {}, session=None)
        manual_address = CollectionAddress(connection_config.key, "post_execution")

        # Add the manual node to the graph first
        from fides.api.graph.config import Collection
        manual_collection = Collection(name="post_execution", fields=[])
        simple_dataset_graph.nodes[manual_address] = manual_collection

        traversal._add_post_execution_edges(simple_dataset_graph, manual_address)

        # Check that edges were created
        edges = list(simple_dataset_graph.edges)
        assert len(edges) >= 2  # Data nodes to manual, manual to terminator


class TestManualTaskTraversalIntegration:
    """Test the complete manual task traversal integration."""

    def test_traversal_with_manual_tasks(self, db: Session, simple_dataset_graph: DatasetGraph, manual_task: ManualTask, pre_execution_config: ManualTaskConfig, post_execution_config: ManualTaskConfig):
        """Test that traversal includes manual task nodes when session is provided."""
        # Add identity key mapping
        simple_dataset_graph.identity_keys = {
            CollectionAddress("test_dataset", "users"): "email"
        }

        data = {"email": "test@example.com"}
        traversal = Traversal(simple_dataset_graph, data, session=db)

        # Check that manual task nodes were added
        manual_nodes = [
            addr for addr in traversal.graph.nodes.keys()
            if addr.collection in MANUAL_TASK_COLLECTIONS.values()
        ]
        assert len(manual_nodes) == 2  # pre_execution and post_execution

        # Check that edges were created
        edges = list(traversal.graph.edges)
        assert len(edges) > 0

    def test_traversal_without_session(self, simple_dataset_graph: DatasetGraph):
        """Test that traversal doesn't include manual task nodes when no session is provided."""
        data = {"email": "test@example.com"}
        traversal = Traversal(simple_dataset_graph, data, session=None)

        # Check that no manual task nodes were added
        manual_nodes = [
            addr for addr in traversal.graph.nodes.keys()
            if addr.collection in MANUAL_TASK_COLLECTIONS.values()
        ]
        assert len(manual_nodes) == 0

    def test_traversal_with_multiple_manual_tasks(self, db: Session, simple_dataset_graph: DatasetGraph):
        """Test traversal with multiple manual tasks."""
        # Create multiple connection configs with manual tasks
        configs = []
        for i in range(2):
            config = ConnectionConfig.create(
                db=db,
                data={
                    "key": f"connection_{i}",
                    "name": f"Connection {i}",
                    "connection_type": "postgres",
                },
            )
            configs.append(config)

            # Create manual task for each config
            manual_task = ManualTask.create(
                db=db,
                data={
                    "task_type": "privacy_request",
                    "parent_entity_id": config.id,
                    "parent_entity_type": ManualTaskParentEntityType.connection_config,
                },
            )

            # Create configs for each task
            for timing in [ManualTaskExecutionTiming.pre_execution, ManualTaskExecutionTiming.post_execution]:
                ManualTaskConfig.create(
                    db=db,
                    data={
                        "task_id": manual_task.id,
                        "config_type": ManualTaskConfigurationType.access_privacy_request,
                        "execution_timing": timing,
                        "is_current": True,
                    },
                )

        # Add identity key mapping
        simple_dataset_graph.identity_keys = {
            CollectionAddress("test_dataset", "users"): "email"
        }

        data = {"email": "test@example.com"}
        traversal = Traversal(simple_dataset_graph, data, session=db)

        # Check that manual task nodes were added for each connection
        manual_nodes = [
            addr for addr in traversal.graph.nodes.keys()
            if addr.collection in MANUAL_TASK_COLLECTIONS.values()
        ]
        assert len(manual_nodes) == 4  # 2 connections * 2 timings

    def test_traversal_manual_task_node_creation(self, db: Session, simple_dataset_graph: DatasetGraph, manual_task: ManualTask, pre_execution_config: ManualTaskConfig, post_execution_config: ManualTaskConfig):
        """Test that manual task nodes are created correctly."""
        # Add identity key mapping
        simple_dataset_graph.identity_keys = {
            CollectionAddress("test_dataset", "users"): "email"
        }

        data = {"email": "test@example.com"}
        traversal = Traversal(simple_dataset_graph, data, session=db)

        # Check that nodes have correct dataset and collection names
        for timing in MANUAL_TASK_COLLECTIONS.values():
            node_address = CollectionAddress(manual_task.parent_entity_id, timing)
            assert node_address in traversal.graph.nodes

            # Check that the node has the correct connection key
            node = traversal.graph.nodes[node_address]
            assert node.dataset.connection_key == manual_task.parent_entity_id


class TestManualTaskTraversalEdgeCases:
    """Test edge cases in manual task traversal."""

    def test_traversal_with_invalid_connection_config(self, db: Session, simple_dataset_graph: DatasetGraph):
        """Test traversal when manual task has invalid connection config."""
        # Create manual task with non-existent connection config
        manual_task = ManualTask.create(
            db=db,
            data={
                "task_type": "privacy_request",
                "parent_entity_id": "non-existent-id",
                "parent_entity_type": ManualTaskParentEntityType.connection_config,
            },
        )

        # Create config for the task
        ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request,
                "execution_timing": ManualTaskExecutionTiming.post_execution,
                "is_current": True,
            },
        )

        data = {"email": "test@example.com"}
        # Should not raise an exception, just skip the invalid task
        traversal = Traversal(simple_dataset_graph, data, session=db)

        # Check that no manual task nodes were added for the invalid task
        manual_nodes = [
            addr for addr in traversal.graph.nodes.keys()
            if addr.collection in MANUAL_TASK_COLLECTIONS.values()
        ]
        assert len(manual_nodes) == 0

    def test_traversal_with_no_manual_task_configs(self, db: Session, simple_dataset_graph: DatasetGraph, manual_task: ManualTask):
        """Test traversal when manual task has no configs."""
        data = {"email": "test@example.com"}
        traversal = Traversal(simple_dataset_graph, data, session=db)

        # Check that no manual task nodes were added
        manual_nodes = [
            addr for addr in traversal.graph.nodes.keys()
            if addr.collection in MANUAL_TASK_COLLECTIONS.values()
        ]
        assert len(manual_nodes) == 0
