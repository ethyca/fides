from typing import Any, Dict, Set

from sqlalchemy.orm import Session

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
    db: Session,
    dataset_config: DatasetConfig,
):
    """
    Determines if the given dataset is reachable.
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
    except Exception:
        # TODO: add more detail
        return False

    identity_seed: Dict[str, str] = {
        k: "something" for k in dataset_graph.identity_keys.values()
    }

    try:
        Traversal(dataset_graph, identity_seed)
    except Exception:
        # TODO: check if our datasets are in the exception
        return False

    return True


def get_identities_and_references(
    dataset_config: DatasetConfig,
) -> Set[str]:
    """
    Returns all identity and dataset references in the dataset.
    """
    result = set()
    dataset: GraphDataset = dataset_config.get_graph()
    for collection in dataset.collections:
        # Process the identities in the collection
        result.update(collection.identities().values())
        for _, field_refs in collection.references().items():
            # Take first reference only
            ref, edge_direction = field_refs[0]
            if edge_direction == "from" and ref.dataset != dataset_config.fides_key:
                result.add(
                    f"{ref.dataset}.{ref.collection}.{ref.field_path.string_path}"
                )
    return result


def run_test_access_request(
    db: Session,
    policy: Policy,
    dataset_config: DatasetConfig,
    input_data: Dict[str, Any],
) -> PrivacyRequest:
    """
    Creates a privacy request with a source of "Dataset test" that runs an access request for a single dataset.
    The input data is used to mock any external dataset values referenced by our dataset so that it can run
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

    # Remove periods to avoid them being parsed as path delimiters downstream.
    escaped_input_data = {
        key.replace(".", "_"): value for key, value in input_data.items()
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

    # We're providing external reference values directly, so we can replace
    # field references with identities and provide the values as seed data
    # at the start of the traversal. This way we don't need to run collections
    # from any other datasets, only from the dataset we're testing.
    graph_dataset = dataset_config.get_graph()
    for collection in graph_dataset.collections:
        for field in collection.fields:
            for ref, edge_direction in field.references[:]:
                if edge_direction == "from" and ref.dataset != dataset_config.fides_key:
                    field.identity = f"{ref.dataset}_{ref.collection}_{'_'.join(ref.field_path.levels)}"
                    field.references.remove((ref, "from"))

    dataset_graph = DatasetGraph(graph_dataset)
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
