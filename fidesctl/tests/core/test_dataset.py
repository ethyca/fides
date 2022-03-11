import sqlalchemy
import pytest
import os
from typing import List, Dict

from fidesctl.core import dataset as _dataset, api
from fideslang.manifests import write_manifest
from fideslang.models import Dataset, DatasetCollection, DatasetField


def create_server_datasets(test_config, datasets: List[Dataset]):
    for dataset in datasets:
        api.delete(
            url=test_config.cli.server_url,
            resource_type="dataset",
            resource_id=dataset.fides_key,
            headers=test_config.user.request_headers,
        )
        api.create(
            url=test_config.cli.server_url,
            resource_type="dataset",
            json_resource=dataset.json(exclude_none=True),
            headers=test_config.user.request_headers,
        )


def set_field_data_categories(datasets: List[Dataset], category: str):
    for dataset in datasets:
        for collection in dataset.collections:
            for field in collection.fields:
                field.data_categories.append(category)


@pytest.fixture()
def test_dataset():
    collections = [
        DatasetCollection(
            name="visit",
            description="Fides Generated Description for Table: visit",
            fields=[
                DatasetField(
                    name="email",
                    description="Fides Generated Description for Column: email",
                    data_categories=[],
                ),
                DatasetField(
                    name="last_visit",
                    description="Fides Generated Description for Column: last_visit",
                    data_categories=[],
                ),
            ],
        ),
        DatasetCollection(
            name="login",
            description="Fides Generated Description for Table: login",
            fields=[
                DatasetField(
                    name="id",
                    description="Fides Generated Description for Column: id",
                    data_categories=[],
                ),
                DatasetField(
                    name="customer_id",
                    description="Fides Generated Description for Column: customer_id",
                    data_categories=[],
                ),
                DatasetField(
                    name="time",
                    description="Fides Generated Description for Column: time",
                    data_categories=[],
                ),
            ],
        ),
    ]
    dataset = Dataset(
        fides_key="fidesdb",
        name="fidesdb",
        description="Fides Generated Description for Dataset: fidesdb",
        collections=collections,
    )
    yield dataset


# Unit
@pytest.mark.unit
def test_generate_dataset_collections():
    test_resource = {"ds": {"foo": ["1", "2"], "bar": ["4", "5"]}}
    expected_result = [
        Dataset(
            name="ds",
            fides_key="ds",
            data_categories=[],
            description="Fides Generated Description for Schema: ds",
            collections=[
                DatasetCollection(
                    name="foo",
                    description="Fides Generated Description for Table: foo",
                    data_categories=[],
                    fields=[
                        DatasetField(
                            name=1,
                            description="Fides Generated Description for Column: 1",
                            data_categories=[],
                        ),
                        DatasetField(
                            name=2,
                            description="Fides Generated Description for Column: 2",
                            data_categories=[],
                        ),
                    ],
                ),
                DatasetCollection(
                    name="bar",
                    description="Fides Generated Description for Table: bar",
                    data_categories=[],
                    fields=[
                        DatasetField(
                            name=4,
                            description="Fides Generated Description for Column: 4",
                            data_categories=[],
                        ),
                        DatasetField(
                            name=5,
                            description="Fides Generated Description for Column: 5",
                            data_categories=[],
                        ),
                    ],
                ),
            ],
        )
    ]
    actual_result = _dataset.create_dataset_collections(test_resource)
    assert actual_result == expected_result


@pytest.mark.unit
def test_find_uncategorized_dataset_fields_all_categorized():
    test_resource = {"ds": {"foo": ["1", "2"], "bar": ["4", "5"]}}
    dataset = Dataset(
        name="ds",
        fides_key="ds",
        collections=[
            DatasetCollection(
                name="foo",
                fields=[
                    DatasetField(
                        name=1,
                        data_categories=["category_1"],
                    ),
                    DatasetField(
                        name=2,
                        data_categories=["category_1"],
                    ),
                ],
            ),
            DatasetCollection(
                name="bar",
                fields=[
                    DatasetField(
                        name=4,
                        data_categories=["category_1"],
                    ),
                    DatasetField(name=5, data_categories=["category_1"]),
                ],
            ),
        ],
    )
    (
        uncategorized_keys,
        total_field_count,
    ) = _dataset.find_uncategorized_dataset_fields(
        dataset_key="ds", dataset=dataset, db_dataset=test_resource.get("ds")
    )
    assert not uncategorized_keys
    assert total_field_count == 4


