from typing import Optional

from sqlalchemy.orm import Session

from fides.api.graph.config import (
    Collection,
    CollectionAddress,
    FieldAddress,
    FieldPath,
    GraphDataset,
    ScalarField,
)
from fides.api.graph.graph import DatasetGraph
from fides.api.models.connectionconfig import ConnectionConfig

# Import application models
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConditionalDependencyType,
    ManualTaskConfigurationType,
)
from fides.api.task.manual.manual_task_address import ManualTaskAddress

PRIVACY_REQUEST_CONFIG_TYPES = {
    ManualTaskConfigurationType.access_privacy_request,
    ManualTaskConfigurationType.erasure_privacy_request,
}


def get_connection_configs_with_manual_tasks(db: Session) -> list[ConnectionConfig]:
    """
    Get all connection configs that have manual tasks.
    """
    connection_configs = (
        db.query(ConnectionConfig)
        .join(ManualTask, ConnectionConfig.id == ManualTask.parent_entity_id)
        .filter(ManualTask.parent_entity_type == "connection_config")
        .filter(ConnectionConfig.disabled.is_(False))
        .all()
    )
    return connection_configs


def get_manual_task_addresses(db: Session) -> list[CollectionAddress]:
    """
    Get manual task addresses for all connection configs that have manual tasks.

    Note: Manual tasks should be included in the graph if they exist for any connection config
    that's part of the dataset graph, regardless of specific policy targets. This allows
    manual tasks to collect additional data that may be needed for the privacy request.
    """
    # Get all connection configs that have manual tasks (excluding disabled ones)
    connection_configs_with_manual_tasks = get_connection_configs_with_manual_tasks(db)

    # Return addresses for all connections that have manual tasks
    return [
        ManualTaskAddress.create(config.key)
        for config in connection_configs_with_manual_tasks
    ]


def get_manual_task_for_connection_config(
    db: Session, connection_config_key: str
) -> ManualTask:
    """Get the ManualTask for a specific connection config,
    the manual task/connection config relationship is 1:1.
    """
    return (
        db.query(ManualTask)
        .join(ConnectionConfig, ManualTask.parent_entity_id == ConnectionConfig.id)
        .filter(
            ConnectionConfig.key == connection_config_key,
            ManualTask.parent_entity_type == "connection_config",
        )
        .one_or_none()
    )


def create_data_category_scalar_fields(manual_task: ManualTask) -> list[ScalarField]:
    """
    Create scalar fields for each field in the given manual task configs.
    """
    fields = []
    # Get current privacy request configs for this manual task
    current_configs = [
        config
        for config in manual_task.configs
        if config.is_current and config.config_type in PRIVACY_REQUEST_CONFIG_TYPES
    ]
    for config in current_configs:
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
    return fields


def create_conditional_dependency_scalar_fields(
    field_addresses: set[str],
) -> list[ScalarField]:
    fields = []
    for field_address in field_addresses:
        # Use the full field address as the field name to preserve collection context
        # This allows the manual task to receive data from specific collections
        # e.g., "user.name" or "customer.profile.email" instead of just "name" or "email"
        scalar_field = ScalarField(
            name=field_address,
            # Conditional dependency fields don't have predefined data categories
            data_categories=[],
        )
        fields.append(scalar_field)

    return fields


def create_collection_for_connection_key(
    db: Session, connection_key: str, dataset_graph: Optional["DatasetGraph"] = None
) -> Optional[Collection]:
    # Get the manual task for this connection config
    manual_task = get_manual_task_for_connection_config(db, connection_key)

    if not manual_task:
        return None

    # Get conditional dependency field addresses - raw field data
    conditional_field_addresses: set[str] = {
        dependency.field_address
        for dependency in manual_task.conditional_dependencies
        if dependency.condition_type == ManualTaskConditionalDependencyType.leaf
        and dependency.field_address is not None
    }

    # Find collections that provide the fields referenced in conditional dependencies - determines execution order
    dependency_collections: set[CollectionAddress] = (
        _find_collections_for_conditional_dependencies(manual_task, dataset_graph)
    )

    # Create scalar fields for data category fields and conditional dependency field addresses
    fields: list[ScalarField] = []
    fields.extend(create_data_category_scalar_fields(manual_task))
    fields.extend(
        create_conditional_dependency_scalar_fields(conditional_field_addresses)
    )

    # Only create collection if there are fields
    if not fields:
        return None

    return Collection(
        name=ManualTaskAddress.MANUAL_DATA_COLLECTION,
        fields=fields,
        # Manual task has dependencies on regular tasks that provide conditional dependency fields
        after=dependency_collections,
    )


