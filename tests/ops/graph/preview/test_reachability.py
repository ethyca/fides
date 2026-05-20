from fideslang.models import Dataset

from fides.api.graph.graph import DatasetGraph
from fides.api.graph.preview.builder import TraversalPreviewBuilder
from fides.api.graph.preview.schemas import Reachability
from fides.api.models.datasetconfig import convert_dataset_to_graph


def test_unreachable_integration_marked(linear_two_graph_datasets, connection_lookup):
    """An integration whose only dataset has no identity path is marked unreachable."""
    isolated_dataset = Dataset.parse_obj(
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


def test_requires_manual_identity_classification(
    linear_two_graph_datasets, connection_lookup
):
    """A dataset with identity fields that wasn't traversed gets REQUIRES_MANUAL_IDENTITY."""
    # Create a dataset with a phone identity (not in the seed)
    phone_dataset = Dataset.parse_obj(
        {
            "fides_key": "phone_db",
            "name": "phone_db",
            "collections": [
                {
                    "name": "contacts",
                    "fields": [
                        {
                            "name": "phone",
                            "fides_meta": {"identity": "phone_number"},
                            "data_categories": ["user.contact.phone_number"],
                        },
                    ],
                }
            ],
        }
    )
    phone_graph_dataset = convert_dataset_to_graph(phone_dataset, "phone-conn")
    combined_graph = DatasetGraph(*linear_two_graph_datasets, phone_graph_dataset)

    lookup = dict(connection_lookup)
    lookup["phone_db"] = {
        "connection_key": "phone-conn",
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
    assert by_key["phone-conn"].reachability == Reachability.REQUIRES_MANUAL_IDENTITY


def test_multi_dataset_connection_reachable_wins(
    linear_two_graph_datasets, connection_lookup
):
    """When a connection has 2 datasets, one reachable and one not, REACHABLE wins."""
    # Add a second dataset mapped to the same connection_key as postgres-users-db
    extra_ds = Dataset.parse_obj(
        {
            "fides_key": "postgres_audit",
            "name": "postgres_audit",
            "collections": [
                {
                    "name": "audit_entries",
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
    extra_graph_dataset = convert_dataset_to_graph(extra_ds, "postgres-users-db")
    combined_graph = DatasetGraph(*linear_two_graph_datasets, extra_graph_dataset)

    lookup = dict(connection_lookup)
    # Map the extra dataset to the same connection as postgres_users
    lookup["postgres_audit"] = {
        "connection_key": "postgres-users-db",
        "connector_type": "postgres",
        "system": {
            "fides_key": "users-system",
            "name": "Users",
            "data_use": "user.functional",
        },
    }

    preview = TraversalPreviewBuilder(
        graph=combined_graph,
        identity_seed={"email": "preview@example.com"},
        action_type="access",
        connection_lookup=lookup,
        manual_tasks=[],
    ).build()

    by_key = {i.connection_key: i for i in preview.integrations}
    # postgres-users-db should be REACHABLE even though postgres_audit is not
    assert by_key["postgres-users-db"].reachability == Reachability.REACHABLE
