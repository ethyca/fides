"""
Execute a Privacy Request Graph.
"""
from typing import Any, Dict, List, Tuple

import dask
from dask import delayed  # type: ignore[attr-defined]
from dask.threaded import get

from fides.api.privacy_requests.graph.config import (
    TERMINATOR_ADDRESS,
    CollectionAddress,
)
from fides.api.util.collection_util import Row

dask.config.set(scheduler="threads")


async def execute_graph(
    request_graph: Dict[CollectionAddress, Any]
) -> Dict[str, List[Row]]:
    """Execute Dask-style DAGs."""
    dask_execution_graph = delayed(
        get(request_graph, TERMINATOR_ADDRESS, num_workers=1)
    )
    return dask_execution_graph.compute()


async def execute_consent_graph(
    request_graph: Dict[CollectionAddress, Any], graph_keys: List[CollectionAddress]
) -> Dict[str, bool]:
    dask_execution_graph = delayed(
        get(request_graph, TERMINATOR_ADDRESS, num_workers=1)
    )

    update_successes: Tuple[bool, ...] = dask_execution_graph.compute()
    # we combine the output of the termination function with the input keys to provide
    # a map of {collection_name: whether consent request succeeded}:
    consent_update_map: Dict[str, bool] = dict(
        zip([coll.value for coll in graph_keys], update_successes)
    )

    return consent_update_map
