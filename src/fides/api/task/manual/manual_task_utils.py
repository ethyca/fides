from loguru import logger
from sqlalchemy.orm import Session

from fides.api.graph.config import (
    Collection,
    CollectionAddress,
    Field,
    GraphDataset,
    ScalarField,
)
from fides.api.graph.graph import Node
from fides.api.graph.traversal import TraversalNode
from fides.api.models.connectionconfig import ConnectionConfig

# Import application models
from fides.api.models.manual_task import ManualTask, ManualTaskConfigurationType
from fides.api.task.manual.manual_task_address import ManualTaskAddress


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


def create_manual_data_traversal_node(
    db: Session, address: CollectionAddress
) -> "TraversalNode":
    """
    Create a TraversalNode for a manual_data collection
    """
    connection_key = address.dataset

    # Get manual tasks for this connection to determine fields
    manual_task = get_manual_task_for_connection_config(db, connection_key)

    # Create fields based on ManualTaskConfigFields
    fields: list[Field] = []
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

    node = Node(dataset, collection)
    traversal_node = TraversalNode(node)

    return traversal_node


def create_manual_task_artificial_graphs(
    db: Session,
) -> list:
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
        policy: The policy being executed (optional, for filtering manual task configs)

    Returns:
        List of GraphDataset objects representing manual tasks as root nodes
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

        # Get manual tasks for this connection to determine fields
        manual_task = get_manual_task_for_connection_config(db, connection_key)

        # Create fields based only on ManualTaskConfigFields
        fields: list = []

        # Manual task collections act as root nodes - they don't need identity dependencies
        # since they provide manually-entered data rather than consuming identity data.
        if manual_task:
            logger.debug(
                f"Processing manual task {manual_task.id} with {len(manual_task.configs)} configs"
            )
            current_configs = [
                config
                for config in manual_task.configs
                if config.is_current
                and config.config_type
                in [
                    ManualTaskConfigurationType.access_privacy_request,
                    ManualTaskConfigurationType.erasure_privacy_request,
                ]
            ]
            logger.debug(
                f"Found {len(current_configs)} current configs for manual task {manual_task.id}"
            )

            for config in current_configs:
                logger.debug(
                    f"Processing config {config.id} with {len(config.field_definitions)} fields"
                )
                for field in config.field_definitions:
                    # Create a scalar field for each manual task field
                    field_metadata = field.field_metadata or {}
                    data_categories = field_metadata.get("data_categories", [])

                    scalar_field = ScalarField(
                        name=field.field_key,
                        data_categories=data_categories,
                    )
                    fields.append(scalar_field)
        else:
            logger.warning(
                f"No manual task found for connection {connection_key}, skipping"
            )

        if fields:  # Only create graph if there are fields
            logger.debug(
                f"Creating graph for connection {connection_key} with {len(fields)} fields"
            )
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
            logger.debug(
                f"Successfully created manual task graph for connection {connection_key}"
            )
        else:
            logger.warning(
                f"No fields found for connection {connection_key}, skipping graph creation"
            )

    logger.debug(f"Created {len(manual_task_graphs)} manual task graphs")
    return manual_task_graphs
