import pytest
import yaml

from fidesops.graph.config import CollectionAddress
from fidesops.models.datasetconfig import convert_dataset_to_graph
from fidesops.schemas.dataset import FidesopsDataset

f = """dataset:
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


def test_dataset_yaml_format():
    """Test that 'after' parameters are properly read"""
    d = yaml.safe_load(f)
    dataset = d.get("dataset")[0]
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
    d = yaml.safe_load(f)
    dataset = d.get("dataset")[0]
    dataset.get("collections")[0].get("fidesops_meta").get("after")[0] = "invalid"
    with pytest.raises(ValueError) as exc:
        d: FidesopsDataset = FidesopsDataset.parse_obj(dataset)
        convert_dataset_to_graph(d, "ignore")
    assert "FidesCollection must be specified in the form 'FidesKey.FidesKey'" in str(exc.value)

def test_dataset_yaml_format_invalid_fides_keys():
    """Test that 'after' parameters are properly read"""
    d = yaml.safe_load(f)
    dataset = d.get("dataset")[0]
    dataset.get("collections")[0].get("fidesops_meta").get("after")[0] = "invalid-dataset-name.invalid-collection-name"
    with pytest.raises(ValueError) as exc:
        d: FidesopsDataset = FidesopsDataset.parse_obj(dataset)
        convert_dataset_to_graph(d, "ignore")
    assert "FidesKey must only contain alphanumeric characters, '.' or '_'." in str(exc.value)