@pytest.mark.unit
def test_find_uncategorized_dataset_fields_uncategorized_fields():
    test_resource = {"ds": {"foo": ["1", "2"]}}
    dataset = Dataset(
        name="ds",
        fides_key="ds",
        data_categories=["category_1"],
        collections=[
            DatasetCollection(
                name="foo",
                data_categories=["category_1"],
                fields=[
                    DatasetField(
                        name=1,
                        data_categories=["category_1"],
                    ),
                    DatasetField(name=2),
                ],
            )
        ],
    )
    (
        uncategorized_keys,
        total_field_count,
    ) = _dataset.find_uncategorized_dataset_fields(
        dataset_key="ds", dataset=dataset, db_dataset=test_resource.get("ds")
    )
    assert set(uncategorized_keys) == {"ds.foo.2"}
    assert total_field_count == 2


@pytest.mark.unit
def test_find_uncategorized_dataset_fields_missing_field():
    test_resource = {"ds": {"bar": ["4", "5"]}}
    dataset = Dataset(
        name="ds",
        fides_key="ds",
        collections=[
            DatasetCollection(
                name="bar",
                fields=[
                    DatasetField(
                        name=4,
                        data_categories=["category_1"],
                    )
                ],
            ),
        ],
    )
    (
        uncategorized_keys,
        total_field_count,
    ) = _dataset.find_uncategorized_dataset_fields(
        dataset_key="ds", dataset=dataset, db_dataset=test_resource.get("ds")
    )
    assert set(uncategorized_keys) == {"ds.bar.5"}
    assert total_field_count == 2


@pytest.mark.unit
def test_find_uncategorized_dataset_fields_missing_collection():
    test_resource = {"ds": {"foo": ["1", "2"], "bar": ["4", "5"]}}
    dataset = Dataset(
        name="ds",
        fides_key="ds",
        collections=[
            DatasetCollection(
                name="bar",
                fields=[
                    DatasetField(
                        name=4,
                        data_categories=["category_1"],
                    ),
                    DatasetField(
                        name=5,
                        data_categories=["category_1"],
                    ),
                ],
            ),
        ],
    )
    (
        uncategorized_keys,
        total_field_count,
    ) = _dataset.find_uncategorized_dataset_fields(
        dataset_key="ds", dataset=dataset, db_dataset=test_resource.get("ds")
    )
    assert set(uncategorized_keys) == {"ds.foo.1", "ds.foo.2"}
    assert total_field_count == 4


@pytest.mark.unit
def test_unsupported_dialect_error():
    test_url = "foo+psycopg2://fidesdb:fidesdb@fidesdb:5432/fidesdb"
    with pytest.raises(SystemExit):
        _dataset.generate_dataset(test_url, "test_file.yml", False)


# Generate Dataset Database Integration Tests

# These URLs are for the databases in the docker-compose.integration-tests.yml file
POSTGRES_URL = (
    "postgresql+psycopg2://postgres:postgres@postgres-test:5432/postgres_example?"
)

MYSQL_URL = "mysql+pymysql://mysql_user:mysql_pw@mysql-test:3306/mysql_example"

MSSQL_URL_TEMPLATE = "mssql+pyodbc://sa:SQLserver1@sqlserver-test:1433/{}?driver=ODBC+Driver+17+for+SQL+Server"
MSSQL_URL = MSSQL_URL_TEMPLATE.format("sqlserver_example")
MASTER_MSSQL_URL = MSSQL_URL_TEMPLATE.format("master") + "&autocommit=True"

# External databases require credentials passed through environment variables
SNOWFLAKE_URL_TEMPLATE = "snowflake://FIDESCTL:{}@ZOA73785/FIDESCTL_TEST"
SNOWFLAKE_URL = SNOWFLAKE_URL_TEMPLATE.format(
    os.getenv("SNOWFLAKE_FIDESCTL_PASSWORD", "")
)

REDSHIFT_URL_TEMPLATE = "redshift+psycopg2://fidesctl:{}@redshift-cluster-1.cohs2e5eq2e4.us-east-1.redshift.amazonaws.com:5439/fidesctl_test"
REDSHIFT_URL = REDSHIFT_URL_TEMPLATE.format(os.getenv("REDSHIFT_FIDESCTL_PASSWORD", ""))


