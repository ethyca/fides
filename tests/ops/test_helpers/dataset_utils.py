import re
from typing import Any, Dict, Iterable, List, Optional

import yaml
from fideslang.models import Dataset

from fides.api.graph.config import (
    Collection,
    Field,
    FieldPath,
    ObjectField,
    ScalarField,
)
from fides.api.graph.data_type import DataType, get_data_type, to_data_type_string
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import (
    DatasetConfig,
    DatasetField,
    convert_dataset_to_graph,
)
from fides.api.util.collection_util import Row

SAAS_DATASET_DIRECTORY = "data/saas/dataset/"


def update_dataset(
    connection_config: ConnectionConfig,
    dataset_config: DatasetConfig,
    api_data: Dict[str, List[Row]],
    file_name: str,
):
    """
    Helper function to update the dataset in the given dataset_config
    with api_data and write the formatted result to the specified file.
    """

    generated_dataset = generate_dataset(
        Dataset.model_validate(dataset_config.ctl_dataset).model_dump(mode="json"),
        api_data,
        [endpoint["name"] for endpoint in connection_config.saas_config["endpoints"]],
    )

    # the yaml library doesn't allow us to just reformat
    # the data_categories field so we fix it with a regex
    #
    # data_categories:
    #   - system.operations
    #
    # data_categories: [system.operations]
    #
    with open(f"{SAAS_DATASET_DIRECTORY}{file_name}", "w") as dataset_file:
        dataset_file.write(
            re.sub(
                r"(data_categories:)\n\s+- ([^\n]+)",
                r"\1 [\2]",
                yaml.dump(
                    {"dataset": [generated_dataset]},
                    default_flow_style=False,
                    sort_keys=False,
                    indent=2,
                ),
            )
        )


def generate_dataset(
    existing_dataset: Dict[str, Any],
    api_data: Dict[str, List[Row]],
    collection_order: List[str] = None,
):
    """
    Generates a dataset which is an aggregate of the existing dataset and
    any new fields generated from the API data. Orders the collections
    based on the order of collection_order.
    """

    # preserve the collection order in the dataset if a collection order is not provided
    if not collection_order:
        collection_order = [
            collection["name"] for collection in existing_dataset["collections"]
        ]

    # remove the dataset name from the keys in the api_data map before passing
    # into generate_collections
    generated_collections = generate_collections(
        {
            collection_name.replace(f"{existing_dataset['fides_key']}:", ""): collection
            for collection_name, collection in api_data.items()
        },
        existing_dataset,
    )

    return {
        "fides_key": existing_dataset["fides_key"],
        "name": existing_dataset["name"],
        "description": existing_dataset["description"],
        "collections": [
            {
                "name": collection["name"],
                "fields": collection["fields"],
            }
            for collection in sorted(
                generated_collections,
                key=lambda collection: collection_order.index(collection["name"]),
            )
        ],
    }


