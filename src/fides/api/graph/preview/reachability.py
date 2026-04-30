from __future__ import annotations

from typing import Dict, Set

from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.preview.schemas import Reachability


def classify_per_integration(
    graph: DatasetGraph,
    captured_addresses: Set[CollectionAddress],
    connection_lookup: Dict[str, Dict],
) -> Dict[str, Reachability]:
    """Label every integration in ``connection_lookup`` as reachable, unreachable,
    or requires_manual_identity.

    - reachable: the integration's dataset appears in ``captured_addresses``
      (i.e. Traversal walked through it from the seed).
    - requires_manual_identity: the dataset has an identity field but didn't
      participate in the traversal (likely because the seed didn't include the
      matching identity type).
    - unreachable: the dataset has no identity field and no traversal coverage.
    """
    captured_datasets = {a.dataset for a in captured_addresses}
    datasets_with_identity = _datasets_with_identity_fields(graph)

    classification: Dict[str, Reachability] = {}
    for dataset_key, conn in connection_lookup.items():
        integration_key = conn["connection_key"]
        if dataset_key in captured_datasets:
            classification[integration_key] = Reachability.REACHABLE
        elif dataset_key in datasets_with_identity:
            classification.setdefault(integration_key, Reachability.REQUIRES_MANUAL_IDENTITY)
        else:
            classification.setdefault(integration_key, Reachability.UNREACHABLE)
    return classification


def _datasets_with_identity_fields(graph: DatasetGraph) -> Set[str]:
    out: Set[str] = set()
    for address, node in graph.nodes.items():
        for field in node.collection.fields:
            if getattr(field, "identity", None):
                out.add(address.dataset)
                break
    return out
