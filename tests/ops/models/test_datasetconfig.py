import pytest
from fideslang.models import Dataset, FidesDatasetReference
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from fides.api.common_exceptions import ValidationError
from fides.api.models.datasetconfig import (
    DatasetConfig,
    FieldAddress,
    convert_dataset_to_graph,
    validate_dataset_reference,
)

from ..graph.graph_test_util import field


def test_create_dataset(
    example_datasets, connection_config, db: Session, ctl_dataset
) -> None:
    postgres_dataset = example_datasets[0]
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": postgres_dataset["fides_key"],
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    assert dataset_config.id is not None
    assert dataset_config.ctl_dataset_id is not None
    assert dataset_config.ctl_dataset == ctl_dataset

    assert dataset_config.connection_config_id == connection_config.id
    assert dataset_config.fides_key == postgres_dataset["fides_key"]
    assert dataset_config.ctl_dataset.fides_key == ctl_dataset.fides_key
    assert len(dataset_config.ctl_dataset.collections) == 1
    assert dataset_config.created_at is not None
    orig_updated = dataset_config.updated_at
    assert orig_updated is not None

    dataset_config.fides_key = "new fides key"
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
    dataset = Dataset(**dataset_json)
    graph = convert_dataset_to_graph(dataset, "mock_connection_config_key")
    assert graph is not None
    assert graph.name == "postgres_example_test_dataset"
    assert len(graph.collections) == 0


@pytest.mark.parametrize(
    "where_clauses,validation_error",
    [
        (
            [
                "`created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY) AND `created` <= CURRENT_TIMESTAMP()",
                "`created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2000 DAY) AND `created` <= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY)",
            ],
            None,
        ),
        (
            [
                "`created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY) AND `created` <= CURRENT_TIMESTAMP()",
                "`created` <= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY)",  # we support only a single comparison for 'terminal' partition windows
            ],
            None,
        ),
        (
            [
                "`created` > 4 OR 1 = 1",  # comparison operators after an OR are not permitted
                "`created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2000 DAY) AND `created` <= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY)",
            ],
            "Unsupported partition clause format",
        ),
        (
            [
                "`created` > 4) OR 1 > 0",  # comparison operators after an OR are not permitted
            ],
            "Unsupported partition clause format",
        ),
        (
            [
                "`created` > 4; drop table user",  # semi-colons are not allowed, so stacked queries are prevented
            ],
            "Unsupported partition clause format",
        ),
        (
            [
                "`created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2000 DAY) AND `foobar` <= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY)",  # field names in comparison must match
            ],
            "Partition clause must have matching fields",
        ),
        (
            [
                "`created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY) AND `created` <= CURRENT_TIMESTAMP()) OR 1 > 0",  # comparison operators after an OR are not permitted
            ],
            "Unsupported partition clause format",
        ),
        (
            [
                "`created` > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1000 DAY)) UNION\nSELECT password from user"  # union is a protected keyword not allowed in an operand
            ],
            "Prohibited keyword referenced in partition clause",
        ),
    ],
)
def test_convert_dataset_to_graph_partitioning(
    example_datasets, where_clauses, validation_error
):
    """
    Verify that a collection with partitioning specification
    goes through proper validation during graph conversion.
    """
    dataset_json = example_datasets[0].copy()
    existing_collection = dataset_json["collections"][0]
    if existing_collection.get("fides_meta") is None:
        existing_collection["fides_meta"] = {}
    existing_collection["fides_meta"]["partitioning"] = {
        "where_clauses": where_clauses,
    }
    dataset_json["collections"][0] = existing_collection
    dataset = Dataset(**dataset_json)
    if validation_error is None:
        graph = convert_dataset_to_graph(dataset, "mock_connection_config_key")
        assert graph is not None
        assert graph.name == "postgres_example_test_dataset"
        assert graph.collections[0].partitioning == {"where_clauses": where_clauses}
    else:
        with pytest.raises(PydanticValidationError) as e:
            graph = convert_dataset_to_graph(dataset, "mock_connection_config_key")
        assert validation_error in str(e)


def test_convert_dataset_to_graph(example_datasets):
    """Test a more complex dataset->graph conversion using the helper method directly"""

    dataset = Dataset(**example_datasets[0])
    customer_collection = list(
        filter(lambda x: x.name == "customer", dataset.collections)
    )[0]
    customer_collection.data_categories = {"user"}
    graph = convert_dataset_to_graph(dataset, "mock_connection_config_key")

    assert graph is not None
    assert graph.name == "postgres_example_test_dataset"
    assert len(graph.collections) == 11

    # Spot-check some key nodes
    customer_collection = list(
        filter(lambda x: x.name == "customer", graph.collections)
    )[0]
    assert customer_collection
    assert customer_collection.data_categories == {"user"}
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

    dataset = Dataset(**example_datasets[1])
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


