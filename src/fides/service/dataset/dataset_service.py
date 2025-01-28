from copy import deepcopy
from typing import Any, Dict, Optional, Set, Tuple

from sqlalchemy.orm import Session

from fides.api.common_exceptions import UnreachableNodesError, ValidationError
from fides.api.graph.config import GraphDataset
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import (
    PrivacyRequest,
    PrivacyRequestSource,
    PrivacyRequestStatus,
)
from fides.api.schemas.redis_cache import Identity, LabeledIdentity
from fides.api.task.create_request_tasks import run_access_request


def get_dataset_reachability(
    db: Session, dataset_config: DatasetConfig, policy: Optional[Policy] = None
) -> Tuple[bool, Optional[str]]:
    """
    Determines if the given dataset is reachable along with an error message
    """

    # Get all the dataset configs that are not associated with a disabled connection
    datasets = DatasetConfig.all(db=db)
    dataset_graphs = [
        dataset_config.get_graph()
        for dataset_config in datasets
        if not dataset_config.connection_config.disabled
    ]

    # We still want to check reachability even if our dataset config's connection is disabled.
    # We also consider the siblings, because if the connection is enabled, then all the
    # datasets will be enabled with it.
    sibling_dataset_graphs = []
    if dataset_config.connection_config.disabled:
        sibling_datasets = dataset_config.connection_config.datasets
        sibling_dataset_graphs = [
            dataset_config.get_graph() for dataset_config in sibling_datasets
        ]

    try:
        dataset_graph = DatasetGraph(*dataset_graphs, *sibling_dataset_graphs)
    except ValidationError as exc:
        return (
            False,
            f'The following dataset references do not exist "{", ".join(exc.errors)}"',
        )

    # dummy data is enough to determine traversability
    identity_seed: Dict[str, str] = {
        k: "something" for k in dataset_graph.identity_keys.values()
    }

    try:
        Traversal(dataset_graph, identity_seed, policy)
    except UnreachableNodesError as exc:
        return False, exc.message

    return True, None


def get_identities_and_references(
    dataset_config: DatasetConfig,
) -> Set[str]:
    """
    Returns all identity and dataset references in the dataset.
    If a field has multiple references only the first reference will be considered.
    """

    result: Set[str] = set()
    dataset: GraphDataset = dataset_config.get_graph()
    for collection in dataset.collections:
        # Process the identities in the collection
        result.update(collection.identities().values())
        for _, field_refs in collection.references().items():
            # Take first reference only, we only care that this collection is reachable,
            # how we get there doesn't matter for our current use case
            ref, edge_direction = field_refs[0]
            if edge_direction == "from" and ref.dataset != dataset_config.fides_key:
                result.add(ref.value)
    return result


def run_test_access_request(
    db: Session,
    policy: Policy,
    dataset_config: DatasetConfig,
    input_data: Dict[str, Any],
) -> PrivacyRequest:
    """
    Creates a privacy request with a source of "Dataset test" that runs an access request for a single dataset.
    The input data is used to mock any external dataset values referenced by our dataset so that it can run in
    complete isolation.
    """

    # Create a privacy request with a source of "Dataset test"
    # so it's not shown to the user.
    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "policy_id": policy.id,
            "source": PrivacyRequestSource.dataset_test,
            "status": PrivacyRequestStatus.in_processing,
        },
    )

    # Remove periods and colons to avoid them being parsed as path delimiters downstream.
    escaped_input_data = {
        key.replace(".", "_").replace(":", "_"): value
        for key, value in input_data.items()
    }

    # Manually cache the input data as identity data.
    # We're doing a bit of trickery here to avoid asking for labels for custom identities.
    predefined_fields = Identity.model_fields.keys()
    input_identity = {
        key: (
            value
            if key in predefined_fields
            else LabeledIdentity(label=key, value=value)
        )
        for key, value in escaped_input_data.items()
    }
    privacy_request.cache_identity(input_identity)

    graph_dataset = dataset_config.get_graph()
    modified_graph_dataset = replace_references_with_identities(
        dataset_config.fides_key, graph_dataset
    )

    dataset_graph = DatasetGraph(modified_graph_dataset)
    connection_config = dataset_config.connection_config

    # Finally invoke the existing DSR 3.0 access request task
    run_access_request(
        privacy_request,
        policy,
        dataset_graph,
        [connection_config],
        escaped_input_data,
        db,
        privacy_request_proceed=False,
    )
    return privacy_request


def replace_references_with_identities(
    dataset_key: str, graph_dataset: GraphDataset
) -> GraphDataset:
    """
    Replace external field references with identity values for testing.

    Creates a copy of the graph dataset and replaces dataset references with
    equivalent identity references that can be seeded directly. This allows
    testing a single dataset in isolation without needing to load data from
    referenced external datasets.
    """

    modified_graph_dataset = deepcopy(graph_dataset)

    for collection in modified_graph_dataset.collections:
        for field in collection.fields:
            for ref, edge_direction in field.references[:]:
                if edge_direction == "from" and ref.dataset != dataset_key:
                    field.identity = f"{ref.dataset}_{ref.collection}_{'_'.join(ref.field_path.levels)}"
                    field.references.remove((ref, "from"))

    return modified_graph_dataset
