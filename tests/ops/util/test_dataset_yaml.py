from typing import Any, Dict

import pytest
import yaml
from fidesops.ops.graph.config import (
    CollectionAddress,
    FieldAddress,
    FieldPath,
    ObjectField,
    ScalarField,
)
from fidesops.ops.graph.graph import DatasetGraph, Edge
from fidesops.ops.models.datasetconfig import convert_dataset_to_graph
from fidesops.ops.schemas.dataset import FidesopsDataset
from pydantic import ValidationError

from ..graph.graph_test_util import field

example_dataset_yaml = """dataset:
  - fides_key: xyz
    fidesops_meta:
        after: [db1, db2, db3]        
    name: xyz
    description: x
    collections:
      - name: address
        fidesops_meta:
            after: [a.b, c.d, e.f]
        fields:
          - name: city
            data_categories: [user.contact.address.city] 
          - name: id
            data_categories: [system.operations]
            fidesops_meta:
              primary_key: True  
              data_type: integer
"""

example_dataset_nested_yaml = """dataset:
  - fides_key: mongo_nested_test
    name: Mongo Example Nested Test Dataset
    description: Example of a Mongo dataset that contains nested data
    collections:
      - name: photos
        fields:
          - name: _id
            data_categories: [system.operations]
            fidesops_meta:
              primary_key: True
              data_type: object_id
          - name: photo_id
            data_categories: [user.unique_id]
            fidesops_meta:
              references:
                - dataset: postgres_main_database
                  field: photo_collection.id
                  direction: from
              data_type: integer
          - name: name
            data_categories: [user]
            fidesops_meta:
                data_type: string
          - name: submitter
            fidesops_meta:
                data_type: string 
            data_categories: [user]
          - name: thumbnail
            fields:
              - name: photo_id
                fidesops_meta:
                    data_type: integer
              - name: name
                data_categories: [user]
                fidesops_meta:
                    data_type: string
              - name: submitter
                fidesops_meta:
                    data_type: string
                    references:
                        - dataset: postgres_main_database
                          field: users.id
                          direction: from
                data_categories: [user]
              - name: camera_used
                data_categories: [ system.operations ]
                fidesops_meta:
                  identity: 'camera_uuid'
                  data_type: integer
          - name: tags
            fidesops_meta:
                data_type: string[]
            data_categories: [user]
          - name: comments
            fidesops_meta:
                data_type: object[]
            fields:
              - name: comment_id
              - name: text
              - name: submitter
"""
example_bad_dataset_nested_yaml = """dataset:
  - fides_key: mongo_nested_test
    name: Mongo Example Nested Test Dataset
    description: Example of a Mongo dataset that contains nested data
    collections:
      - name: photos
        fields:
          - name: thumbnail
            fidesops_meta:
                data_type: string
            fields:
              - name: photo_id
                data_type: integer
              - name: name
                data_categories: [user]
                data_type: string
              - name: submitter
                data_type: string
                data_categories: [user]
"""


def __to_dataset__(yamlstr: str) -> Dict[str, Any]:
    return yaml.safe_load(yamlstr).get("dataset")[0]


def test_dataset_yaml_format():
    """Test that 'after' parameters are properly read"""
    dataset = __to_dataset__(example_dataset_yaml)
    d: FidesopsDataset = FidesopsDataset.parse_obj(dataset)
    config = convert_dataset_to_graph(d, "ignore")
    assert config.after == {"db1", "db2", "db3"}
    assert config.collections[0].after == {
        CollectionAddress("a", "b"),
        CollectionAddress("c", "d"),
        CollectionAddress("e", "f"),
    }


def test_dataset_yaml_format_invalid_format():
    """Test that 'after' parameters are properly read"""
    dataset = __to_dataset__(example_dataset_yaml)
    dataset.get("collections")[0].get("fidesops_meta").get("after")[0] = "invalid"
    with pytest.raises(ValueError) as exc:
        d: FidesopsDataset = FidesopsDataset.parse_obj(dataset)
        convert_dataset_to_graph(d, "ignore")
    assert "FidesCollection must be specified in the form 'FidesKey.FidesKey'" in str(
        exc.value
    )


def test_dataset_yaml_format_invalid_fides_keys():
    """Test that 'after' parameters are properly read"""
    dataset = __to_dataset__(example_dataset_yaml)
    dataset.get("collections")[0].get("fidesops_meta").get("after")[
        0
    ] = "invalid*dataset*name.invalid*collection*name"
    with pytest.raises(ValueError) as exc:
        d: FidesopsDataset = FidesopsDataset.parse_obj(dataset)
        convert_dataset_to_graph(d, "ignore")
    assert (
        "FidesKey must only contain alphanumeric characters, '.', '_' or '-'."
        in str(exc.value)
    )


