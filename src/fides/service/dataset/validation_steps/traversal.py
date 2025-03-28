from uuid import uuid4

from fides.api.common_exceptions import (
    TraversalError,
    UnreachableNodesError,
    ValidationError,
)
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.connectionconfig import ConnectionType
from fides.api.models.datasetconfig import convert_dataset_to_graph
from fides.api.schemas.dataset import DatasetTraversalDetails
from fides.api.util.saas_util import merge_datasets
from fides.service.dataset.dataset_validator import (
    DatasetValidationContext,
    DatasetValidationStep,
)


class TraversalValidationStep(DatasetValidationStep):
    """Validates dataset traversability"""

    def validate(self, context: DatasetValidationContext) -> None:
        try:
            # Create graph for the current dataset
            current_graph_dataset = convert_dataset_to_graph(
                context.dataset,
                (
                    context.connection_config.key
                    if context.connection_config
                    else str(uuid4())
                ),
            )

            # Handle SaaS connections for the current dataset
            connection_type = (
                context.connection_config.connection_type
                if context.connection_config
                else None
            )

            if connection_type == ConnectionType.saas:
                current_graph_dataset = merge_datasets(
                    current_graph_dataset,
                    context.connection_config.get_saas_config().get_graph(
                        context.connection_config.secrets
                    ),
                )

            # Combine the current dataset graph with the active dataset graphs
            # Use list() to make a copy of dataset_graphs before appending
            all_graph_datasets = list(context.graph_datasets)
            all_graph_datasets.append(current_graph_dataset)

            # Create the complete graph
            complete_graph = DatasetGraph(*all_graph_datasets)

            unique_identities = set(complete_graph.identity_keys.values())

            from fides.service.dataset.dataset_config_service import DatasetFilter

            Traversal(
                complete_graph,
                {k: None for k in unique_identities},
                node_filters=[DatasetFilter(context.dataset.fides_key)],
            )

            context.traversal_details = DatasetTraversalDetails(
                is_traversable=True, msg=None
            )

        except (TraversalError, ValidationError, UnreachableNodesError) as err:
            context.traversal_details = DatasetTraversalDetails(
                is_traversable=False, msg=str(err)
            )
