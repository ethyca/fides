from typing import Dict, Any

import pytest
import yaml
from pydantic import ValidationError

from fidesops.graph.config import (
    CollectionAddress,
    ScalarField,
    ObjectField,
)
from fidesops.graph.data_type import DataType
from fidesops.models.datasetconfig import convert_dataset_to_graph
from fidesops.schemas.dataset import FidesopsDataset
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
            data_categories: [user.provided.identifiable.contact.city] 
          - name: id
            data_categories: [system.operations]
            fidesops_meta:
              primary_key: True  
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
            data_categories: [user.derived.identifiable.unique_id]
            fidesops_meta:
              references:
                - dataset: postgres_example_test_dataset
                  field: customer.id
                  direction: from
              data_type: integer
          - name: name
            data_categories: [user.provided.identifiable]
            fidesops_meta:
                data_type: string
          - name: submitter
            fidesops_meta:
                data_type: string 
            data_categories: [user.provided.identifiable]
          - name: thumbnail
            fields:
              - name: photo_id
                fidesops_meta:
                    data_type: integer
              - name: name
                data_categories: [user.provided.identifiable]
                fidesops_meta:
                    data_type: string
              - name: submitter
                fidesops_meta:
                    data_type: string
                data_categories: [user.provided.identifiable]
          - name: tags
            fidesops_meta:
                data_type: string[]
            data_categories: [user.provided]
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
                data_categories: [user.provided.identifiable]
                data_type: string
              - name: submitter
                data_type: string
                data_categories: [user.provided.identifiable]          
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
    ] = "invalid-dataset-name.invalid-collection-name"
    with pytest.raises(ValueError) as exc:
        d: FidesopsDataset = FidesopsDataset.parse_obj(dataset)
        convert_dataset_to_graph(d, "ignore")
    assert "FidesKey must only contain alphanumeric characters, '.' or '_'." in str(
        exc.value
    )


def test_nested_dataset_format():
    dataset = __to_dataset__(example_dataset_nested_yaml)
    ds = FidesopsDataset.parse_obj(dataset)
    graph = convert_dataset_to_graph(ds, "ignore")

    comments_field = field([graph], ("mongo_nested_test", "photos", "comments"))
    tags_field = field([graph], ("mongo_nested_test", "photos", "tags"))
    _id_field = field([graph], ("mongo_nested_test", "photos", "_id"))
    thumbnail_field = field([graph], ("mongo_nested_test", "photos", "thumbnail"))

    assert isinstance(comments_field, ObjectField)
    assert comments_field.is_array
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
