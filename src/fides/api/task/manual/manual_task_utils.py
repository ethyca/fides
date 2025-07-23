from typing import TYPE_CHECKING, Optional

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
from fides.api.models.manual_task.conditional_dependency import (
    ManualTaskConditionalDependency,
    ManualTaskConditionalDependencyType,
)
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType

# TYPE_CHECKING import placed after all runtime imports to avoid lint issues
if TYPE_CHECKING:  # pragma: no cover
    from fides.api.graph.traversal import TraversalNode  # noqa: F401
    from fides.api.models.policy import Policy  # noqa: F401


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
    def create_for_task(
        connection_config_key: str, manual_task_id: str
    ) -> CollectionAddress:
        """Create a CollectionAddress for a specific manual task: {connection_key}:manual_data_{task_id}"""
        return CollectionAddress(
            dataset=connection_config_key,
            collection=f"{ManualTaskAddress.MANUAL_DATA_COLLECTION}_{manual_task_id}",
        )

    @staticmethod
    def is_manual_task_address(address: CollectionAddress) -> bool:
        """Check if address represents manual task data"""
        if isinstance(address, str):
            # Handle string format "connection_key:collection_name"
            return address.endswith(
                f":{ManualTaskAddress.MANUAL_DATA_COLLECTION}"
            ) or address.startswith(f":{ManualTaskAddress.MANUAL_DATA_COLLECTION}_")

        # Handle CollectionAddress object
        return (
            address.collection == ManualTaskAddress.MANUAL_DATA_COLLECTION
            or address.collection.startswith(
                f"{ManualTaskAddress.MANUAL_DATA_COLLECTION}_"
            )
        )

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

    @staticmethod
    def get_manual_task_id(address: CollectionAddress) -> Optional[str]:
        """Extract manual task ID from manual task address if it's a specific task address"""
        if not ManualTaskAddress.is_manual_task_address(address):
            return None

        if isinstance(address, str):
            # Handle string format "connection_key:manual_data_task_id"
            parts = address.split(":")
            if len(parts) == 2:
                collection_part = parts[1]
                if collection_part.startswith(
                    f"{ManualTaskAddress.MANUAL_DATA_COLLECTION}_"
                ):
                    return collection_part[
                        len(f"{ManualTaskAddress.MANUAL_DATA_COLLECTION}_") :
                    ]
            return None

        # Handle CollectionAddress object
        if address.collection.startswith(
            f"{ManualTaskAddress.MANUAL_DATA_COLLECTION}_"
        ):
            return address.collection[
                len(f"{ManualTaskAddress.MANUAL_DATA_COLLECTION}_") :
            ]
        return None


def get_connection_configs_with_manual_tasks(db: Session) -> list[ConnectionConfig]:
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


