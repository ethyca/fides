from typing import TYPE_CHECKING, List

from sqlalchemy.orm import Session

from fides.api.graph.config import (
    Collection,
    CollectionAddress,
    Field,
    GraphDataset,
    ScalarField,
)
from fides.api.graph.graph import Node
from fides.api.models.connectionconfig import ConnectionConfig

# Import application models
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskConfigurationType,
    ManualTaskEntityType,
    ManualTaskInstance,
)
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType

# TYPE_CHECKING import placed after all runtime imports to avoid lint issues
if TYPE_CHECKING:  # pragma: no cover
    from fides.api.graph.traversal import TraversalNode  # noqa: F401


class ManualTaskAddress:
    """Utility class for creating and parsing manual task addresses"""

    MANUAL_DATA_COLLECTION = "manual_data"

    @staticmethod
    def create(connection_config_key: str) -> CollectionAddress:
        """Create a CollectionAddress for manual data: {connection_key}:manual_data"""
        return CollectionAddress(
            dataset=connection_config_key,
            collection=ManualTaskAddress.MANUAL_DATA_COLLECTION,
        )

    @staticmethod
    def is_manual_task_address(address: CollectionAddress) -> bool:
        """Check if address represents manual task data"""
        if isinstance(address, str):
            # Handle string format "connection_key:collection_name"
            return address.endswith(f":{ManualTaskAddress.MANUAL_DATA_COLLECTION}")

        # Handle CollectionAddress object
        return address.collection == ManualTaskAddress.MANUAL_DATA_COLLECTION

    @staticmethod
    def get_connection_key(address: CollectionAddress) -> str:
        """Extract connection config key from manual task address"""
        if not ManualTaskAddress.is_manual_task_address(address):
            raise ValueError(f"Not a manual task address: {address}")

        if isinstance(address, str):
            # Handle string format "connection_key:collection_name"
            return address.split(":")[0]

        # Handle CollectionAddress object
        return address.dataset


def get_connection_configs_with_manual_tasks(db: Session) -> List[ConnectionConfig]:
    """
    Get all connection configs that have manual tasks.
    """
    return (
        db.query(ConnectionConfig)
        .join(ManualTask, ConnectionConfig.id == ManualTask.parent_entity_id)
        .filter(ManualTask.parent_entity_type == "connection_config")
        .filter(ConnectionConfig.disabled.is_(False))
        .all()
    )


def get_manual_task_addresses(db: Session) -> List[CollectionAddress]:
    """
    Get manual task addresses for all connection configs that have manual tasks.

    Note: Manual tasks should be included in the graph if they exist for any connection config
    that's part of the dataset graph, regardless of specific policy targets. This allows
    manual tasks to collect additional data that may be needed for the privacy request.
    """
    # Get all connection configs that have manual tasks (excluding disabled ones)
    connection_configs_with_manual_tasks = get_connection_configs_with_manual_tasks(db)

    # Create addresses for all connections that have manual tasks
    manual_task_addresses = []
    for config in connection_configs_with_manual_tasks:
        manual_task_addresses.append(ManualTaskAddress.create(config.key))

    return manual_task_addresses


def get_manual_tasks_for_connection_config(
    db: Session, connection_config_key: str
) -> List[ManualTask]:
    """Get all ManualTasks for a specific connection config"""
    connection_config = (
        db.query(ConnectionConfig)
        .filter(ConnectionConfig.key == connection_config_key)
        .first()
    )

    if not connection_config:
        return []

    return (
        db.query(ManualTask)
        .filter(
            ManualTask.parent_entity_id == connection_config.id,
            ManualTask.parent_entity_type == "connection_config",
        )
        .all()
    )


def create_manual_data_traversal_node(
    db: Session, address: CollectionAddress
) -> "TraversalNode":
    """
    Create a TraversalNode for a manual_data collection
    """
    connection_key = address.dataset

    # Get manual tasks for this connection to determine fields
    manual_tasks = get_manual_tasks_for_connection_config(db, connection_key)

    # Create fields based on ManualTaskConfigFields
    fields: List[Field] = []
    for manual_task in manual_tasks:
        for config in manual_task.configs:
            for field in config.field_definitions:
                # Create a scalar field for each manual task field
                # Extract data categories from field metadata if available
                field_metadata = field.field_metadata or {}
                data_categories = field_metadata.get("data_categories", [])

                scalar_field = ScalarField(
                    name=field.field_key,
                    data_categories=data_categories,
                    # Manual task fields don't have complex relationships
                )
                fields.append(scalar_field)

    # Create a synthetic Collection
    collection = Collection(
        name=ManualTaskAddress.MANUAL_DATA_COLLECTION,
        fields=fields,
        # Manual tasks don't have complex dependencies
        after=set(),
    )

    # Create a synthetic GraphDataset
    dataset = GraphDataset(
        name=connection_key,
        collections=[collection],
        connection_key=connection_key,
        after=set(),
    )

    # Create Node and TraversalNode (import locally to avoid cyclic import)
    from fides.api.graph.traversal import TraversalNode  # local import

    node = Node(dataset, collection)
    traversal_node = TraversalNode(node)

    return traversal_node