def test_validate_dataset_reference(db: Session, dataset_config: DatasetConfig):
    """
    Happy path, test valid reference to existing dataset
    """
    dataset_key = dataset_config.fides_key
    collection_name = dataset_config.ctl_dataset.collections[0]["name"]
    field_name = dataset_config.ctl_dataset.collections[0]["fields"][0]["name"]
    dsr = FidesDatasetReference(
        dataset=dataset_key, field=f"{collection_name}.{field_name}"
    )
    validate_dataset_reference(db, dsr)


def test_validate_dataset_reference_invalid(db: Session, dataset_config: DatasetConfig):
    """
    Test that various types of invalid references to datasets raise expected errors
    """
    dataset_key = "fake_dataset"
    collection_name = dataset_config.ctl_dataset.collections[0]["name"]
    field_name = dataset_config.ctl_dataset.collections[0]["fields"][0]["name"]
    dsr = FidesDatasetReference(
        dataset=dataset_key, field=f"{collection_name}.{field_name}"
    )
    with pytest.raises(ValidationError) as e:
        validate_dataset_reference(db, dsr)
    assert "Unknown dataset" in e.value.message

    dataset_key = dataset_config.fides_key
    collection_name = "fake_collection"
    field_name = dataset_config.ctl_dataset.collections[0]["fields"][0]["name"]
    dsr = FidesDatasetReference(
        dataset=dataset_key, field=f"{collection_name}.{field_name}"
    )
    with pytest.raises(ValidationError) as e:
        validate_dataset_reference(db, dsr)
    assert "Unknown collection" in e.value.message

    dataset_key = dataset_config.fides_key
    collection_name = dataset_config.ctl_dataset.collections[0]["name"]
    field_name = "fake_field"
    dsr = FidesDatasetReference(
        dataset=dataset_key, field=f"{collection_name}.{field_name}"
    )
    with pytest.raises(ValidationError) as e:
        validate_dataset_reference(db, dsr)
    assert "Unknown field" in e.value.message

    dataset_key = dataset_config.fides_key
    collection_name = dataset_config.ctl_dataset.collections[0]["name"]
    field_name = "fake_field"
    dsr = FidesDatasetReference(dataset=dataset_key, field=f"{collection_name}.")
    with pytest.raises(ValidationError) as e:
        validate_dataset_reference(db, dsr)
    assert "must include at least two dot-separated components" in e.value.message

    dataset_key = dataset_config.fides_key
    collection_name = dataset_config.ctl_dataset.collections[0]["name"]
    field_name = "fake_field"
    dsr = FidesDatasetReference(dataset=dataset_key, field=f".{field_name}")
    with pytest.raises(ValidationError) as e:
        validate_dataset_reference(db, dsr)
    assert "must include at least two dot-separated components" in e.value.message

    dataset_key = dataset_config.fides_key
    collection_name = dataset_config.ctl_dataset.collections[0]["name"]
    field_name = "fake_field"
    dsr = FidesDatasetReference(dataset=dataset_key, field=f"{collection_name}")
    with pytest.raises(ValidationError) as e:
        validate_dataset_reference(db, dsr)
    assert "must include at least two dot-separated components" in e.value.message

    dataset_key = dataset_config.fides_key
    collection_name = dataset_config.ctl_dataset.collections[0]["name"]
    field_name = "fake_field"
    dsr = FidesDatasetReference(dataset=dataset_key, field=f".")
    with pytest.raises(ValidationError) as e:
        validate_dataset_reference(db, dsr)
    assert "must include at least two dot-separated components" in e.value.message

    dataset_key = dataset_config.fides_key
    collection_name = dataset_config.ctl_dataset.collections[0]["name"]
    field_name = "fake_field"
    dsr = FidesDatasetReference(dataset=dataset_key, field="")
    with pytest.raises(ValidationError) as e:
        validate_dataset_reference(db, dsr)
    assert "must include at least two dot-separated components" in e.value.message


