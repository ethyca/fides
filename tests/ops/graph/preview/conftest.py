import pytest
from fideslang.models import Dataset

from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.models.datasetconfig import convert_dataset_to_graph
from fides.api.util.data_category import DataCategory


@pytest.fixture
def linear_two_dataset_graph() -> DatasetGraph:
    """A → B: postgres.users (identity: email) → stripe.customers (lookup by user_id)."""
    postgres_dataset = Dataset.parse_obj({
        "fides_key": "postgres_users",
        "name": "postgres_users",
        "collections": [{
            "name": "users",
            "fields": [
                {"name": "email", "fides_meta": {"identity": "email"}, "data_categories": ["user.contact.email"]},
                {"name": "user_id", "data_categories": ["user.unique_id"]},
            ],
        }],
    })
    stripe_dataset = Dataset.parse_obj({
        "fides_key": "stripe",
        "name": "stripe",
        "collections": [{
            "name": "customers",
            "fields": [
                {"name": "id", "data_categories": ["user.unique_id"], "fides_meta": {
                    "references": [{"dataset": "postgres_users", "field": "users.user_id", "direction": "from"}],
                }},
                {"name": "balance", "data_categories": ["user.financial"]},
            ],
        }],
    })
    postgres_graph = convert_dataset_to_graph(postgres_dataset, "postgres-users-db")
    stripe_graph = convert_dataset_to_graph(stripe_dataset, "stripe")
    return DatasetGraph(postgres_graph, stripe_graph)


@pytest.fixture
def connection_lookup() -> dict:
    """Maps dataset fides_key → ConnectionConfig metadata. Stub for the builder."""
    return {
        "postgres_users": {
            "connection_key": "postgres-users-db",
            "connector_type": "postgres",
            "system": {"fides_key": "users-system", "name": "Users", "data_use": "user.functional"},
        },
        "stripe": {
            "connection_key": "stripe",
            "connector_type": "stripe",
            "system": {"fides_key": "billing-system", "name": "Billing", "data_use": "user.financial"},
        },
    }
