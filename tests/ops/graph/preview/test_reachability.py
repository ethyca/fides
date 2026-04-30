from fideslang.models import Dataset

from fides.api.graph.graph import DatasetGraph
from fides.api.graph.preview.builder import TraversalPreviewBuilder
from fides.api.graph.preview.schemas import Reachability
from fides.api.models.datasetconfig import convert_dataset_to_graph


def test_unreachable_integration_marked(linear_two_graph_datasets, connection_lookup):
    """An integration whose only dataset has no identity path is marked unreachable."""
    isolated_dataset = Dataset.parse_obj({
        "fides_key": "isolated_db",
        "name": "isolated_db",
        "collections": [{
            "name": "logs",
            "fields": [{"name": "id", "data_categories": ["system.operations"]}],
        }],
    })
    isolated_graph_dataset = convert_dataset_to_graph(isolated_dataset, "isolated")

    combined_graph = DatasetGraph(*linear_two_graph_datasets, isolated_graph_dataset)

    lookup = dict(connection_lookup)
    lookup["isolated_db"] = {
        "connection_key": "isolated",
        "connector_type": "postgres",
        "system": None,
    }

    preview = TraversalPreviewBuilder(
        graph=combined_graph,
        identity_seed={"email": "preview@example.com"},
        action_type="access",
        connection_lookup=lookup,
        manual_tasks=[],
    ).build()

    by_key = {i.connection_key: i for i in preview.integrations}
    assert by_key["isolated"].reachability == Reachability.UNREACHABLE
