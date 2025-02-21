from loguru import logger

from fides.api.common_exceptions import TraversalError, ValidationError
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
        if not context.connection_config:
            logger.warning(
                "Skipping traversal validation, no connection config provided"
            )
            return

        try:
            graph = convert_dataset_to_graph(
                context.dataset, context.connection_config.key
            )

            if context.connection_config.connection_type == ConnectionType.saas:
                graph = merge_datasets(
                    graph,
                    context.connection_config.get_saas_config().get_graph(
                        context.connection_config.secrets
                    ),
                )

            complete_graph = DatasetGraph(graph)
            unique_identities = set(complete_graph.identity_keys.values())
            Traversal(complete_graph, {k: None for k in unique_identities})

            context.traversal_details = DatasetTraversalDetails(
                is_traversable=True, msg=None
            )

        except (TraversalError, ValidationError) as err:
            context.traversal_details = DatasetTraversalDetails(
                is_traversable=False, msg=str(err)
            )
