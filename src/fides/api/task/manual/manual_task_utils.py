from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.graph.config import (
    Collection,
    CollectionAddress,
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
    logger.info("Querying for connection configs with manual tasks")
    connection_configs = (
        db.query(ConnectionConfig)
        .join(ManualTask, ConnectionConfig.id == ManualTask.parent_entity_id)
        .filter(ManualTask.parent_entity_type == "connection_config")
        .filter(ConnectionConfig.disabled.is_(False))
        .all()
    )
    logger.info(
        f"Found {len(connection_configs)} connection configs with manual tasks: {[cc.key for cc in connection_configs]}"
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
    logger.debug(
        f"Found {len(connection_configs_with_manual_tasks)} connection configs with manual tasks"
    )

    # Create addresses for all connections that have manual tasks
    manual_task_addresses = []
    for config in connection_configs_with_manual_tasks:
        logger.info(f"Creating manual task address for connection config: {config.key}")
        manual_task_addresses.append(ManualTaskAddress.create(config.key))

    logger.info(
        f"Created {len(manual_task_addresses)} manual task addresses: {manual_task_addresses}"
    )
    return manual_task_addresses


def get_manual_task_for_connection_config(
    db: Session, connection_config_key: str
) -> ManualTask:
    """Get the ManualTask for a specific connection config,
    the manual task/connection config relationship is 1:1.
    """
    logger.info(
        f"Looking for manual task for connection config: {connection_config_key}"
    )

    manual_task = (
        db.query(ManualTask)
        .join(ConnectionConfig, ManualTask.parent_entity_id == ConnectionConfig.id)
        .filter(
            ConnectionConfig.key == connection_config_key,
            ManualTask.parent_entity_type == "connection_config",
        )
        .one_or_none()
    )

    if manual_task:
        logger.info(
            f"Found manual task {manual_task.id} for connection {connection_config_key}"
        )
    else:
        logger.warning(
            f"No manual task found for connection config: {connection_config_key}"
        )

    return manual_task


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
        # Extract the field name from the address (e.g., "user.age" -> "age")
        field_name = (
            field_address.split(".")[-1] if "." in field_address else field_address
        )

        scalar_field = ScalarField(
            name=field_name,
            data_categories=[],  # Conditional dependency fields don't have predefined data categories
            # Conditional dependency fields don't have complex relationships
        )
        fields.append(scalar_field)

    return fields


def create_collection_for_connection_key(
    db: Session, connection_key: str, dataset_graph: Optional["DatasetGraph"] = None
) -> Optional[Collection]:
    # Get the manual task for this connection config
    manual_task = get_manual_task_for_connection_config(db, connection_key)

    if not manual_task:
        # No manual tasks - create empty collection for backward compatibility
        return Collection(
            name=ManualTaskAddress.MANUAL_DATA_COLLECTION,
            fields=[],
            after=set(),
        )

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
    if fields:
        return Collection(
            name=ManualTaskAddress.MANUAL_DATA_COLLECTION,
            fields=fields,
            # Manual task has dependencies on regular tasks that provide conditional dependency fields
            after=dependency_collections,
        )
    return None


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

    logger.debug("Creating manual task artificial graphs")
    manual_task_graphs = []
    manual_addresses = get_manual_task_addresses(db)
    logger.debug(
        f"Found {len(manual_addresses)} manual task addresses: {manual_addresses}"
    )

    for address in manual_addresses:
        connection_key = address.dataset
        logger.debug(
            f"Processing manual task address: {address} for connection: {connection_key}"
        )

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
            logger.debug(
                f"Successfully created manual task graph for connection {connection_key}"
            )

    logger.info(f"Created {len(manual_task_graphs)} manual task graphs")
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
        db: Database session
        manual_task: The manual task to analyze
        dataset_graph: The actual graph being executed (optional for backward compatibility)

    Returns:
        Set of CollectionAddress objects for collections that provide conditional dependency fields
    """
    dependency_collections = set()
    conditional_dependencies = [
        dep
        for dep in manual_task.conditional_dependencies
        if dep.condition_type == ManualTaskConditionalDependencyType.leaf
    ]

    logger.info(
        f"🔍 Found {len(conditional_dependencies)} conditional dependencies for manual task {manual_task.id}"
    )

    for dependency in conditional_dependencies:
        logger.info(f"📋 Processing dependency: {dependency.field_address}")

        # Parse the field address to determine which collection provides this field
        # if the field address is None, skip it (Groups do not have field addresses)
        if dependency.field_address is None:
            continue

        collection_address = _get_collection_for_field_address(
            dependency.field_address, dataset_graph
        )
        if collection_address:
            logger.info(f"✅ Added dependency: {collection_address}")
            dependency_collections.add(collection_address)
        else:
            logger.warning(
                f"❌ No collection found for field address: {dependency.field_address}"
            )

    logger.info(f"📊 Final dependency collections: {dependency_collections}")
    return dependency_collections


def _get_collection_for_field_address(
    field_address: str,
    dataset_graph: Optional["DatasetGraph"] = None,
) -> Optional[CollectionAddress]:
    """
    Determine which collection provides a given field address.

    This function searches through the actual dataset graph to find collections
    that contain fields matching the field address pattern.

    Args:
        field_address: The field address to analyze (e.g., "user.profile.age")
        dataset_graph: The actual graph being executed (optional for backward compatibility)

    Returns:
        CollectionAddress for the collection that provides this field, or None if not found
    """
    logger.info(f"🔍 Looking for field address: {field_address}")
    logger.info(f"📊 Dataset graph provided: {dataset_graph is not None}")

    if not field_address or "." not in field_address:
        logger.warning(f"❌ Invalid field address: {field_address}")
        return None

    # If we have the actual graph, search through its collections
    if dataset_graph:
        logger.info(
            f"🔍 Searching through {len(dataset_graph.nodes)} collections in graph"
        )

        for node_address, node in dataset_graph.nodes.items():
            collection = node.collection
            logger.info(
                f"📋 Checking collection: {node_address} with {len(collection.field_dict)} fields"
            )

            # Check if any field in this collection matches the field address pattern
            for field_path, _ in collection.field_dict.items():
                # Convert field path to string for comparison
                field_string = field_path.string_path
                logger.debug(f"  🔍 Field: {field_string} vs target: {field_address}")

                # Check if the field address ends with this field path
                # e.g., "user.profile.age" should match field "profile.age" or "age"
                if (
                    field_address.endswith(field_string)
                    or field_string in field_address
                ):
                    logger.info(f"✅ Found match! {field_address} -> {node_address}")
                    return node_address

        logger.warning(f"❌ No match found for field address: {field_address}")
        return None

    logger.warning(
        f"❌ No dataset graph provided, cannot find collection for: {field_address}"
    )
    return None
