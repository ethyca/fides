from fidesops.ops.models.datasetconfig import (
    DatasetConfig,
    FieldAddress,
    convert_dataset_to_graph,
)
from fidesops.ops.schemas.dataset import FidesopsDataset
from sqlalchemy.orm import Session

from ..graph.graph_test_util import field


def test_create_dataset(example_datasets, connection_config, db: Session) -> None:
    postgres_dataset = example_datasets[0]
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": postgres_dataset["fides_key"],
            "dataset": postgres_dataset,
        },
    )
    assert dataset_config.id is not None

    assert dataset_config.connection_config_id == connection_config.id
    assert dataset_config.fides_key == postgres_dataset["fides_key"]
    assert dataset_config.dataset["fides_key"] == postgres_dataset["fides_key"]
    assert len(dataset_config.dataset["collections"]) == 11
    assert dataset_config.created_at is not None
    orig_updated = dataset_config.updated_at
    assert orig_updated is not None

    dataset_config.dataset["description"] = "Updated description"
    dataset_config.save(db=db)
    assert dataset_config.updated_at is not None
    assert dataset_config.updated_at > orig_updated

    dataset_config.delete(db=db)


def test_get_graph(dataset_config: DatasetConfig) -> None:
    graph = dataset_config.get_graph()
    assert graph is not None
    assert graph.name == "postgres_example_subscriptions_dataset"
    assert len(graph.collections) == 1
    assert [collection.name for collection in graph.collections] == ["subscriptions"]
    assert graph.collections[0].fields[0].name == "email"
    assert graph.collections[0].fields[0].identity == "email"


def test_convert_dataset_to_graph_no_collections(example_datasets):
    dataset_json = example_datasets[0].copy()
    dataset_json["collections"] = []
    dataset = FidesopsDataset(**dataset_json)
    graph = convert_dataset_to_graph(dataset, "mock_connection_config_key")
    assert graph is not None
    assert graph.name == "postgres_example_test_dataset"
    assert len(graph.collections) == 0


def test_convert_dataset_to_graph(example_datasets):
    """Test a more complex dataset->graph conversion using the helper method directly"""

    dataset = FidesopsDataset(**example_datasets[0])
    graph = convert_dataset_to_graph(dataset, "mock_connection_config_key")

    assert graph is not None
    assert graph.name == "postgres_example_test_dataset"
    assert len(graph.collections) == 11

    # Spot-check some key nodes
    customer_collection = list(
        filter(lambda x: x.name == "customer", graph.collections)
    )[0]
    assert customer_collection
    assert customer_collection.fields[0].name == "address_id"
    assert customer_collection.fields[0].data_categories == ["system.operations"]
    assert customer_collection.fields[0].identity is None
    assert customer_collection.fields[0].references == [
        (FieldAddress("postgres_example_test_dataset", "address", "id"), "to")
    ]

    employee_collection = list(
        filter(lambda x: x.name == "employee", graph.collections)
    )[0]
    assert employee_collection
    assert employee_collection.fields[1].name == "email"
    assert employee_collection.fields[1].data_categories == ["user.contact.email"]
    assert employee_collection.fields[1].identity == "email"
    assert employee_collection.fields[1].references == []

    login_collection = list(filter(lambda x: x.name == "login", graph.collections))[0]
    assert login_collection
    assert login_collection.fields[0].name == "customer_id"
    assert login_collection.fields[0].data_categories == ["user.unique_id"]
    assert login_collection.fields[0].identity is None
    assert login_collection.fields[0].references == [
        (FieldAddress("postgres_example_test_dataset", "customer", "id"), "from")
    ]

    # check that primary key member has been set
    assert (
        field([graph], "postgres_example_test_dataset", "address", "id").primary_key
        is True
    )
    assert (
        field([graph], "postgres_example_test_dataset", "customer", "id").primary_key
        is True
    )
    assert (
        field([graph], "postgres_example_test_dataset", "employee", "id").primary_key
        is True
    )
    assert (
        field([graph], "postgres_example_test_dataset", "visit", "email").primary_key
        is False
    )


def test_convert_dataset_to_graph_array_fields(example_datasets):
    """Test a more complex dataset->graph conversion using the helper method directly"""

    dataset = FidesopsDataset(**example_datasets[1])
    graph = convert_dataset_to_graph(dataset, "mock_connection_config_key")

    assert graph is not None
    assert graph.name == "mongo_test"
    assert len(graph.collections) == 9

    rewards_collection = list(filter(lambda x: x.name == "rewards", graph.collections))[
        0
    ]
    assert rewards_collection
    owner_field = list(filter(lambda x: x.name == "owner", rewards_collection.fields))[
        0
    ]

    assert owner_field.is_array
    assert owner_field.data_type() == "object"
    assert owner_field.return_all_elements
    for field_name, field_obj in owner_field.fields.items():
        # Assert return_all_elements propagated to sub-fields for use in querying
        assert field_obj.return_all_elements

    points_field = list(
        filter(lambda x: x.name == "points", rewards_collection.fields)
    )[0]
    assert not points_field.is_array
    assert points_field.return_all_elements is None
