import sqlalchemy
import pytest
from unittest import mock


from fidesctl.core import generate_dataset


# Unit
@pytest.mark.unit
def test_generate_table_manifests():
    test_resource = {"foo": ["1", "2"], "bar": ["4", "5"]}
    expected_result = [
        {
            "name": "foo",
            "description": "Fides Generated Description for Table: foo",
            "dataset_fields": [
                {
                    "name": "1",
                    "description": "Fides Generated Description for Column: 1",
                    "data_categories": [],
                },
                {
                    "name": "2",
                    "description": "Fides Generated Description for Column: 2",
                    "data_categories": [],
                },
            ],
        },
        {
            "name": "bar",
            "description": "Fides Generated Description for Table: bar",
            "dataset_fields": [
                {
                    "name": "4",
                    "description": "Fides Generated Description for Column: 4",
                    "data_categories": [],
                },
                {
                    "name": "5",
                    "description": "Fides Generated Description for Column: 5",
                    "data_categories": [],
                },
            ],
        },
    ]
    actual_result = generate_dataset.generate_table_manifests(test_resource)
    assert actual_result == expected_result


# Integration
@pytest.mark.integration
def test_generate_dataset_info():
    test_url = "postgresql+psycopg2://fidesdb:fidesdb@fidesdb:5432/fidesdb"
    test_engine = sqlalchemy.create_engine(test_url)
    expected_result = {
        "dataset": [
            {
                "organization_fides_key": 1,
                "fides_key": "fidesdb",
                "name": "fidesdb",
                "description": f"Fides Generated Description for Dataset: fidesdb",
                "dataset_type": "postgresql",
                "dataset_location": "fidesdb:5432",
            }
        ]
    }
    actual_result = generate_dataset.generate_dataset_info(test_engine)
    assert actual_result == expected_result


@pytest.mark.integration
def test_get_db_tables():
    # Test Setup
    inspector = mock.Mock()
    inspector.get_table_names = lambda schema: test_tables
    inspector.get_columns = lambda x: {
        "foo": [{"name": "1"}, {"name": "2"}],
        "bar": [{"name": "3"}, {"name": "4"}],
    }.get(x)
    inspector.get_schema_names = lambda: ["test_db", "information_schema"]

    engine = mock.Mock()
    sqlalchemy.inspect = mock.Mock(return_value=inspector)
    test_tables = ["foo", "bar"]

    expected_result = {"test_db.bar": ["3", "4"], "test_db.foo": ["1", "2"]}
    actual_result = generate_dataset.get_db_tables(engine)
    assert actual_result == expected_result
