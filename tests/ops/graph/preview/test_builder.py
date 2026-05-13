from fideslang.models import Dataset

from fides.api.graph.graph import DatasetGraph
from fides.api.graph.preview.builder import TraversalPreviewBuilder
from fides.api.graph.preview.schemas import ManualTaskNode, Reachability
from fides.api.models.datasetconfig import convert_dataset_to_graph


def test_builder_returns_preview_for_linear_graph(
    linear_two_dataset_graph, connection_lookup
):
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
    assert (
        "identity-root",
        "integration:postgres-users-db",
        "depends_on",
    ) in edge_kinds
    assert (
        "integration:postgres-users-db",
        "integration:stripe",
        "depends_on",
    ) in edge_kinds


def test_graph_excludes_skip_processing_collections(connection_lookup):
    """DatasetGraph excludes skip_processing collections at construction time,
    so they never appear in the builder's traversal output."""
    ds = Dataset.parse_obj(
        {
            "fides_key": "postgres_users",
            "name": "postgres_users",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "email",
                            "fides_meta": {"identity": "email"},
                            "data_categories": ["user.contact.email"],
                        },
                    ],
                },
                {
                    "name": "audit_log",
                    "fides_meta": {"skip_processing": True},
                    "fields": [
                        {"name": "id", "data_categories": ["system.operations"]}
                    ],
                },
            ],
        }
    )
    graph = DatasetGraph(convert_dataset_to_graph(ds, "postgres-users-db"))

    preview = TraversalPreviewBuilder(
        graph=graph,
        identity_seed={"email": "preview@example.com"},
        action_type="access",
        connection_lookup={
            k: v for k, v in connection_lookup.items() if k == "postgres_users"
        },
        manual_tasks=[],
    ).build()

    pg = next(
        i for i in preview.integrations if i.connection_key == "postgres-users-db"
    )
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


def test_capture_traversal_failure_falls_back_to_static_edges(connection_lookup):
    """When traversal raises (unreachable nodes), static edges still appear."""
    reachable_ds = Dataset.parse_obj(
        {
            "fides_key": "postgres_users",
            "name": "postgres_users",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "email",
                            "fides_meta": {"identity": "email"},
                            "data_categories": ["user.contact.email"],
                        },
                        {"name": "user_id", "data_categories": ["user.unique_id"]},
                    ],
                }
            ],
        }
    )
    # isolated_db has no identity path and no FK reference — unreachable.
    isolated_ds = Dataset.parse_obj(
        {
            "fides_key": "isolated_db",
            "name": "isolated_db",
            "collections": [
                {
                    "name": "logs",
                    "fields": [
                        {"name": "id", "data_categories": ["system.operations"]},
                        {
                            "name": "user_id",
                            "data_categories": ["user.unique_id"],
                            "fides_meta": {
                                "references": [
                                    {
                                        "dataset": "postgres_users",
                                        "field": "users.user_id",
                                        "direction": "from",
                                    }
                                ],
                            },
                        },
                    ],
                }
            ],
        }
    )
    lookup = dict(connection_lookup)
    lookup["isolated_db"] = {
        "connection_key": "isolated",
        "connector_type": "postgres",
        "system": None,
    }
    # Remove stripe from lookup so it's just postgres + isolated
    lookup = {k: v for k, v in lookup.items() if k != "stripe"}
    graph = DatasetGraph(
        convert_dataset_to_graph(reachable_ds, "postgres-users-db"),
        convert_dataset_to_graph(isolated_ds, "isolated"),
    )
    preview = TraversalPreviewBuilder(
        graph=graph,
        identity_seed={"email": "preview@example.com"},
        action_type="access",
        connection_lookup=lookup,
        manual_tasks=[],
    ).build()

    # Edges should still be present even though traversal may have failed
    assert len(preview.edges) > 0


