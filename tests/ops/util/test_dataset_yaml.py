from typing import Any, Dict

import pytest
import yaml
from fideslang.models import Dataset
from pydantic import ValidationError

from fides.api import common_exceptions
from fides.api.graph.config import (
    CollectionAddress,
    FieldAddress,
    ObjectField,
    ScalarField,
)
from fides.api.graph.graph import DatasetGraph, Edge
from fides.api.models.datasetconfig import convert_dataset_to_graph

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
    d: Dataset = Dataset.model_validate(dataset)
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
        d: Dataset = Dataset.model_validate(dataset)
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
        d: Dataset = Dataset.model_validate(dataset)
        convert_dataset_to_graph(d, "ignore")
    assert (
        "FidesKeys must only contain alphanumeric characters, '.', '_', '<', '>' or '-'."
        in str(exc.value)
    )


def test_nested_dataset_format():
    dataset = __to_dataset__(example_dataset_nested_yaml)
    ds = Dataset.model_validate(dataset)
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
        Dataset.model_validate(__to_dataset__(example_bad_dataset_nested_yaml))


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
        Dataset.model_validate(dataset)


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
    ds = Dataset.model_validate(dataset)
    mongo_dataset = convert_dataset_to_graph(ds, "ignore")

    postgres_dataset = __to_dataset__(example_postgres_yaml)
    ds_postgres = Dataset.model_validate(postgres_dataset)
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
        Dataset.model_validate(__to_dataset__(non_array_field_with_invalid_flag))


skip_processing_yaml = """dataset:
  - fides_key: a_dataset
    name: a_dataset
    description: a description
    collections:
      - name: a_collection
        fides_meta:
            skip_processing: True
        fields:
          - name: a_field
            data_categories: [user.contact.address.city]
          - name: id
            data_categories: [system.operations]
      - name: b_collection
        fields:
          - name: b_field
            data_categories: [user.contact.address.city]
          - name: id
            data_categories: [system.operations]
"""

skip_processing_invalid_yaml = """dataset:
  - fides_key: a_dataset
    name: A Dataset
    description: a description
    collections:
      - name: a_collection
        fides_meta:
            skip_processing: True
        fields:
          - name: a_field
            data_categories: [user.contact.address.city]
          - name: id
            data_categories: [system.operations]
      - name: b_collection
        fields:
          - name: b_field
            data_categories: [user.contact.address.city]
          - name: id
            data_categories: [system.operations]
            fides_meta:
              references:
                - dataset: a_dataset
                  field: a_collection.id
                  direction: from
"""


class TestConvertDatasetToGraphSkipProcessing:
    def test_collection_skip_processing(self):
        """A skip_processing flag at collection > fides_meta causes the collection
        to be ignored in convert_dataset_to_graph"""
        dataset = __to_dataset__(skip_processing_yaml)
        ds = Dataset.model_validate(dataset)
        converted_dataset = convert_dataset_to_graph(ds, "ignore")
        assert len(converted_dataset.collections) == 1
        assert converted_dataset.collections[0].name == "b_collection"
        assert converted_dataset.collections[0].skip_processing is False

        assert DatasetGraph(converted_dataset)

    def test_invalid_collection_skip_processing(self):
        """Skipping a collection that shouldn't be skipped is not picked up in convert_dataset_to_graph, but
        downstream when DatasetGraph is instantiated"""
        dataset = __to_dataset__(skip_processing_invalid_yaml)
        ds = Dataset.model_validate(dataset)
        converted_dataset = convert_dataset_to_graph(ds, "ignore")
        assert len(converted_dataset.collections) == 1
        assert converted_dataset.collections[0].name == "b_collection"
        assert converted_dataset.collections[0].skip_processing is False

        with pytest.raises(common_exceptions.ValidationError) as exc:
            DatasetGraph(converted_dataset)

        assert (
            exc.value.message
            == "Referred to object a_dataset:a_collection:id does not exist"
        )
