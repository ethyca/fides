from typing import Optional

from sqlalchemy.orm import Session

from fides.api.graph.config import (
    Collection,
    CollectionAddress,
    FieldAddress,
    GraphDataset,
    ScalarField,
)

# Import application models
from fides.api.models.conditional_dependency.conditional_dependency_base import (
    ConditionalDependencyType,
)
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.manual_task import ManualTask, ManualTaskConfigurationType
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


def create_collection_for_connection_key(
    db: Session, connection_key: str
) -> Optional[Collection]:
    # Get the manual task for this connection config
    manual_task = get_manual_task_for_connection_config(db, connection_key)

    if not manual_task:
        return None

    # Get conditional dependency field addresses - raw field data
    conditional_field_addresses: set[str] = {
        dependency.field_address
        for dependency in manual_task.conditional_dependencies
        if dependency.condition_type == ConditionalDependencyType.leaf
        and dependency.field_address is not None
    }

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
    manual_task_graphs = []
    manual_addresses = get_manual_task_addresses(db)

    for address in manual_addresses:
        connection_key = address.dataset

        # Get the collection for this connection config using the reusable function
        collection = create_collection_for_connection_key(db, connection_key)

        if collection:  # Only create graph if there are collections
            # Create a synthetic GraphDataset with all manual task collections
            graph_dataset = GraphDataset(
                name=connection_key,
                collections=[collection],
                connection_key=connection_key,
            )

            manual_task_graphs.append(graph_dataset)

    return manual_task_graphs