def test_nested_dataset_format():
    dataset = __to_dataset__(example_dataset_nested_yaml)
    ds = FidesopsDataset.parse_obj(dataset)
    graph = convert_dataset_to_graph(ds, "ignore")

    comments_field = field([graph], "mongo_nested_test", "photos", "comments")
    tags_field = field([graph], "mongo_nested_test", "photos", "tags")
    _id_field = field([graph], "mongo_nested_test", "photos", "_id")
    thumbnail_field = field([graph], "mongo_nested_test", "photos", "thumbnail")

    assert isinstance(comments_field, ObjectField)
    assert comments_field.is_array
    assert comments_field.data_type() == "object"
    assert isinstance(comments_field.fields["text"], ScalarField)
    assert comments_field.fields["text"].data_type() == "None"
    assert isinstance(tags_field, ScalarField)
    assert tags_field.is_array
    assert isinstance(_id_field, ScalarField)
    assert _id_field.is_array is False

    assert isinstance(thumbnail_field, ObjectField)
    assert thumbnail_field.is_array is False
    assert thumbnail_field.data_type() == "object"
    assert thumbnail_field.fields["photo_id"].data_type() == "integer"
    assert thumbnail_field.fields["name"].data_type() == "string"


def test_nested_dataset_validation():
    with pytest.raises(ValidationError):
        FidesopsDataset.parse_obj(__to_dataset__(example_bad_dataset_nested_yaml))


def test_invalid_datatype():
    """Test that specifying a data type string that doesn't correspond to a supported
    data type string will throw a validation error."""
    bad_data_declaration = """dataset:
  - fides_key: dont_care
    collections:
      - name: dont_care
        fields:
          - name: dont_care
            fidesops_meta:
                data_type: this_is_bad"""
    dataset = __to_dataset__(bad_data_declaration)
    with pytest.raises(ValidationError):
        FidesopsDataset.parse_obj(dataset)


example_postgres_yaml = """dataset:
  - fides_key: postgres_main_database
    name: Postgres users and photos
    description: Example of a Postgres reference db
    collections:
      - name: photo_collection
        fields:
          - name: id
            data_categories: [system.operations]
            fidesops_meta:
              primary_key: True
              data_type: integer
      - name: users
        fields:
          - name: name
            data_categories: [ user.name]
            fidesops_meta:
              data_type: string
          - name: id
            data_categories: [system.operations]
            fidesops_meta:
              data_type: integer
      - name: cameras
        fields:
          - name: name
            data_categories: [ user]
            fidesops_meta:
              data_type: string
          - name: id
            data_categories: [system.operations]
            fidesops_meta:
              data_type: integer
              references:
                - dataset: mongo_nested_test
                  field: photos.thumbnail.camera_used
                  direction: from
"""


def test_dataset_graph_connected_by_nested_fields():
    """Two of the fields in the postgres dataset references a nested field in the mongo dataset"""
    dataset = __to_dataset__(example_dataset_nested_yaml)
    ds = FidesopsDataset.parse_obj(dataset)
    mongo_dataset = convert_dataset_to_graph(ds, "ignore")

    postgres_dataset = __to_dataset__(example_postgres_yaml)
    ds_postgres = FidesopsDataset.parse_obj(postgres_dataset)
    postgres_dataset = convert_dataset_to_graph(ds_postgres, "ignore")
    dataset_graph = DatasetGraph(mongo_dataset, postgres_dataset)

    assert dataset_graph.edges == {
        Edge(
            FieldAddress("postgres_main_database", "users", "id"),
            FieldAddress("mongo_nested_test", "photos", "thumbnail", "submitter"),
        ),
        Edge(
            FieldAddress("postgres_main_database", "photo_collection", "id"),
            FieldAddress("mongo_nested_test", "photos", "photo_id"),
        ),
        Edge(
            FieldAddress("mongo_nested_test", "photos", "thumbnail", "camera_used"),
            FieldAddress("postgres_main_database", "cameras", "id"),
        ),
    }

    assert dataset_graph.identity_keys == {
        FieldAddress(
            "mongo_nested_test", "photos", "thumbnail", "camera_used"
        ): "camera_uuid"
    }

    assert [
        field_path.string_path
        for field_path in dataset_graph.data_category_field_mapping[
            CollectionAddress("mongo_nested_test", "photos")
        ]["system.operations"]
    ] == ["_id", "thumbnail.camera_used"]


example_object_with_data_categories_nested_yaml = """dataset:
  - fides_key: mongo_nested_test 
    name: Mongo Example Nested Test Dataset
    description: Example of a Mongo dataset that has a data_category incorrectly declared at the object level
    collections:
      - name: photos
        fields:
          - name: thumbnail
            data_categories: [user]    
            fidesops_meta:
                data_type: object
            fields:
              - name: photo_id
                data_type: integer
              - name: name
                data_categories: [user]    
"""


def test_object_data_category_validation():
    """Test trying to validate object with data category specified"""
    with pytest.raises(ValidationError):
        FidesopsDataset.parse_obj(
            __to_dataset__(example_object_with_data_categories_nested_yaml)
        )


non_array_field_with_invalid_flag = """dataset:
  - fides_key: mongo_return_all_elements_test
    name: Mongo Return All Elements Test Dataset
    description: Example of a Mongo dataset that incorrectly has return_all_elements specified on a non array field.
    collections:
      - name: photos
        fields:
          - name: thumbnail
            fidesops_meta:
                return_all_elements: true
                data_type: object
            fields:
              - name: photo_id
                data_type: integer
              - name: name
                data_categories: [user]    
"""


def test_return_all_elements_specified_on_non_array_field():
    """Test return_all_elements can only be specified on array fields"""
    with pytest.raises(ValidationError):
        FidesopsDataset.parse_obj(__to_dataset__(non_array_field_with_invalid_flag))
