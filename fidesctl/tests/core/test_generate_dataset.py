import sqlalchemy
import pytest
from typing import List, Dict

from fidesctl.core import generate_dataset, api
from fideslang.models import Dataset, DatasetCollection, DatasetField


# These URLs are for the databases in the docker-compose.integration-tests.yml file
POSTGRES_URL = (
    "postgresql+psycopg2://postgres:postgres@postgres-test:5432/postgres_example?"
)

MYSQL_URL = "mysql+pymysql://mysql_user:mysql_pw@mysql-test:3306/mysql_example"

MSSQL_URL_TEMPLATE = "mssql+pyodbc://sa:SQLserver1@sqlserver-test:1433/{}?driver=ODBC+Driver+17+for+SQL+Server"
MSSQL_URL = MSSQL_URL_TEMPLATE.format("sqlserver_example")
MASTER_MSSQL_URL = MSSQL_URL_TEMPLATE.format("master") + "&autocommit=True"

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
    actual_result = generate_dataset.create_dataset_collections(test_resource)
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
    missing_keys, coverage_rate = generate_dataset.find_uncategorized_dataset_fields(
        dataset=dataset, db_collections=test_resource
    )
    assert not missing_keys
    assert coverage_rate == 1


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
    missing_keys, coverage_rate = generate_dataset.find_uncategorized_dataset_fields(
        dataset=dataset, db_collections=test_resource
    )
    assert set(missing_keys) == {"ds.foo.2"}
    assert coverage_rate == 0.5


@pytest.mark.unit
def test_find_missing_dataset_fields_missing_field():
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
    missing_keys, coverage_rate = generate_dataset.find_uncategorized_dataset_fields(
        dataset=dataset, db_collections=test_resource
    )
    assert set(missing_keys) == {"ds.bar.5"}
    assert coverage_rate == 0.5


@pytest.mark.unit
def test_find_missing_dataset_fields_missing_collection():
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
    missing_keys, coverage_rate = generate_dataset.find_uncategorized_dataset_fields(
        dataset=dataset, db_collections=test_resource
    )
    assert set(missing_keys) == {"ds.foo.1", "ds.foo.2"}
    assert coverage_rate == 0.5

@pytest.mark.unit
def test_unsupported_dialect_error():
    test_url = "foo+psycopg2://fidesdb:fidesdb@fidesdb:5432/fidesdb"
    with pytest.raises(SystemExit):
        generate_dataset.generate_dataset(test_url, "test_file.yml")


@pytest.mark.postgres
class TestPostgres:
    EXPECTED_COLLECTION = {
        "public": {
            "public.visit": ["email", "last_visit"],
            "public.login": ["id", "customer_id", "time"],
        }
    }

    @pytest.fixture(scope="class", autouse=True)
    def postgres_setup(self):
        "Set up the Postgres Database for testing."
        engine = sqlalchemy.create_engine(POSTGRES_URL)
        with open("tests/data/example_sql/postgres_example.sql", "r") as query_file:
            query = sqlalchemy.sql.text(query_file.read())
        engine.execute(query)
        yield

    @pytest.mark.integration
    def test_get_db_tables_postgres(self):
        engine = sqlalchemy.create_engine(POSTGRES_URL)
        actual_result = generate_dataset.get_postgres_collections_and_fields(engine)
        assert actual_result == TestPostgres.EXPECTED_COLLECTION

    @pytest.mark.integration
    def test_generate_dataset_postgres(self, tmpdir):
        actual_result = generate_dataset.generate_dataset(POSTGRES_URL, f"{tmpdir}/test_file.yml")
        assert actual_result

    @pytest.mark.integration
    def test_generate_dataset_passes_postgres(self, test_config):
        datasets: List[Dataset] = generate_dataset.create_dataset_collections(TestPostgres.EXPECTED_COLLECTION)
        set_field_data_categories(datasets, "system.operations")
        create_server_datasets(test_config, datasets)
        generate_dataset.database_coverage(
                connection_string = POSTGRES_URL, 
                dataset_key = "public", 
                coverage_threshold = 1.0,
                url = test_config.cli.server_url,
                headers= test_config.user.request_headers,
        )

    @pytest.mark.integration
    def test_generate_dataset_coverage_failure_postgres(self, test_config):
        datasets: List[Dataset] = generate_dataset.create_dataset_collections(TestPostgres.EXPECTED_COLLECTION)
        create_server_datasets(test_config, datasets)
        with pytest.raises(SystemExit):
            generate_dataset.database_coverage(
                    connection_string = POSTGRES_URL, 
                    dataset_key = "public", 
                    coverage_threshold = 1.0,
                    url = test_config.cli.server_url,
                    headers= test_config.user.request_headers,
            )