def get_manual_task_addresses(db: Session) -> list[CollectionAddress]:
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
) -> list[ManualTask]:
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

    # Create fields based on ManualTaskConfigFields and conditional dependencies
    fields: list[Field] = []
    conditional_field_addresses: set[str] = set()

    for manual_task in manual_tasks:
        # Add fields from manual task configs
        current_configs = [
            config for config in manual_task.configs if config.is_current
        ]
        for config in current_configs:
            if config.config_type not in [
                ManualTaskConfigurationType.access_privacy_request,
                ManualTaskConfigurationType.erasure_privacy_request,
            ]:
                continue

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

        # Add fields from conditional dependencies
        conditional_field_addresses.update(
            _extract_field_addresses_from_conditional_dependencies(db, manual_task)
        )

    # Create scalar fields for conditional dependency field addresses
    for field_address in conditional_field_addresses:
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
) -> list[ManualTaskInstance]:
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
                    )
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
) -> list[ManualTaskInstance]:
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
) -> list:
    """
    Create artificial GraphDataset objects for manual tasks that can be included
    in the main dataset graph during the dataset configuration phase.

    Each manual task gets its own collection with its own dependencies based on
    its specific conditional dependencies. This allows individual manual tasks
    to receive only the data they need from regular tasks.

    Args:
        db: Database session
        policy: The policy being executed (optional, for filtering manual task configs)

    Returns:
        List of GraphDataset objects representing manual tasks as individual collections
    """

    manual_task_graphs = []
    manual_addresses = get_manual_task_addresses(db)

    for address in manual_addresses:
        connection_key = address.dataset

        # Get manual tasks for this connection
        manual_tasks = get_manual_tasks_for_connection_config(db, connection_key)

        # Create a separate collection for each manual task
        collections = []

        for manual_task in manual_tasks:
            # Create fields for this specific manual task
            fields: list = []
            conditional_field_addresses: set[str] = set()
            dependency_collections: set[CollectionAddress] = set()

            # Add fields from manual task configs
            current_configs = [
                config for config in manual_task.configs if config.is_current
            ]
            for config in current_configs:
                if config.config_type not in [
                    ManualTaskConfigurationType.access_privacy_request,
                    ManualTaskConfigurationType.erasure_privacy_request,
                ]:
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

            # Add fields from conditional dependencies for this specific task
            conditional_field_addresses.update(
                _extract_field_addresses_from_conditional_dependencies(db, manual_task)
            )

            # Find collections that provide the fields referenced in conditional dependencies for this task
            dependency_collections.update(
                _find_collections_for_conditional_dependencies(db, manual_task)
            )

            # Create scalar fields for conditional dependency field addresses
            for field_address in conditional_field_addresses:
                # Extract the field name from the address (e.g., "user.age" -> "age")
                field_name = (
                    field_address.split(".")[-1]
                    if "." in field_address
                    else field_address
                )

                scalar_field = ScalarField(
                    name=field_name,
                    data_categories=[],  # Conditional dependency fields don't have predefined data categories
                )
                fields.append(scalar_field)

            if fields:  # Only create collection if there are fields
                # Create a unique collection name for this manual task
                collection_name = (
                    f"{ManualTaskAddress.MANUAL_DATA_COLLECTION}_{manual_task.id}"
                )

                # Create a Collection for this specific manual task
                collection = Collection(
                    name=collection_name,
                    fields=fields,
                    # This manual task has dependencies on regular tasks that provide its conditional dependency fields
                    after=dependency_collections,
                )
                collections.append(collection)

        if collections:  # Only create graph if there are collections
            # Create a synthetic GraphDataset with all manual task collections
            graph_dataset = GraphDataset(
                name=connection_key,
                collections=collections,
                connection_key=connection_key,
                after=set(),
            )

            manual_task_graphs.append(graph_dataset)

    return manual_task_graphs


def _extract_field_addresses_from_conditional_dependencies(
    db: Session, manual_task: ManualTask
) -> set[str]:
    """
    Extract all field addresses from conditional dependencies for a manual task.

    Args:
        db: Database session
        manual_task: The manual task to extract field addresses from

    Returns:
        Set of field addresses from all conditional dependency leafs
    """
    field_addresses = set()

    # Get all conditional dependencies for this manual task
    conditional_dependencies = (
        db.query(ManualTaskConditionalDependency)
        .filter(ManualTaskConditionalDependency.manual_task_id == manual_task.id)
        .all()
    )

    for dependency in conditional_dependencies:
        if dependency.condition_type == ManualTaskConditionalDependencyType.leaf:
            # For leaf conditions, extract the field_address directly
            if dependency.field_address:
                field_addresses.add(dependency.field_address)
        elif dependency.condition_type == ManualTaskConditionalDependencyType.group:
            # For group conditions, recursively check all children
            _extract_field_addresses_from_group(dependency, field_addresses)

    return field_addresses


