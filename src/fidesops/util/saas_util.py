from collections import defaultdict
from typing import Dict, List
from fidesops.graph.config import Collection, Dataset, Field


def merge_fields(target: Field, source: Field) -> Field:
    """Replaces source references and identities if they are available from the target"""
    if source.references is not None:
        target.references = source.references
    if source.identity is not None:
        target.identity = source.identity
    return target


def extract_fields(aggregate: Dict, collections: List[Collection]) -> None:
    """
    Takes all of the Fields in the given Collection and places them into an
    dictionary (dict[collection.name][field.name]) merging Fields when necessary
    """
    for collection in collections:
        field_dict = aggregate[collection.name]
        for field in collection.fields:
            if field_dict.get(field.name):
                field_dict[field.name] = merge_fields(field_dict[field.name], field)
            else:
                field_dict[field.name] = field


def merge_datasets(dataset: Dataset, config_dataset: Dataset) -> Dataset:
    """
    Merges all Collections and Fields from the config_dataset into the dataset.
    In the event of a collection/field name collision, the target field
    will inherit the identity and field references. This is by design since
    dataset references for SaaS connectors should not have any references.
    """
    field_aggregate: Dict[str, Dict] = defaultdict(dict)
    extract_fields(field_aggregate, dataset.collections)
    extract_fields(field_aggregate, config_dataset.collections)

    collections = []
    for collection_name, field_dict in field_aggregate.items():
        collections.append(
            Collection(name=collection_name, fields=list(field_dict.values()))
        )

    return Dataset(
        name=dataset.name,
        collections=collections,
        connection_key=dataset.connection_key,
    )
