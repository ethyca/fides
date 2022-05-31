# pylint: disable=missing-docstring, redefined-outer-name
import os
from typing import Dict, Generator, List
from urllib.parse import quote_plus

import pytest
import sqlalchemy
from fideslang.manifests import write_manifest
from fideslang.models import Dataset, DatasetCollection, DatasetField, DatasetMetadata
from py._path.local import LocalPath

from fidesctl.core import api
from fidesctl.core import dataset as _dataset
from fidesctl.core.config import FidesctlConfig


def create_server_datasets(
    test_config: FidesctlConfig, datasets: List[Dataset]
) -> None:
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


def set_field_data_categories(datasets: List[Dataset], category: str) -> None:
    for dataset in datasets:
        for collection in dataset.collections:
            for field in collection.fields:
                field.data_categories.append(category)


# Unit
@pytest.mark.unit
def test_create_db_datasets() -> None:
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
    actual_result = _dataset.create_db_datasets(test_resource)
    assert actual_result == expected_result


@pytest.mark.unit
def test_find_uncategorized_dataset_fields_all_categorized() -> None:
    test_resource = {"foo": ["1", "2"], "bar": ["4", "5"]}
    test_resource_dataset = _dataset.create_db_dataset("ds", test_resource)
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
        existing_dataset=dataset, source_dataset=test_resource_dataset
    )
    assert not uncategorized_keys
    assert total_field_count == 4


@pytest.mark.unit
def test_find_uncategorized_dataset_fields_uncategorized_fields() -> None:
    test_resource = {"foo": ["1", "2"]}
    test_resource_dataset = _dataset.create_db_dataset("ds", test_resource)
    existing_dataset = Dataset(
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
        existing_dataset=existing_dataset, source_dataset=test_resource_dataset
    )
    assert set(uncategorized_keys) == {"ds.foo.2"}
    assert total_field_count == 2


@pytest.mark.unit
def test_find_uncategorized_dataset_fields_missing_field() -> None:
    test_resource = {"bar": ["4", "5"]}
    test_resource_dataset = _dataset.create_db_dataset("ds", test_resource)
    existing_dataset = Dataset(
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
        existing_dataset=existing_dataset, source_dataset=test_resource_dataset
    )
    assert set(uncategorized_keys) == {"ds.bar.5"}
    assert total_field_count == 2


@pytest.mark.unit
def test_find_uncategorized_dataset_fields_missing_collection() -> None:
    test_resource = {"foo": ["1", "2"], "bar": ["4", "5"]}
    test_resource_dataset = _dataset.create_db_dataset("ds", test_resource)
    existing_dataset = Dataset(
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
        existing_dataset=existing_dataset, source_dataset=test_resource_dataset
    )
    assert set(uncategorized_keys) == {"ds.foo.1", "ds.foo.2"}
    assert total_field_count == 4


@pytest.mark.unit
def test_unsupported_dialect_error() -> None:
    test_url = "foo+psycopg2://fidesdb:fidesdb@fidesdb:5432/fidesdb"
    with pytest.raises(SystemExit):
        _dataset.generate_dataset_db(test_url, "test_file.yml", False)


@pytest.mark.unit
def test_get_dataset_resource_ids() -> None:
    datasets = [
        Dataset(
            fides_key="okta_id_1",
            name="okta_id_1",
            fidesctl_meta=DatasetMetadata(
                resource_id="okta_id_1",
            ),
            description="Fides Generated Description for Okta Application: okta_label_1",
            data_categories=[],
            collections=[],
        ),
        Dataset(
            fides_key="okta_id_2",
            name="okta_id_2",
            fidesctl_meta=DatasetMetadata(
                resource_id="okta_id_2",
            ),
            description="Fides Generated Description for Okta Application: okta_label_2",
            data_categories=[],
            collections=[],
        ),
        Dataset(
            fides_key="other_resource",
            name="other_resource",
            data_categories=[],
            collections=[],
        ),
    ]
    resource_ids = _dataset.get_dataset_resource_ids(datasets=datasets)
    assert resource_ids == ["okta_id_1", "okta_id_2"]


@pytest.mark.unit
def test_find_missing_datasets() -> None:
    okta_dataset_1 = Dataset(
        fides_key="okta_id_1",
        name="okta_id_1",
        fidesctl_meta=DatasetMetadata(
            resource_id="okta_id_1",
        ),
        description="Fides Generated Description for Okta Application: okta_label_1",
        data_categories=[],
        collections=[],
    )
    okta_dataset_2 = Dataset(
        fides_key="okta_id_2",
        name="okta_id_2",
        fidesctl_meta=DatasetMetadata(
            resource_id="okta_id_2",
        ),
        description="Fides Generated Description for Okta Application: okta_label_2",
        data_categories=[],
        collections=[],
    )
    okta_datasets = [okta_dataset_1, okta_dataset_2]
    existing_datasets = [okta_dataset_1]
    actual_result = _dataset.find_missing_datasets(
        source_datasets=okta_datasets, existing_datasets=existing_datasets
    )
    assert actual_result == [okta_dataset_2]


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
    quote_plus(os.getenv("SNOWFLAKE_FIDESCTL_PASSWORD", ""))
)

