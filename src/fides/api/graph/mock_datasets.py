"""Generate synthetic GraphDataset objects for scale-testing the execution graph viewer.

Gated behind the FIDES__MOCK_GRAPH_DATASETS env var. Not used in production.
"""

import random
from typing import Optional

from loguru import logger

from fides.api.graph.config import (
    Collection,
    FieldAddress,
    GraphDataset,
    ScalarField,
)

MOCK_CONNECTION_KEY = "__mock_connector__"


def _make_collection(
    dataset_name: str,
    collection_name: str,
    *,
    identity: Optional[str] = None,
    upstream_dataset: Optional[str] = None,
    upstream_collection: Optional[str] = None,
    upstream_field: str = "id",
) -> Collection:
    """Build a single Collection with an id field, optional identity seed, and optional upstream reference."""
    fields: list[ScalarField] = [
        ScalarField(name="id", primary_key=True),
        ScalarField(name="name"),
        ScalarField(name="created_at"),
    ]

    if identity:
        fields.append(ScalarField(name="email", identity=identity))

    if upstream_dataset and upstream_collection:
        fields.append(
            ScalarField(
                name="ref_id",
                references=[
                    (
                        FieldAddress(
                            upstream_dataset, upstream_collection, upstream_field
                        ),
                        "from",
                    )
                ],
            )
        )

    return Collection(name=collection_name, fields=fields)


def generate_mock_datasets(
    num_datasets: int = 100,
    min_collections: int = 10,
    max_collections: int = 20,
) -> list[GraphDataset]:
    """Generate *num_datasets* interconnected GraphDataset objects.

    Topology
    --------
    * Tier 0 (1 dataset)  – seed dataset with an ``email`` identity field.
    * Tier 1 (~10 %)      – each references a random Tier-0 collection.
    * Tier 2 (~30 %)      – each references a random Tier-1 collection.
    * Tier 3 (remainder)  – each references a random Tier-2 collection.

    Within every dataset the collections form a chain so that
    ``col_0 ← col_1 ← … ← col_N``, giving each dataset internal depth.
    """
    if num_datasets < 1:
        return []

    tier_1_end = max(1, int(num_datasets * 0.10))
    tier_2_end = tier_1_end + max(1, int(num_datasets * 0.30))

    datasets: list[GraphDataset] = []
    tier_collections: dict[int, list[tuple[str, str]]] = {0: [], 1: [], 2: [], 3: []}

    for i in range(num_datasets):
        ds_name = f"mock_ds_{i:04d}"
        num_cols = random.randint(min_collections, max_collections)

        collections: list[Collection] = []
        for j in range(num_cols):
            col_name = f"col_{j:03d}"

            if j == 0:
                if i == 0:
                    col = _make_collection(ds_name, col_name, identity="email")
                else:
                    if i < tier_1_end:
                        tier = 0
                    elif i < tier_2_end:
                        tier = 1
                    else:
                        tier = 2

                    pool = tier_collections.get(tier, [])
                    if not pool:
                        pool = tier_collections[0]
                    up_ds, up_col = random.choice(pool)

                    col = _make_collection(
                        ds_name,
                        col_name,
                        upstream_dataset=up_ds,
                        upstream_collection=up_col,
                    )
            else:
                col = _make_collection(
                    ds_name,
                    col_name,
                    upstream_dataset=ds_name,
                    upstream_collection=f"col_{j - 1:03d}",
                )

            collections.append(col)

        dataset = GraphDataset(
            name=ds_name,
            collections=collections,
            connection_key=MOCK_CONNECTION_KEY,
        )
        datasets.append(dataset)

        current_tier: int
        if i == 0:
            current_tier = 0
        elif i < tier_1_end:
            current_tier = 1
        elif i < tier_2_end:
            current_tier = 2
        else:
            current_tier = 3

        for col in collections:
            tier_collections[current_tier].append((ds_name, col.name))

    total_collections = sum(len(ds.collections) for ds in datasets)
    logger.info(
        "Generated {} mock datasets with {} total collections",
        len(datasets),
        total_collections,
    )
    return datasets
