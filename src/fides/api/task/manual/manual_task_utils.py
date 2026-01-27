from typing import Any, Optional

from sqlalchemy.orm import Session, selectinload

from fides.api.graph.config import (
    Collection,
    CollectionAddress,
    FieldAddress,
    GraphDataset,
    ScalarField,
)

# Import application models
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.manual_task import ManualTask
from fides.api.schemas.policy import ActionType
from fides.api.task.conditional_dependencies.privacy_request.schemas import (
    PrivacyRequestTopLevelFields,
)
from fides.api.task.manual.manual_task_address import ManualTaskAddress

PRIVACY_REQUEST_CONFIG_TYPES = {
    ActionType.access,
    ActionType.erasure,
    ActionType.consent,
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


def get_manual_task_addresses(
    db: Session, config_types: Optional[list[ActionType]] = None
) -> list[CollectionAddress]:
    """
    Get manual task addresses for all connection configs that have manual tasks.

    Note: Manual tasks should be included in the graph if they exist for any connection config
    that's part of the dataset graph, regardless of specific policy targets. This allows
    manual tasks to collect additional data that may be needed for the privacy request.

    Args:
        db: Database session
        config_types: Optional list of ActionType values to filter manual tasks by.
            Only tasks with current configs matching these types will be included.
            If None, all manual tasks are included.
    """
    from fides.api.models.manual_task import ManualTaskConfig

    # Build base query joining connection configs with manual tasks
    query = (
        db.query(ConnectionConfig)
        .join(ManualTask, ConnectionConfig.id == ManualTask.parent_entity_id)
        .filter(ManualTask.parent_entity_type == "connection_config")
        .filter(ConnectionConfig.disabled.is_(False))
    )

    # If config_types specified, filter to only include tasks with matching current configs
    if config_types is not None:
        query = query.join(
            ManualTaskConfig, ManualTask.id == ManualTaskConfig.task_id
        ).filter(
            ManualTaskConfig.is_current.is_(True),
            ManualTaskConfig.config_type.in_(config_types),
        )

    connection_configs = query.distinct().all()

    return [ManualTaskAddress.create(config.key) for config in connection_configs]


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
            selectinload(ManualTask.configs).selectinload("field_definitions"),  # type: ignore[attr-defined]
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
    config_types: Optional[list[ActionType]] = None,
) -> Optional[Collection]:
    """Create a Collection from a ManualTask. Helper function to avoid duplication.

    Args:
        manual_task: The manual task to create a collection from
        config_types: Optional list of config types to filter dependencies by.
            For consent tasks, dataset field references are excluded since
            consent DSRs don't have data flow through datasets.
    """
    # Determine if we should exclude dataset field references
    # Consent tasks don't have data flow, so they shouldn't reference dataset fields
    is_consent_only = (
        config_types is not None
        and len(config_types) == 1
        and ActionType.consent in config_types
    )

    # Get conditional dependency field addresses from JSONB condition_tree
    conditional_field_addresses: set[str] = set()
    for dependency in manual_task.conditional_dependencies:
        tree = dependency.condition_tree
        if isinstance(tree, dict) or tree is None:
            field_addresses = set(
                addr
                for addr in extract_field_addresses(tree)
                if not addr.startswith(
                    PrivacyRequestTopLevelFields.privacy_request.value
                )
            )

            # For consent-only tasks, skip dataset field references entirely
            # since consent DSRs don't have data flow through datasets
            if is_consent_only:
                continue

            conditional_field_addresses.update(field_addresses)

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


def create_manual_task_artificial_graphs(
    db: Session, config_types: Optional[list[ActionType]] = None
) -> list[GraphDataset]:
    """
    Create artificial GraphDataset objects for manual tasks that can be included
    in the main dataset graph during the dataset configuration phase.

    Each manual task gets its own collection with its own dependencies based on
    its specific conditional dependencies. This allows individual manual tasks
    to receive only the data they need from regular tasks.

    Args:
        db: Database session
        config_types: Optional list of ActionType values to filter manual tasks by.
            Only tasks with configs matching these types will be included.
            If None, all manual tasks are included.

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
            selectinload(ManualTask.configs).selectinload("field_definitions"),  # type: ignore[attr-defined]
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

        # Filter by config_types if specified
        if config_types is not None:
            # Check if any config matches the requested types
            has_matching_config = any(
                config.config_type in config_types for config in manual_task.configs
            )
            if not has_matching_config:
                continue

        # Create collection using the helper function to avoid duplication
        # Pass config_types to filter dependencies appropriately (e.g., consent tasks
        # should not include dataset field references since they don't have data flow)
        collection = _create_collection_from_manual_task(manual_task, config_types)
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


def extract_field_addresses(
    tree: Optional[dict[str, Any]],
) -> set[str]:
    """Recursively extract dataset field addresses from a JSONB condition tree.

    This function is used to extract all field addresses from a condition tree
    stored as JSONB. It's useful for determining upstream dependencies when
    building the dataset graph for conditional dependencies.

    Returns:
        Set of field addresses found in the tree, excluding privacy_request.* fields
    """
    if not tree:
        return set()

    field_addresses: set[str] = set()

    # Check if this is a leaf condition (has field_address)
    if "field_address" in tree:
        field_addresses.add(tree["field_address"])
    # Check if this is a group condition (has conditions list)
    elif "conditions" in tree:
        for condition in tree.get("conditions", []):
            field_addresses.update(extract_field_addresses(condition))

    return field_addresses