REDSHIFT_URL_TEMPLATE = "redshift+psycopg2://fidesctl:{}@redshift-cluster-1.cohs2e5eq2e4.us-east-1.redshift.amazonaws.com:5439/fidesctl_test"
REDSHIFT_URL = REDSHIFT_URL_TEMPLATE.format(
    quote_plus(os.getenv("REDSHIFT_FIDESCTL_PASSWORD", ""))
)


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
    def database_setup(self) -> Generator:
        """
        Set up the Database for testing.

        The query file must have each query on a separate line.
        """
        for database_parameters in TEST_DATABASE_PARAMETERS.values():
            engine = sqlalchemy.create_engine(database_parameters.get("setup_url"))
            with open(database_parameters.get("init_script_path"), "r") as query_file:  # type: ignore
                queries = [
                    query for query in query_file.read().splitlines() if query != ""
                ]
            print(queries)
            for query in queries:
                engine.execute(sqlalchemy.sql.text(query))
        yield

    def test_get_db_tables(self, request: Dict, database_type: str) -> None:
        database_parameters = TEST_DATABASE_PARAMETERS[database_type]
        engine = sqlalchemy.create_engine(database_parameters.get("url"))
        actual_result = _dataset.get_db_schemas(engine=engine)
        assert actual_result == database_parameters.get("expected_collection")

    def test_generate_dataset(self, tmpdir: LocalPath, database_type: str) -> None:
        database_parameters = TEST_DATABASE_PARAMETERS[database_type]
        actual_result = _dataset.generate_dataset_db(
            database_parameters.get("url"), f"{tmpdir}/test_file.yml", False
        )
        assert actual_result

    def test_generate_dataset_passes_(
        self, test_config: FidesctlConfig, database_type: str
    ) -> None:
        database_parameters = TEST_DATABASE_PARAMETERS[database_type]
        datasets: List[Dataset] = _dataset.create_db_datasets(
            database_parameters.get("expected_collection")
        )
        set_field_data_categories(datasets, "system.operations")
        create_server_datasets(test_config, datasets)
        _dataset.scan_dataset_db(
            connection_string=database_parameters.get("url"),
            manifest_dir="",
            coverage_threshold=100,
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
        )

    def test_generate_dataset_coverage_failure(
        self, test_config: FidesctlConfig, database_type: str
    ) -> None:
        database_parameters = TEST_DATABASE_PARAMETERS[database_type]
        datasets: List[Dataset] = _dataset.create_db_datasets(
            database_parameters.get("expected_collection")
        )
        create_server_datasets(test_config, datasets)
        with pytest.raises(SystemExit):
            _dataset.scan_dataset_db(
                connection_string=database_parameters.get("url"),
                manifest_dir="",
                coverage_threshold=100,
                url=test_config.cli.server_url,
                headers=test_config.user.request_headers,
            )

    def test_dataset_coverage_manifest_passes(
        self, test_config: FidesctlConfig, tmpdir: LocalPath, database_type: str
    ) -> None:
        database_parameters = TEST_DATABASE_PARAMETERS[database_type]
        datasets: List[Dataset] = _dataset.create_db_datasets(
            database_parameters.get("expected_collection")
        )
        set_field_data_categories(datasets, "system.operations")

        file_name = tmpdir.join("dataset.yml")
        write_manifest(file_name, [i.dict() for i in datasets], "dataset")

        create_server_datasets(test_config, datasets)
        _dataset.scan_dataset_db(
            connection_string=database_parameters.get("url"),
            manifest_dir=f"{tmpdir}",
            coverage_threshold=100,
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
        )


@pytest.mark.external
def test_generate_dataset_okta(tmpdir: LocalPath, test_config: FidesctlConfig) -> None:
    actual_result = _dataset.generate_dataset_okta(
        file_name=f"{tmpdir}/test_file.yml",
        include_null=False,
        okta_config={"orgUrl": "https://dev-78908748.okta.com"},
    )
    assert actual_result


@pytest.mark.external
def test_scan_dataset_okta_success(
    tmpdir: LocalPath, test_config: FidesctlConfig
) -> None:
    file_name = f"{tmpdir}/test_file.yml"
    _dataset.generate_dataset_okta(
        file_name=file_name,
        include_null=False,
        okta_config={"orgUrl": "https://dev-78908748.okta.com"},
    )
    _dataset.scan_dataset_okta(
        manifest_dir=file_name,
        okta_config={"orgUrl": "https://dev-78908748.okta.com"},
        coverage_threshold=100,
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
    )
    assert True


@pytest.mark.external
def test_scan_dataset_okta_fail(tmpdir: LocalPath, test_config: FidesctlConfig) -> None:
    with pytest.raises(SystemExit):
        _dataset.scan_dataset_okta(
            manifest_dir="",
            okta_config={"orgUrl": "https://dev-78908748.okta.com"},
            coverage_threshold=100,
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
        )
