import yaml
from fidesops.ops.graph.graph import *

#  -------------------------------------------
#   graph object tests
#  -------------------------------------------
from fidesops.ops.graph.traversal import Traversal
from fidesops.ops.models.datasetconfig import convert_dataset_to_graph
from fidesops.ops.schemas.dataset import FidesopsDataset

from . import sql_data_generator

f = """dataset:
  - fides_key: db
    name: name
    description: description
    collections:
      - name: user
        fields:
          - name: id
            fidesops_meta:
              primary_key: True
              data_type: integer
              references:
                - dataset: db
                  field: address.user_id
          - name: email
            fidesops_meta:
              identity: email
          - name: name

      - name: address
        fields:
          - name: id
            fidesops_meta:
              primary_key: True
              data_type: integer
          - name: user_id
          - name: street
          - name: city
          - name: state
          - name: zip
"""


def parse_yaml() -> Dataset:
    """Test that 'after' parameters are properly read"""
    d = yaml.safe_load(f)
    dataset = d.get("dataset")[0]
    d: FidesopsDataset = FidesopsDataset.parse_obj(dataset)
    return convert_dataset_to_graph(d, "ignore")


def test_generate():
    dataset = parse_yaml()
    traversal = Traversal(DatasetGraph(dataset), {"email": "example@example.com"})
    for k, v in sql_data_generator.generate_data_for_traversal(traversal, 10).items():
        for k2, v2 in v.items():
            print(f"{k}--{k2}=={v2}")
