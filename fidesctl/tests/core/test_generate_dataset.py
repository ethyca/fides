import sqlalchemy
import pytest


from fidesctl.core import generate_dataset
from fideslang.models import Dataset, DatasetCollection, DatasetField


# These URLs are for the databases in the docker-compose.integration-tests.yml file
POSTGRES_URL = (
    "postgresql+psycopg2://postgres:postgres@postgres-test:5432/postgres_example?"
)

MYSQL_URL = "mysql+pymysql://mysql_user:mysql_pw@mysql-test:3306/mysql_example"

MSSQL_URL_TEMPLATE = "mssql+pyodbc://sa:SQLserver1@sqlserver-test:1433/{}?driver=ODBC+Driver+17+for+SQL+Server"
MSSQL_URL = MSSQL_URL_TEMPLATE.format("sqlserver_example")
MASTER_MSSQL_URL = MSSQL_URL_TEMPLATE.format("master") + "&autocommit=True"


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
def test_find_missing_dataset_fields_db_collections_missing_dataset():
    test_resource = {"otherds": {"foo": ["1", "2"], "bar": ["4", "5"]}}
    dataset = Dataset(
        name="ds",
        fides_key="ds",
        collections=[
            DatasetCollection(
                name="bar",
                fields=[
                    DatasetField(
                        name=4,
                    ),
                ],
            ),
        ],
    )
    with pytest.raises(SystemExit):
        generate_dataset.find_uncategorized_dataset_fields(
            dataset=dataset, db_collections=test_resource
        )


@pytest.mark.unit
def test_unsupported_dialect_error():
    test_url = "foo+psycopg2://fidesdb:fidesdb@fidesdb:5432/fidesdb"
    with pytest.raises(SystemExit):
        generate_dataset.generate_dataset(test_url, "test_file.yml")


@pytest.mark.postgres
class TestPostgres:
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
        expected_result = {
            "public": {
                "public.visit": ["email", "last_visit"],
                "public.login": ["id", "customer_id", "time"],
            }
        }
        actual_result = generate_dataset.get_postgres_collections_and_fields(engine)
        assert actual_result == expected_result

    @pytest.mark.integration
    def test_generate_dataset_postgres(self):
        actual_result = generate_dataset.generate_dataset(POSTGRES_URL, "test_file.yml")
        assert actual_result


@pytest.mark.mysql
class TestMySQL:
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
        expected_result = {
            "mysql_example": {
                "visit": ["email", "last_visit"],
                "login": ["id", "customer_id", "time"],
            }
        }
        actual_result = generate_dataset.get_mysql_collections_and_fields(engine)
        assert actual_result == expected_result

    @pytest.mark.integration
    def test_generate_dataset_mysql(self):
        actual_result = generate_dataset.generate_dataset(MYSQL_URL, "test_file.yml")
        assert actual_result


@pytest.mark.mssql
class TestSQLServer:
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
        expected_result = {
            "dbo": {
                "visit": ["email", "last_visit"],
                "login": ["id", "customer_id", "time"],
            }
        }
        actual_result = generate_dataset.get_mssql_collections_and_fields(engine)
        assert actual_result == expected_result

    @pytest.mark.integration
    def test_generate_dataset_mssql(self):
        actual_result = generate_dataset.generate_dataset(MSSQL_URL, "test_file.yml")
        assert actual_result