@pytest.mark.mysql
class TestMySQL:
    EXPECTED_COLLECTION = {
        "mysql_example": {
            "visit": ["email", "last_visit"],
            "login": ["id", "customer_id", "time"],
        }
    }

    @pytest.fixture(scope="class", autouse=True)
    def mysql_setup(self):
        """
        Set up the MySQL Database for testing.

        The query file must have each query on a separate line.
        """
        engine = sqlalchemy.create_engine(MYSQL_URL)
        with open("tests/data/example_sql/mysql_example.sql", "r") as query_file:
            queries = [query for query in query_file.read().splitlines() if query != ""]
        print(queries)
        for query in queries:
            engine.execute(sqlalchemy.sql.text(query))
        yield

    @pytest.mark.integration
    def test_get_db_tables_mysql(self):
        engine = sqlalchemy.create_engine(MYSQL_URL)
        actual_result = generate_dataset.get_mysql_collections_and_fields(engine)
        assert actual_result == TestMySQL.EXPECTED_COLLECTION

    @pytest.mark.integration
    def test_generate_dataset_mysql(self,tmpdir):
        actual_result = generate_dataset.generate_dataset(MYSQL_URL, f"{tmpdir}test_file.yml")
        assert actual_result

    @pytest.mark.integration
    def test_generate_dataset_passes_mysql(self, test_config):
        datasets: List[Dataset] = generate_dataset.create_dataset_collections(TestMySQL.EXPECTED_COLLECTION)
        set_field_data_categories(datasets, "system.operations")
        create_server_datasets(test_config, datasets)
        generate_dataset.database_coverage(
                connection_string = MYSQL_URL, 
                dataset_key = "mysql_example", 
                coverage_threshold = 1.0,
                url = test_config.cli.server_url,
                headers= test_config.user.request_headers,
        )

    @pytest.mark.integration
    def test_generate_dataset_coverage_failure_mysql(self, test_config):
        datasets: List[Dataset] = generate_dataset.create_dataset_collections(TestMySQL.EXPECTED_COLLECTION)
        create_server_datasets(test_config, datasets)
        with pytest.raises(SystemExit):
            generate_dataset.database_coverage(
                    connection_string = MYSQL_URL, 
                    dataset_key = "mysql_example", 
                    coverage_threshold = 1.0,
                    url = test_config.cli.server_url,
                    headers= test_config.user.request_headers,
            )
@pytest.mark.mssql
class TestSQLServer:
    EXPECTED_COLLECTION = {
        "dbo": {
            "visit": ["email", "last_visit"],
            "login": ["id", "customer_id", "time"],
        }
    }
    
    @pytest.fixture(scope="class", autouse=True)
    def mssql_setup(self):
        """
        Set up the SQL Server Database for testing.

        The query file must have each query on a separate line.
        Initial connection must be done to the master database.
        """
        engine = sqlalchemy.create_engine(MASTER_MSSQL_URL)
        with open("tests/data/example_sql/sqlserver_example.sql", "r") as query_file:
            queries = [query for query in query_file.read().splitlines() if query != ""]
        print(queries)
        for query in queries:
            engine.execute(sqlalchemy.sql.text(query))
        yield

    @pytest.mark.integration
    def test_get_db_tables_mssql(self):
        engine = sqlalchemy.create_engine(MSSQL_URL)
        actual_result = generate_dataset.get_mssql_collections_and_fields(engine)
        assert actual_result == TestSQLServer.EXPECTED_COLLECTION

    @pytest.mark.integration
    def test_generate_dataset_mssql(self,tmpdir):
        actual_result = generate_dataset.generate_dataset(MSSQL_URL, f"{tmpdir}/test_file.yml")
        assert actual_result

    @pytest.mark.integration
    def test_generate_dataset_passes_mssql(self, test_config):
        datasets: List[Dataset] = generate_dataset.create_dataset_collections(TestSQLServer.EXPECTED_COLLECTION)
        set_field_data_categories(datasets, "system.operations")
        create_server_datasets(test_config, datasets)
        generate_dataset.database_coverage(
                connection_string = MSSQL_URL, 
                dataset_key = "dbo", 
                coverage_threshold = 1.0,
                url = test_config.cli.server_url,
                headers= test_config.user.request_headers,
        )

    @pytest.mark.integration
    def test_generate_dataset_coverage_failure_mssql(self, test_config):
        datasets: List[Dataset] = generate_dataset.create_dataset_collections(TestSQLServer.EXPECTED_COLLECTION)
        create_server_datasets(test_config, datasets)
        with pytest.raises(SystemExit):
            generate_dataset.database_coverage(
                    connection_string = MSSQL_URL, 
                    dataset_key = "dbo", 
                    coverage_threshold = 1.0,
                    url = test_config.cli.server_url,
                    headers= test_config.user.request_headers,
            )