def generate_collections(
    api_data: Dict[str, List[Row]], dataset: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Generates a list of collections based on the response data or returns
    the existing collections if no API data is available.
    """

    # convert FidesLang Dataset to graph Dataset to be able to use the Collection helpers
    collection_map = {}
    if dataset:
        graph = convert_dataset_to_graph(Dataset(**dataset), dataset["fides_key"])
        collection_map = {
            collection.name: collection for collection in graph.collections
        }

    collections = []
    for collection_name in set().union(
        api_data.keys(),
        collection_map.keys(),
    ):
        if len(rows := api_data.get(collection_name, [])):
            fields = generate_fields(rows[0], collection_name, collection_map)
        else:
            fields = get_simple_fields(collection_map.get(collection_name).fields)

        collections.append(
            {
                "name": collection_name,
                "fields": fields,
            }
        )

    return collections


def generate_fields(
    row: Dict[str, Any], parent_path: str, field_map: Dict[str, Collection]
) -> List[Dict[str, Dict]]:
    """
    Generates a simplified version of dataset fields based on the row data.
    Maintains the current path of the traversal to determine if the field
    exists in the existing dataset. If it does, existing attributes
    are preserved instead of generating them from the row data.
    """

    fields = []
    for key, value in row.items():
        # increment path
        current_path = f"{parent_path}.{key}"
        # initialize field
        field = {"name": key}
        # derive data_type based on row data
        data_type, is_array = get_data_type(value)

        # only values of type object or object[] should have sub-fields defined
        # additionally object and object[] cannot have data_categories
        if data_type == DataType.object.name and not is_array:
            field["fidesops_meta"] = {"data_type": data_type}
            field["fields"] = generate_fields(value, current_path, field_map)
        elif data_type == DataType.object.name and is_array:
            field["fidesops_meta"] = {"data_type": to_data_type_string(data_type, True)}
            field["fields"] = generate_fields(value[0], current_path, field_map)
        else:
            if existing_field := get_existing_field(field_map, current_path):
                if isinstance(existing_field, ScalarField):
                    # field exists, copy existing data categories and data_type (if available)
                    field["data_categories"] = existing_field.data_categories or [
                        "system.operations"
                    ]
                    data_type = (
                        existing_field.data_type()
                        if existing_field.data_type() != "None"
                        else data_type
                    )
                    if data_type:
                        field["fidesops_meta"] = {"data_type": data_type}
                elif isinstance(existing_field, ObjectField):
                    # the existing field has a more complex type than what we could derive
                    # from the API response, we need to copy the fields too instead of just
                    # the data_categories and data_type
                    field["fidesops_meta"] = {
                        "data_type": to_data_type_string(
                            DataType.object.name, isinstance(value, list)
                        )
                    }
                    field["fields"] = get_simple_fields(existing_field.fields.values())
            else:
                # we don't have this field in our dataset, use the default category
                # and the derived data_type
                field["data_categories"] = ["system.operations"]
                # we don't assume the data_type for empty strings, empty lists,
                # empty dicts, or nulls
                if data_type != DataType.no_op.name:
                    field["fidesops_meta"] = {
                        "data_type": to_data_type_string(data_type, is_array)
                    }
        fields.append(field)
    return fields


def get_existing_field(field_map: Dict[str, Collection], path: str) -> Optional[Field]:
    """
    Lookup existing field by collection name and field path.
    """
    collection_name, field_path = path.split(".", 1)
    if collection := field_map.get(collection_name):
        return collection.field_dict.get(FieldPath.parse((field_path)))
    return None


def get_simple_fields(fields: Iterable[Field]) -> List[Dict[str, Any]]:
    """
    Converts dataset fields into simple dictionaries with only
    name, data_category, and data_type.
    """

    object_list = []
    for field in fields:
        object = {"name": field.name}
        if field.data_categories:
            object["data_categories"] = field.data_categories
        if field.data_type() != "None":
            object["fidesops_meta"] = {"data_type": field.data_type()}
        if isinstance(field, ObjectField) and field.fields:
            object["fields"] = get_simple_fields(field.fields.values())
        object_list.append(object)
    return object_list


def remove_primary_keys(dataset: Dataset) -> Dataset:
    """Returns a copy of the dataset with primary key fields removed from fides_meta."""
    dataset_copy = dataset.model_copy(deep=True)

    for collection in dataset_copy.collections:
        for field in collection.fields:
            if field.fides_meta:
                if field.fides_meta.primary_key:
                    field.fides_meta.primary_key = None
                if field.fields:
                    _remove_nested_primary_keys(field.fields)

    return dataset_copy


def _remove_nested_primary_keys(fields: List[DatasetField]) -> None:
    """Helper function to recursively remove primary keys from nested fields."""
    for field in fields:
        if field.fides_meta and field.fides_meta.primary_key:
            field.fides_meta.primary_key = None
        if field.fields:
            _remove_nested_primary_keys(field.fields)