def create_manual_task_artificial_graphs(
    db: Session, dataset_graph: Optional["DatasetGraph"] = None
) -> list:
    """
    Create artificial GraphDataset objects for manual tasks that can be included
    in the main dataset graph during the dataset configuration phase.

    Each manual task gets its own collection with its own dependencies based on
    its specific conditional dependencies. This allows individual manual tasks
    to receive only the data they need from regular tasks.

    Args:
        db: Database session
        dataset_graph: The actual graph being executed (optional for backward compatibility)

    Returns:
        List of GraphDataset objects representing manual tasks as individual collections
    """
    manual_task_graphs = []
    manual_addresses = get_manual_task_addresses(db)

    for address in manual_addresses:
        connection_key = address.dataset

        # Get the collection for this connection config using the reusable function
        collection = create_collection_for_connection_key(
            db, connection_key, dataset_graph
        )

        if collection:  # Only create graph if there are collections
            # Create a synthetic GraphDataset with all manual task collections
            # The graph should inherit dependencies from its collections
            # Convert CollectionAddress objects to strings for GraphDataset.after
            after_dependencies = {str(addr) for addr in collection.after}
            graph_dataset = GraphDataset(
                name=connection_key,
                collections=[collection],
                connection_key=connection_key,
                after=after_dependencies,
            )

            manual_task_graphs.append(graph_dataset)

    return manual_task_graphs


def _find_collections_for_conditional_dependencies(
    manual_task: ManualTask, dataset_graph: Optional["DatasetGraph"] = None
) -> set[CollectionAddress]:
    """
    Find collections that provide fields referenced in conditional dependencies.

    This function analyzes the conditional dependencies of a manual task and
    identifies which regular task collections need to be executed before the
    manual task to provide the required field data.

    Args:
        manual_task: The manual task to analyze
        dataset_graph: The actual graph being executed (optional for backward compatibility)

    Returns:
        Set of CollectionAddress objects for collections that provide conditional dependency fields
    """
    dependency_collections: set[CollectionAddress] = set()
    if not dataset_graph:
        return dependency_collections

    conditional_dependencies = [
        dep
        for dep in manual_task.conditional_dependencies
        if dep.condition_type == ManualTaskConditionalDependencyType.leaf
        and dep.field_address is not None
    ]

    for dependency in conditional_dependencies:
        # Parse the field address to determine which collection provides this field
        if dependency.field_address is None:
            continue
        collection_address = _get_collection_for_field_address(
            dependency.field_address, dataset_graph
        )
        if collection_address:
            dependency_collections.add(collection_address)

    return dependency_collections


def _get_collection_for_field_address(
    field_address: str,
    dataset_graph: DatasetGraph,
) -> Optional[CollectionAddress]:
    """
    Determine which collection provides a given field address.

    This function parses the field address to determine which collection provides
    the specified field. Field addresses can be in two formats:
    1. Full format: "dataset:collection:field" (e.g., "postgres_example_test_dataset:customer:name")
    2. Simplified format: "collection.field" (e.g., "customer.name", "user.profile.age")

    Args:
        field_address: The field address to analyze
        dataset_graph: The actual graph being executed

    Returns:
        CollectionAddress for the collection that provides this field, or None if not found
    """
    if not field_address:
        return None

    # Try to parse as full field address format first (dataset:collection:field)
    if ":" in field_address:
        return _parse_full_address_format(field_address, dataset_graph)

    # Fall back to simplified format parsing (collection.field)
    if "." not in field_address:
        return None

    return _parse_simplified_address_format(field_address, dataset_graph)


def _parse_simplified_address_format(
    field_address: str, dataset_graph: DatasetGraph
) -> Optional[CollectionAddress]:
    """
    Parse the field address to extract collection name
    Field address format: "collection.field" or "collection.nested.field"
    """
    parts = field_address.split(".", 1)  # Split on first dot only
    if len(parts) != 2:
        return None

    collection_name = parts[0]
    field_path = parts[1]

    # Search for the specific collection
    for node_address, node in dataset_graph.nodes.items():
        # Check if this collection matches the collection name from the field address
        if node.collection.name == collection_name:
            # Check if the field exists in this collection
            # field_dict has FieldPath objects as keys, so we need to create a FieldPath for comparison
            if FieldPath.parse(field_path) in node.collection.field_dict:
                return node_address
    return None


def _parse_full_address_format(
    field_address: str, dataset_graph: DatasetGraph
) -> Optional[CollectionAddress]:
    """
    Parse the field address to extract collection name
    Field address format: "dataset:collection:field"
    """
    field_addr = FieldAddress.from_string(field_address)
    collection_address = field_addr.collection_address()

    # Verify the collection exists in the graph
    for node_address, node in dataset_graph.nodes.items():
        if node_address == collection_address:
            # Check if the field exists in this collection
            if field_addr.field_path in node.collection.field_dict:
                return node_address
    return None