TEST_DATABASE_PARAMETERS = {
    "postgresql": {
        "url": POSTGRES_URL,
        "setup_url": POSTGRES_URL,
        "init_script_path": "tests/data/example_sql/postgres_example.sql",
        "is_external": False,
        "expected_collection": {
            "public": {
                "visit": ["email", "last_visit"],
                "login": ["id", "customer_id", "time"],
            }
        },
    },
    "mysql": {
        "url": MYSQL_URL,
        "setup_url": MYSQL_URL,
        "init_script_path": "tests/data/example_sql/mysql_example.sql",
        "is_external": False,
        "expected_collection": {
            "mysql_example": {
                "visit": ["email", "last_visit"],
                "login": ["id", "customer_id", "time"],
            }
        },
    },
    "mssql": {
        "url": MSSQL_URL,
        "setup_url": MASTER_MSSQL_URL,
        "init_script_path": "tests/data/example_sql/sqlserver_example.sql",
        "is_external": False,
        "expected_collection": {
            "dbo": {
                "visit": ["email", "last_visit"],
                "login": ["id", "customer_id", "time"],
            }
        },
    },
    "snowflake": {
        "url": SNOWFLAKE_URL,
        "setup_url": SNOWFLAKE_URL,
        "init_script_path": "tests/data/example_sql/snowflake_example.sql",
        "is_external": True,
        "expected_collection": {
            "public": {
                "visit": ["email", "last_visit"],
                "login": ["id", "customer_id", "time"],
            }
        },
    },
    "redshift": {
        "url": REDSHIFT_URL,
        "setup_url": REDSHIFT_URL,
        "init_script_path": "tests/data/example_sql/redshift_example.sql",
        "is_external": True,
        "expected_collection": {
            "public": {
                "visit": ["email", "last_visit"],
                "login": ["id", "customer_id", "time"],
            }
        },
    },
}


@pytest.mark.external
@pytest.mark.parametrize("database_type", TEST_DATABASE_PARAMETERS.keys())
class TestDatabase:
    @pytest.fixture(scope="class", autouse=True)
    def database_setup(self):
        """
        Set up the Database for testing.

        The query file must have each query on a separate line.
        """
        for database_parameters in TEST_DATABASE_PARAMETERS.values():
            engine = sqlalchemy.create_engine(database_parameters.get("setup_url"))
            with open(database_parameters.get("init_script_path"), "r") as query_file:
                queries = [query for query in query_file.read().splitlines() if query != ""]
            print(queries)
            for query in queries:
                engine.execute(sqlalchemy.sql.text(query))
            yield

    def test_get_db_tables(self, request, database_type):
        print(request.node.get_closest_marker("external"))
        print(request.keywords)
        database_parameters = TEST_DATABASE_PARAMETERS.get(database_type)
        engine = sqlalchemy.create_engine(database_parameters.get("url"))
        actual_result = _dataset.get_db_collections_and_fields(engine)
        assert actual_result == database_parameters.get("expected_collection")

    def test_generate_dataset(self, tmpdir, database_type):
        database_parameters = TEST_DATABASE_PARAMETERS.get(database_type)
        actual_result = _dataset.generate_dataset(
            database_parameters.get("url"), f"{tmpdir}/test_file.yml", False
        )
        assert actual_result

    def test_generate_dataset_passes_(self, test_config, database_type):
        database_parameters = TEST_DATABASE_PARAMETERS.get(database_type)
        datasets: List[Dataset] = _dataset.create_dataset_collections(
            database_parameters.get("expected_collection")
        )
        set_field_data_categories(datasets, "system.operations")
        create_server_datasets(test_config, datasets)
        _dataset.scan_dataset(
            connection_string=database_parameters.get("url"),
            manifest_dir="",
            coverage_threshold=100,
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
        )

    def test_generate_dataset_coverage_failure(self, test_config, database_type):
        database_parameters = TEST_DATABASE_PARAMETERS.get(database_type)
        datasets: List[Dataset] = _dataset.create_dataset_collections(
            database_parameters.get("expected_collection")
        )
        create_server_datasets(test_config, datasets)
        with pytest.raises(SystemExit):
            _dataset.scan_dataset(
                connection_string=database_parameters.get("url"),
                manifest_dir="",
                coverage_threshold=100,
                url=test_config.cli.server_url,
                headers=test_config.user.request_headers,
            )

    def test_dataset_coverage_manifest_passes(self, test_config, tmpdir, database_type):
        database_parameters = TEST_DATABASE_PARAMETERS.get(database_type)
        datasets: List[Dataset] = _dataset.create_dataset_collections(
            database_parameters.get("expected_collection")
        )
        set_field_data_categories(datasets, "system.operations")

        file_name = tmpdir.join("dataset.yml")
        write_manifest(file_name, [i.dict() for i in datasets], "dataset")

        create_server_datasets(test_config, datasets)
        _dataset.scan_dataset(
            connection_string=database_parameters.get("url"),
            manifest_dir=f"{tmpdir}",
            coverage_threshold=100,
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
        )
