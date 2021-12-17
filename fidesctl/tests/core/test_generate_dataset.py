import sqlalchemy
import pytest


from fidesctl.core import generate_dataset
from fideslang.models import Dataset, DatasetCollection, DatasetField


# These URLs are for the databases in the docker-compose.integration-tests.yml file
POSTGRES_URL = (
    "postgresql+psycopg2://postgres:postgres@postgres-test:5432/postgres_example"
)

MYSQL_URL = "mysql+pymysql://mysql_user:mysql_pw@mysql-test:3306/mysql_example"

SQLSERVER_URL_TEMPLATE = "mssql+pyodbc://sa:SQLserver1@sqlserver-test:1433/{}?driver=ODBC+Driver+17+for+SQL+Server"
SQLSERVER_URL = SQLSERVER_URL_TEMPLATE.format("sqlserver_example")
MASTER_SQLSERVER_URL = SQLSERVER_URL_TEMPLATE.format("master") + "&autocommit=True"


@pytest.fixture(scope="module")
def postgres_setup():
    "Set up the Postgres Database for testing."
    engine = sqlalchemy.create_engine(POSTGRES_URL)
    with open("tests/data/example_sql/postgres_example.sql", "r") as query_file:
        query = sqlalchemy.sql.text(query_file.read())
    engine.execute(query)
    yield


@pytest.fixture(scope="module")
def mysql_setup():
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


@pytest.fixture(scope="module")
def sqlserver_setup():
    """
    Set up the SQL Server Database for testing.

    The query file must have each query on a separate line.
    Initial connection must be done to the master database.
    """
    engine = sqlalchemy.create_engine(MASTER_SQLSERVER_URL)
    with open("tests/data/example_sql/sqlserver_example.sql", "r") as query_file:
        queries = [query for query in query_file.read().splitlines() if query != ""]
    print(queries)
    for query in queries:
        engine.execute(sqlalchemy.sql.text(query))
    yield


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
            description="Fides Generated Description for Schema: ds",
            collections=[
                DatasetCollection(
                    name="foo",
                    description="Fides Generated Description for Table: foo",
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
def test_generate_dataset_info(test_dataset):
    test_url = "postgresql+psycopg2://fidesdb:fidesdb@fidesdb:5432/fidesdb"
    test_engine = sqlalchemy.create_engine(test_url)
    actual_result = generate_dataset.create_dataset(
        test_engine, test_dataset.collections
    )
    assert actual_result == test_dataset


# Integration
@pytest.mark.integration
def test_get_db_tables_postgres(postgres_setup):
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
def test_get_db_tables_mysql(mysql_setup):
    engine = sqlalchemy.create_engine(MYSQL_URL)
    expected_result = {
        "mysql_example": {
            "mysql_example.visit": ["email", "last_visit"],
            "mysql_example.login": ["id", "customer_id", "time"],
        }
    }
    actual_result = generate_dataset.get_mysql_collections_and_fields(engine)
    assert actual_result == expected_result


@pytest.mark.integration
def test_get_db_tables_sqlserver(sqlserver_setup):
    engine = sqlalchemy.create_engine(SQLSERVER_URL)
    expected_result = {
        "sqlserver_example": {
            "sqlserver_example.visit": ["email", "last_visit"],
            "sqlserver_example.login": ["id", "customer_id", "time"],
        }
    }
    actual_result = generate_dataset.get_db_collections_and_fields(engine)
    assert actual_result == expected_result
