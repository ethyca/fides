from typing import Any, Optional

from sqlalchemy.orm import Session, selectinload

from fides.api.graph.config import (
    Collection,
    CollectionAddress,
    FieldAddress,
    GraphDataset,
    ScalarField,
)
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.manual_task import ManualTask, ManualTaskConfigurationType
from fides.api.task.manual.manual_task_address import ManualTaskAddress

PRIVACY_REQUEST_CONFIG_TYPES = {
    ManualTaskConfigurationType.access_privacy_request,
    ManualTaskConfigurationType.erasure_privacy_request,
}


def extract_dataset_field_addresses(
    tree: Optional[dict[str, Any]],
) -> set[str]:
    """Recursively extract dataset field addresses from a JSONB condition tree.

    This function is used to extract all field addresses from a condition tree
    stored as JSONB. It's useful for determining upstream dependencies when
    building the dataset graph for conditional dependencies.

    Args:
        tree: The condition tree dict (or None)

    Returns:
        Set of field addresses found in the tree, excluding privacy_request.* fields
    """
    if not tree:
        return set()

    field_addresses: set[str] = set()

    # Check if this is a leaf condition (has field_address)
    if "field_address" in tree:
        field_address = tree["field_address"]
        if field_address and not field_address.startswith("privacy_request."):
            field_addresses.add(field_address)
    # Check if this is a group condition (has conditions list)
    elif "conditions" in tree:
        for condition in tree.get("conditions", []):
            field_addresses.update(extract_dataset_field_addresses(condition))

    return field_addresses


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
        .options(
            selectinload(ManualTask.configs).selectinload(
                "field_definitions"
            ),  # type: ignore[attr-defined]
            selectinload(ManualTask.conditional_dependencies),
        )
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
    fields: list[ScalarField] = []
    for field_address in field_addresses:
        # Use the full field address as the field name to preserve collection context
        # This allows the manual task to receive data from specific collections
        # e.g., "user.name" or "customer.profile.email" instead of just "name" or "email"
        field_address_obj = FieldAddress.from_string(field_address)

        scalar_field = ScalarField(
            name=field_address_obj.value,
            # Conditional dependency fields don't have predefined data categories
            data_categories=[],
            references=[(field_address_obj, "from")],
        )
        fields.append(scalar_field)

    return fields


def _create_collection_from_manual_task(
    manual_task: ManualTask,
) -> Optional[Collection]:
    """Create a Collection from a ManualTask. Helper function to avoid duplication."""
    # Get conditional dependency field addresses from JSONB condition_tree
    conditional_field_addresses: set[str] = set()
    for dependency in manual_task.conditional_dependencies:
        # condition_tree is always a dict (ConditionLeaf or ConditionGroup), never a list
        tree = dependency.condition_tree
        if isinstance(tree, dict) or tree is None:
            conditional_field_addresses.update(extract_dataset_field_addresses(tree))

    # Create scalar fields for data category fields and conditional dependency field addresses
    fields: list[ScalarField] = []
    fields.extend(create_data_category_scalar_fields(manual_task))
    fields.extend(
        create_conditional_dependency_scalar_fields(conditional_field_addresses)
    )

    # Only create collection if there are fields
    if not fields:
        return None

    return Collection(name=ManualTaskAddress.MANUAL_DATA_COLLECTION, fields=fields)


def create_collection_for_connection_key(
    db: Session, connection_key: str
) -> Optional[Collection]:
    # Get the manual task for this connection config
    manual_task = get_manual_task_for_connection_config(db, connection_key)

    if not manual_task:
        return None

    return _create_collection_from_manual_task(manual_task)


def create_manual_task_artificial_graphs(db: Session) -> list[GraphDataset]:
    """
    Create artificial GraphDataset objects for manual tasks that can be included
    in the main dataset graph during the dataset configuration phase.

    Each manual task gets its own collection with its own dependencies based on
    its specific conditional dependencies. This allows individual manual tasks
    to receive only the data they need from regular tasks.

    Args:
        db: Database session

    Returns:
        List of GraphDataset objects representing manual tasks as individual collections
    """
    manual_task_graphs: list[GraphDataset] = []
    manual_addresses = get_manual_task_addresses(db)

    if not manual_addresses:
        return manual_task_graphs

    # Batch load all manual tasks with their relationships to avoid N+1 queries
    connection_keys = [address.dataset for address in manual_addresses]
    manual_tasks = (
        db.query(ManualTask, ConnectionConfig.key)
        .join(ConnectionConfig, ManualTask.parent_entity_id == ConnectionConfig.id)
        .options(
            selectinload(ManualTask.configs).selectinload(
                "field_definitions"
            ),  # type: ignore[attr-defined]
            selectinload(ManualTask.conditional_dependencies),
        )
        .filter(
            ConnectionConfig.key.in_(connection_keys),
            ManualTask.parent_entity_type == "connection_config",
        )
        .all()
    )

    # Create a lookup map by connection key
    manual_task_map = {connection_key: task for task, connection_key in manual_tasks}

    for address in manual_addresses:
        connection_key = address.dataset
        manual_task = manual_task_map.get(connection_key)

        if not manual_task:
            continue

        # Create collection using the helper function to avoid duplication
        collection = _create_collection_from_manual_task(manual_task)
        if not collection:
            continue

        # Create a synthetic GraphDataset with all manual task collections
        graph_dataset = GraphDataset(
            name=connection_key,
            collections=[collection],
            connection_key=connection_key,
        )

        manual_task_graphs.append(graph_dataset)

    return manual_task_graphs
