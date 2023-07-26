"""
Build Privacy Request graphs.
"""
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.privacy_requests.graph.config import TERMINATOR_ADDRESS, CollectionAddress
from fides.privacy_requests.graph.graph import DatasetGraph, GraphDataset
from fides.privacy_requests.graph.traversal import TraversalNode
from fides.privacy_requests.graph_tasks.graph_task import GraphTask
from fides.privacy_requests.graph_tasks.task_resources import TaskResources


def build_consent_dataset_graph(datasets: List[DatasetConfig]) -> DatasetGraph:
    """
    Build the starting DatasetGraph for consent requests.

    Consent Graph has one node per dataset.  Nodes must be of saas type and have consent requests defined.
    """
    consent_datasets: List[GraphDataset] = []

    for dataset_config in datasets:
        connection_type: ConnectionType = (
            dataset_config.connection_config.connection_type  # type: ignore
        )
        saas_config: Optional[Dict] = dataset_config.connection_config.saas_config
        if (
            connection_type == ConnectionType.saas
            and saas_config
            and saas_config.get("consent_requests")
        ):
            consent_datasets.append(
                dataset_config.get_dataset_with_stubbed_collection()
            )

    return DatasetGraph(*consent_datasets)


async def build_consent_graph(  # pylint: disable = too-many-arguments
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
) -> Tuple[Dict[CollectionAddress, Any], List[CollectionAddress]]:
    """Build a consent graph.

    A consent graph is relatively simple: there are no relationships between the nodes, every node has
    identity data input and every node outputs whether the consent request succeeded.

    The DatasetGraph passed in is expected to have one Node per Dataset. That Node is expected to carry out requests
    for the Dataset as a whole.
    """

    with TaskResources(
        privacy_request, policy, connection_configs, session
    ) as resources:
        graph_keys: List[CollectionAddress] = list(graph.nodes.keys())
        dsk: Dict[CollectionAddress, Any] = {}

        for col_address, node in graph.nodes.items():
            traversal_node = TraversalNode(node)
            task = GraphTask(traversal_node, resources)
            dsk[col_address] = (task.consent_request, identity)

        def termination_fn(*dependent_values: bool) -> Tuple[bool, ...]:
            """The dependent_values here is an bool output from each task feeding in, where
            each task reports the output of 'task.consent_request(identity_data)', which is whether the
            consent request succeeded

            The termination function just returns this tuple of booleans."""
            return dependent_values

        # terminator function waits for all keys
        dsk[TERMINATOR_ADDRESS] = (termination_fn, *graph_keys)

        return (dsk, graph_keys)