def create_manual_task_instances_for_privacy_request(
    db: Session, privacy_request: PrivacyRequest
) -> List[ManualTaskInstance]:
    """Create ManualTaskInstance entries for all active manual tasks relevant to a privacy request."""
    instances = []

    # Get all connection configs that have manual tasks (excluding disabled ones)
    connection_configs_with_manual_tasks = get_connection_configs_with_manual_tasks(db)

    # Determine the privacy request type based on policy rules
    has_access_rules = bool(
        privacy_request.policy.get_rules_for_action(action_type=ActionType.access)
    )
    has_erasure_rules = bool(
        privacy_request.policy.get_rules_for_action(action_type=ActionType.erasure)
    )

    for connection_config in connection_configs_with_manual_tasks:
        manual_tasks = (
            db.query(ManualTask)
            .filter(
                ManualTask.parent_entity_id == connection_config.id,
                ManualTask.parent_entity_type == "connection_config",
            )
            .all()
        )

        for manual_task in manual_tasks:
            # Get the active config for this manual task, filtered by request type
            active_config_query = db.query(ManualTaskConfig).filter(
                ManualTaskConfig.task_id == manual_task.id,
                ManualTaskConfig.is_current.is_(True),
            )

            # Filter by configuration type based on privacy request type
            if has_access_rules and has_erasure_rules:
                # If both access and erasure rules exist, include both types
                active_config_query = active_config_query.filter(
                    ManualTaskConfig.config_type.in_(
                        [
                            ManualTaskConfigurationType.access_privacy_request,
                            ManualTaskConfigurationType.erasure_privacy_request,
                        ]
                    ).filter(ManualTaskConfig.is_current.is_(True))
                )
            elif has_access_rules:
                # Only access rules - only include access configurations
                active_config_query = active_config_query.filter(
                    ManualTaskConfig.config_type
                    == ManualTaskConfigurationType.access_privacy_request
                )
            elif has_erasure_rules:
                # Only erasure rules - only include erasure configurations
                active_config_query = active_config_query.filter(
                    ManualTaskConfig.config_type
                    == ManualTaskConfigurationType.erasure_privacy_request
                )
            else:
                # No relevant rules - skip this manual task
                continue

            active_configs = active_config_query.all()

            if not active_configs:
                continue  # Skip if no active configs

            # Create instances for each active config
            for active_config in active_configs:
                # Check if instance already exists for this config
                existing_instance = (
                    db.query(ManualTaskInstance)
                    .filter(
                        ManualTaskInstance.entity_id == privacy_request.id,
                        ManualTaskInstance.entity_type == "privacy_request",
                        ManualTaskInstance.task_id == manual_task.id,
                        ManualTaskInstance.config_id == active_config.id,
                    )
                    .first()
                )

                if not existing_instance:
                    instance = ManualTaskInstance(
                        entity_id=privacy_request.id,
                        entity_type=ManualTaskEntityType.privacy_request,
                        task_id=manual_task.id,
                        config_id=active_config.id,
                    )
                    db.add(instance)
                    instances.append(instance)

    if instances:
        db.commit()

    return instances


def get_manual_task_instances_for_privacy_request(
    db: Session, privacy_request: PrivacyRequest
) -> List[ManualTaskInstance]:
    """Get all manual task instances for a privacy request."""
    return (
        db.query(ManualTaskInstance)
        .filter(
            ManualTaskInstance.entity_id == privacy_request.id,
            ManualTaskInstance.entity_type == "privacy_request",
        )
        .all()
    )


def create_manual_task_artificial_graphs(
    db: Session,
) -> List:
    """
    Create artificial GraphDataset objects for manual tasks that can be included
    in the main dataset graph during the dataset configuration phase.

    Manual tasks should be treated as data sources/datasets rather than being
    appended to the traversal graph later.

    Manual task collections are designed as root nodes that execute immediately when
    the privacy request starts, in parallel with identity processing. They don't depend
    on identity data since they provide manually-entered data rather than consuming it.

    Args:
        db: Database session
        policy: The policy being executed

    Returns:
        List of GraphDataset objects representing manual tasks as root nodes
    """

    manual_task_graphs = []
    manual_addresses = get_manual_task_addresses(db)

    for address in manual_addresses:
        connection_key = address.dataset

        # Get manual tasks for this connection to determine fields
        manual_tasks = get_manual_tasks_for_connection_config(db, connection_key)

        # Create fields based only on ManualTaskConfigFields
        fields: List = []

        # Manual task collections act as root nodes - they don't need identity dependencies
        # since they provide manually-entered data rather than consuming identity data.
        for manual_task in manual_tasks:
            for config in manual_task.configs:
                if config.config_type not in [
                    ManualTaskConfigurationType.access_privacy_request,
                    ManualTaskConfigurationType.erasure_privacy_request,
                ]:
                    continue
                if not config.is_current:
                    continue
                for field in config.field_definitions:
                    # Create a scalar field for each manual task field
                    field_metadata = field.field_metadata or {}
                    data_categories = field_metadata.get("data_categories", [])

                    scalar_field = ScalarField(
                        name=field.field_key,
                        data_categories=data_categories,
                    )
                    fields.append(scalar_field)

        if fields:  # Only create graph if there are fields
            # Create a synthetic Collection
            collection = Collection(
                name=ManualTaskAddress.MANUAL_DATA_COLLECTION,
                fields=fields,
                # Manual tasks have no dependencies - they're root nodes
                after=set(),
            )

            # Create a synthetic GraphDataset
            graph_dataset = GraphDataset(
                name=connection_key,
                collections=[collection],
                connection_key=connection_key,
                after=set(),
            )

            manual_task_graphs.append(graph_dataset)

    return manual_task_graphs
