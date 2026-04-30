from fideslang.models import Dataset

from fides.api.graph.graph import DatasetGraph
from fides.api.graph.preview.builder import TraversalPreviewBuilder
from fides.api.graph.preview.schemas import ManualTaskNode, Reachability
from fides.api.models.datasetconfig import convert_dataset_to_graph


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


def test_skipped_collection_excluded_from_traversed_count(connection_lookup):
    """A collection marked skip_processing must not contribute to ``traversed``."""
    ds = Dataset.parse_obj({
        "fides_key": "postgres_users",
        "name": "postgres_users",
        "collections": [
            {
                "name": "users",
                "fields": [
                    {"name": "email", "fides_meta": {"identity": "email"}, "data_categories": ["user.contact.email"]},
                ],
            },
            {
                "name": "audit_log",
                "fides_meta": {"skip_processing": True},
                "fields": [{"name": "id", "data_categories": ["system.operations"]}],
            },
        ],
    })
    graph = DatasetGraph(convert_dataset_to_graph(ds, "postgres-users-db"))

    preview = TraversalPreviewBuilder(
        graph=graph,
        identity_seed={"email": "preview@example.com"},
        action_type="access",
        connection_lookup={k: v for k, v in connection_lookup.items() if k == "postgres_users"},
        manual_tasks=[],
    ).build()

    pg = next(i for i in preview.integrations if i.connection_key == "postgres-users-db")
    # Only `users` was traversed; `audit_log` was excluded from the graph at construction.
    assert pg.collection_count.traversed == 1


def test_manual_task_emits_gates_edge(linear_two_dataset_graph, connection_lookup):
    """Manual tasks generate a ``gates`` edge to each integration they gate."""
    manual = ManualTaskNode(
        id="manual:verify-id",
        name="Verify ID",
        gates=["integration:postgres-users-db"],
    )
    preview = TraversalPreviewBuilder(
        graph=linear_two_dataset_graph,
        identity_seed={"email": "preview@example.com"},
        action_type="access",
        connection_lookup=connection_lookup,
        manual_tasks=[manual],
    ).build()

    gates = [e for e in preview.edges if e.kind == "gates"]
    assert len(gates) == 1
    assert gates[0].source == "manual:verify-id"
    assert gates[0].target == "integration:postgres-users-db"
    assert gates[0].dep_count is None
    assert preview.manual_tasks[0].id == "manual:verify-id"