def _extract_field_addresses_from_group(
    group_dependency: ManualTaskConditionalDependency, field_addresses: set[str]
) -> None:
    """
    Recursively extract field addresses from a group conditional dependency.

    Args:
        group_dependency: The group conditional dependency to process
        field_addresses: Set to accumulate field addresses
    """
    for child in group_dependency.children:  # type: ignore[attr-defined]
        if child.condition_type == ManualTaskConditionalDependencyType.leaf:
            # For leaf conditions, extract the field_address directly
            if child.field_address:
                field_addresses.add(child.field_address)
        elif child.condition_type == ManualTaskConditionalDependencyType.group:
            # For group conditions, recursively check all children
            _extract_field_addresses_from_group(child, field_addresses)


def _find_collections_for_conditional_dependencies(
    db: Session, manual_task: ManualTask
) -> set[CollectionAddress]:
    """
    Find collections that provide fields referenced in conditional dependencies.

    This function analyzes the conditional dependencies of a manual task and
    identifies which regular task collections need to be executed before the
    manual task to provide the required field data.

    Args:
        db: Database session
        manual_task: The manual task to analyze

    Returns:
        Set of CollectionAddress objects for collections that provide conditional dependency fields
    """
    dependency_collections = set()

    # Get all conditional dependencies for this manual task
    conditional_dependencies = (
        db.query(ManualTaskConditionalDependency)
        .filter(ManualTaskConditionalDependency.manual_task_id == manual_task.id)
        .all()
    )

    for dependency in conditional_dependencies:
        if dependency.condition_type == ManualTaskConditionalDependencyType.leaf:
            if dependency.field_address:
                # Parse the field address to determine which collection provides this field
                collection_address = _get_collection_for_field_address(
                    dependency.field_address
                )
                if collection_address:
                    dependency_collections.add(collection_address)
        elif dependency.condition_type == ManualTaskConditionalDependencyType.group:
            # For group conditions, recursively check all children
            _find_collections_from_group_recursive(dependency, dependency_collections)

    return dependency_collections


def _find_collections_from_group_recursive(
    group_dependency: ManualTaskConditionalDependency,
    dependency_collections: set[CollectionAddress],
) -> None:
    """
    Recursively find collections from group conditional dependencies.

    Args:
        group_dependency: The group conditional dependency to process
        dependency_collections: Set to accumulate collection addresses
    """
    for child in group_dependency.children:  # type: ignore[attr-defined]
        if child.condition_type == ManualTaskConditionalDependencyType.leaf:
            if child.field_address:
                collection_address = _get_collection_for_field_address(
                    child.field_address
                )
                if collection_address:
                    dependency_collections.add(collection_address)
        elif child.condition_type == ManualTaskConditionalDependencyType.group:
            # For group conditions, recursively check all children
            _find_collections_from_group_recursive(child, dependency_collections)


def _get_collection_for_field_address(
    field_address: str,
) -> Optional[CollectionAddress]:
    """
    Determine which collection provides a given field address.

    This function parses field addresses like "user.profile.age" and determines
    which collection would provide this field. The logic here assumes a standard
    naming convention where the first part of the field address indicates the
    collection name.

    Args:
        field_address: The field address to analyze (e.g., "user.profile.age")

    Returns:
        CollectionAddress for the collection that provides this field, or None if not found
    """
    if not field_address or "." not in field_address:
        return None

    # Parse the field address to extract collection information
    # For field addresses like "user.profile.age", we assume "user" is the collection
    # This is a simplified approach - in a real implementation, you might need
    # more sophisticated logic to map field addresses to collections
    parts = field_address.split(".")
    if len(parts) < 2:
        return None

    collection_name = parts[0]

    # For now, we'll use a simple mapping approach
    # In a real implementation, you might query the database to find which collections
    # actually contain fields that match this pattern
    collection_mapping = {
        "user": CollectionAddress("postgres_example", "customer"),
        "billing": CollectionAddress("postgres_example", "payment_card"),
        # Add more mappings as needed based on your actual data model
    }

    return collection_mapping.get(collection_name)
