import yaml
from fideslang.models import Dataset

from fides.api.graph.graph import *

#  -------------------------------------------
#   graph object tests
#  -------------------------------------------
from fides.api.graph.traversal import Traversal
from fides.api.models.datasetconfig import convert_dataset_to_graph

from . import sql_data_generator

f = """dataset:
  - fides_key: db
    name: name
    description: description
    collections:
      - name: user
        fields:
          - name: id
              data_type: integer
              references:
                - dataset: db
                  field: address.user_id
          - name: email
            fides_meta:
              identity: email
          - name: name

      - name: address
        fields:
          - name: id
              data_type: integer
          - name: user_id
          - name: street
          - name: city
          - name: state
          - name: zip
"""


def parse_yaml() -> GraphDataset:
    """Test that 'after' parameters are properly read"""
    d = yaml.safe_load(f)
    dataset = d.get("dataset")[0]
    d: Dataset = Dataset.model_validate(dataset)
    return convert_dataset_to_graph(d, "ignore")


def test_generate():
    dataset = parse_yaml()
    traversal = Traversal(DatasetGraph(dataset), {"email": "example@example.com"})
    for k, v in sql_data_generator.generate_data_for_traversal(traversal, 10).items():
        for k2, v2 in v.items():
            print(f"{k}--{k2}=={v2}")
