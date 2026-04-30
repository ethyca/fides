from fides.api.graph.preview.builder import TraversalPreviewBuilder
from fides.api.graph.preview.schemas import Reachability


def test_builder_returns_preview_for_linear_graph(linear_two_dataset_graph, connection_lookup):
    builder = TraversalPreviewBuilder(
        graph=linear_two_dataset_graph,
        identity_seed={"email": "preview@example.com"},
        action_type="access",
        connection_lookup=connection_lookup,
        manual_tasks=[],
    )
    preview = builder.build()

    assert preview.action_type == "access"
    assert preview.identity_root.identity_types == ["email"]
    assert len(preview.integrations) == 2

    by_key = {i.connection_key: i for i in preview.integrations}
    assert by_key["postgres-users-db"].reachability == Reachability.REACHABLE
    assert by_key["stripe"].reachability == Reachability.REACHABLE

    edge_kinds = {(e.source, e.target, e.kind) for e in preview.edges}
    assert ("identity-root", "integration:postgres-users-db", "depends_on") in edge_kinds
    assert ("integration:postgres-users-db", "integration:stripe", "depends_on") in edge_kinds