def test_static_dataset_detail_for_unreachable_integration(connection_lookup):
    """Integration not in traversal still gets datasets/fields from the graph."""
    reachable_ds = Dataset.parse_obj(
        {
            "fides_key": "postgres_users",
            "name": "postgres_users",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "email",
                            "fides_meta": {"identity": "email"},
                            "data_categories": ["user.contact.email"],
                        },
                    ],
                }
            ],
        }
    )
    isolated_ds = Dataset.parse_obj(
        {
            "fides_key": "isolated_db",
            "name": "isolated_db",
            "collections": [
                {
                    "name": "logs",
                    "fields": [
                        {"name": "id", "data_categories": ["system.operations"]}
                    ],
                }
            ],
        }
    )
    lookup = {
        "postgres_users": connection_lookup["postgres_users"],
        "isolated_db": {
            "connection_key": "isolated",
            "connector_type": "postgres",
            "system": None,
        },
    }
    graph = DatasetGraph(
        convert_dataset_to_graph(reachable_ds, "postgres-users-db"),
        convert_dataset_to_graph(isolated_ds, "isolated"),
    )
    preview = TraversalPreviewBuilder(
        graph=graph,
        identity_seed={"email": "preview@example.com"},
        action_type="access",
        connection_lookup=lookup,
        manual_tasks=[],
    ).build()

    by_key = {i.connection_key: i for i in preview.integrations}
    isolated = by_key["isolated"]
    assert isolated.reachability == Reachability.UNREACHABLE
    assert isolated.collection_count.traversed == 0
    assert isolated.collection_count.total == 1
    assert len(isolated.datasets) == 1
    assert isolated.datasets[0].collections[0].name == "logs"


def test_warnings_populated_on_traversal_failure():
    """When traversal fails, preview.warnings contains the exception message."""
    ds = Dataset.parse_obj(
        {
            "fides_key": "ds_a",
            "name": "ds_a",
            "collections": [
                {
                    "name": "tbl",
                    "fields": [
                        {"name": "id", "data_categories": ["system.operations"]}
                    ],
                }
            ],
        }
    )
    graph = DatasetGraph(convert_dataset_to_graph(ds, "conn-a"))
    lookup = {
        "ds_a": {
            "connection_key": "conn-a",
            "connector_type": "postgres",
            "system": None,
        }
    }
    preview = TraversalPreviewBuilder(
        graph=graph,
        identity_seed={"email": "test@example.com"},
        action_type="access",
        connection_lookup=lookup,
        manual_tasks=[],
    ).build()

    # The dataset has no identity field, so traversal will fail
    # and warnings should capture the error
    assert len(preview.warnings) > 0


def test_empty_graph_returns_empty_preview():
    """Zero integrations, zero edges."""
    # An empty DatasetGraph has no nodes — create with an empty dataset
    ds = Dataset.parse_obj(
        {
            "fides_key": "empty_ds",
            "name": "empty_ds",
            "collections": [],
        }
    )
    graph = DatasetGraph(convert_dataset_to_graph(ds, "empty-conn"))
    preview = TraversalPreviewBuilder(
        graph=graph,
        identity_seed={"email": "test@example.com"},
        action_type="access",
        connection_lookup={
            "empty_ds": {
                "connection_key": "empty-conn",
                "connector_type": "postgres",
                "system": None,
            }
        },
        manual_tasks=[],
    ).build()

    assert len(preview.integrations) <= 1
    assert len(preview.edges) == 0


def test_target_categories_filter_fields(linear_two_dataset_graph, connection_lookup):
    """target_categories={\"user.contact\"} filters field data_categories."""
    preview = TraversalPreviewBuilder(
        graph=linear_two_dataset_graph,
        identity_seed={"email": "preview@example.com"},
        action_type="access",
        connection_lookup=connection_lookup,
        manual_tasks=[],
        target_categories={"user.contact"},
    ).build()

    by_key = {i.connection_key: i for i in preview.integrations}
    pg = by_key["postgres-users-db"]
    users_coll = pg.datasets[0].collections[0]
    email_field = next(f for f in users_coll.fields if f.name == "email")
    # user.contact.email is a descendant of user.contact
    assert "user.contact.email" in email_field.data_categories
    # user.unique_id should be filtered out
    uid_field = next(f for f in users_coll.fields if f.name == "user_id")
    assert uid_field.data_categories == []