class TestCreateOrUpdate:
    def test_no_existing_dataset_config_or_ctl_dataset(
        self, db, example_datasets, connection_config
    ):
        """Ctl Dataset is created"""
        postgres_dataset = example_datasets[0]

        dataset_config = DatasetConfig.create_or_update(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "brand_new_fides_key",
                "dataset": postgres_dataset,
            },
        )
        assert dataset_config.fides_key == "brand_new_fides_key"
        assert dataset_config.ctl_dataset_id is not None

        ctl_dataset = dataset_config.ctl_dataset

        assert (
            ctl_dataset.fides_key == "postgres_example_test_dataset"
        ), "New ctl dataset record created"
        assert ctl_dataset.description == postgres_dataset["description"]
        assert ctl_dataset.organization_fides_key == "default_organization"
        assert ctl_dataset.data_categories == postgres_dataset.get("data_categories")
        assert ctl_dataset.collections is not None

        # the `upsert` method instantiates a fideslang `Dataset` underneath.
        # that instantiation initializes some (important!) fields that aren't present
        # on the input data that's been passed in.
        # we need to do the same instantiation here, i.e. on the test side of the fence
        # to make our assertions more straightforward
        postgres_dataset_result = Dataset(**postgres_dataset)
        assert ctl_dataset.collections[0] == postgres_dataset_result.collections[
            0
        ].model_dump(mode="json")

        dataset_config.delete(db)
        ctl_dataset.delete(db)

    def test_no_existing_dataset_config_but_ctl_dataset_exists(
        self, db, ctl_dataset, connection_config
    ):
        """Ctl Dataset is created"""

        assert (
            ctl_dataset.description
            == "Example Postgres dataset created in test fixtures"
        )
        assert ctl_dataset.name == "Postgres Example Subscribers Dataset"
        current_ctl_dataset_id = ctl_dataset.id

        dataset_data = {
            "fides_key": "postgres_example_subscriptions_dataset",
            "name": "New Dataset Name",
            "description": "New Dataset Description",
            "dataset_type": "PostgreSQL",
            "location": "postgres_example.test",
            "collections": [
                {
                    "name": "subscriptions",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                            "fidesops_meta": {
                                "identity": "email",
                            },
                        },
                    ],
                }
            ],
        }
        dataset_config = DatasetConfig.create_or_update(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "brand_new_fides_key",
                "dataset": dataset_data,
            },
        )
        assert dataset_config.fides_key == "brand_new_fides_key"
        assert (
            dataset_config.ctl_dataset_id == current_ctl_dataset_id
        ), "Dataset config linked to existing ctl dataset"

        ctl_dataset = dataset_config.ctl_dataset

        assert (
            ctl_dataset.fides_key == "postgres_example_subscriptions_dataset"
        ), "Existing ctl dataset fides key"
        assert (
            ctl_dataset.description == "New Dataset Description"
        ), "Updated description"
        assert ctl_dataset.name == "New Dataset Name", "Updated name"

        assert ctl_dataset.organization_fides_key == "default_organization"
        assert ctl_dataset.data_categories is None
        assert ctl_dataset.collections is not None

        # the `upsert` method instantiates a fideslang `Dataset` underneath.
        # that instantiation initializes some (important!) fields that aren't present
        # on the input data that's been passed in.
        # we need to do the same instantiation here, i.e. on the test side of the fence
        # to make our assertions more straightforward
        dataset_result = Dataset(**dataset_data)
        assert ctl_dataset.collections[0] == dataset_result.collections[0].model_dump(
            mode="json"
        )

        dataset_config.delete(db)
        ctl_dataset.delete(db)

    def test_existing_dataset_config_and_ctl_dataset(self, dataset_config, db):
        existing_dataset_config_id = dataset_config.id
        existing_ctl_dataset_id = dataset_config.ctl_dataset_id
        existing_ctl_dataset_fides_key = dataset_config.ctl_dataset.fides_key

        dataset_data = {
            "fides_key": "brand_new_fides_key",
            "name": "New Dataset Name",
            "description": "New Dataset Description",
            "dataset_type": "PostgreSQL",
            "location": "postgres_example.test",
            "collections": [
                {
                    "name": "subscriptions",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                            "fidesops_meta": {
                                "identity": "email",
                            },
                        },
                    ],
                },
            ],
        }
        updated_dataset_config = DatasetConfig.create_or_update(
            db=db,
            data={
                "connection_config_id": dataset_config.connection_config_id,
                "fides_key": dataset_config.fides_key,
                "dataset": dataset_data,
            },
        )

        assert updated_dataset_config.id == existing_dataset_config_id
        assert updated_dataset_config.ctl_dataset_id == existing_ctl_dataset_id
        updated_ctl_dataset = updated_dataset_config.ctl_dataset

        assert (
            updated_ctl_dataset.fides_key != existing_ctl_dataset_fides_key
        ), "Because we updated based on the ctl_dataset.id, the fides key got changed"

        assert (
            updated_ctl_dataset.description == "New Dataset Description"
        ), "Updated description"
        assert updated_ctl_dataset.name == "New Dataset Name", "Updated name"

        assert updated_ctl_dataset.collections is not None

        # the `upsert` method instantiates a fideslang `Dataset` underneath.
        # that instantiation initializes some (important!) fields that aren't present
        # on the input data that's been passed in.
        # we need to do the same instantiation here, i.e. on the test side of the fence
        # to make our assertions more straightforward
        dataset_result = Dataset(**dataset_data)
        assert updated_ctl_dataset.collections[0] == dataset_result.collections[
            0
        ].model_dump(mode="json")
