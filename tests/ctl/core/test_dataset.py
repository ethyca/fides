# pylint: disable=missing-docstring, redefined-outer-name
import os
from typing import Dict, Generator, List
from urllib.parse import quote_plus
from uuid import uuid4

import pymssql
import pytest
import sqlalchemy
from fideslang.manifests import write_manifest
from fideslang.models import Dataset, DatasetCollection, DatasetField
from py._path.local import LocalPath
from sqlalchemy.orm import Session

from fides.api.db.crud import get_resource
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.config import FidesConfig
from fides.core import api
from fides.core import dataset as _dataset


def create_server_datasets(test_config: FidesConfig, datasets: List[Dataset]) -> None:
    for dataset in datasets:
        api.delete(
            url=test_config.cli.server_url,
            resource_type="dataset",
            resource_id=dataset.fides_key,
            headers=test_config.user.auth_header,
        )
        api.create(
            url=test_config.cli.server_url,
            resource_type="dataset",
            json_resource=dataset.json(exclude_none=True),
            headers=test_config.user.auth_header,
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
                            name="1",
                            description="Fides Generated Description for Column: 1",
                            data_categories=[],
                        ),
                        DatasetField(
                            name="2",
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
                            name="4",
                            description="Fides Generated Description for Column: 4",
                            data_categories=[],
                        ),
                        DatasetField(
                            name="5",
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
                        name="1",
                        data_categories=["category_1"],
                    ),
                    DatasetField(
                        name="2",
                        data_categories=["category_1"],
                    ),
                ],
            ),
            DatasetCollection(
                name="bar",
                fields=[
                    DatasetField(
                        name="4",
                        data_categories=["category_1"],
                    ),
                    DatasetField(name="5", data_categories=["category_1"]),
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


@pytest.fixture(scope="function")
def connection_config(
    db: Session,
) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_postgres_db_1",
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.write,
            "disabled": False,
            "description": "Primary postgres connection",
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.mark.unit
async def test_upsert_db_datasets(
    test_config: FidesConfig, db: Session, connection_config, async_session
) -> None:
    """
    Upsert a CTL Dataset, link this to a DatasetConfig and then upsert that CTL Dataset again.

    The id of the CTL Dataset cannot change on upsert, as the DatasetConfig has a FK to this resource.
    """

    dataset = Dataset(
        name="ds1",
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
                        name="1",
                        description="Fides Generated Description for Column: 1",
                        data_categories=[],
                    ),
                    DatasetField(
                        name="2",
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
                        name="4",
                        description="Fides Generated Description for Column: 4",
                        data_categories=[],
                    ),
                    DatasetField(
                        name="5",
                        description="Fides Generated Description for Column: 5",
                        data_categories=[],
                    ),
                ],
            ),
        ],
    )

    resp = api.upsert(
        url=test_config.cli.server_url,
        resource_type="dataset",
        resources=[dataset.model_dump(exclude_none=True)],
        headers=test_config.user.auth_header,
    )
    assert resp.status_code == 201
    assert resp.json()["inserted"] == 1

    ds: CtlDataset = await get_resource(CtlDataset, "ds", async_session)

    # Create a DatasetConfig that links to the created CTL Dataset
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": "new_fides_key",
            "ctl_dataset_id": ds.id,
        },
    )

    ctl_dataset_id = ds.id
    assert dataset_config.ctl_dataset_id == ctl_dataset_id

    # Do another upsert of the CTL Dataset to update the name
    dataset.name = "new name"
    resp = api.upsert(
        url=test_config.cli.server_url,
        resource_type="dataset",
        resources=[dataset.model_dump(exclude_none=True)],
        headers=test_config.user.auth_header,
    )
    assert resp.status_code == 200
    assert resp.json()["inserted"] == 0
    assert resp.json()["updated"] == 1

    db.refresh(dataset_config)
    assert dataset_config.ctl_dataset.name == "new name"
    assert dataset_config.ctl_dataset.id == ctl_dataset_id, "Id unchanged with upsert"


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
                        name="1",
                        data_categories=["category_1"],
                    ),
                    DatasetField(name="2"),
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
                        name="4",
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
                        name="4",
                        data_categories=["category_1"],
                    ),
                    DatasetField(
                        name="5",
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
    with pytest.raises(Exception):
        _dataset.generate_dataset_db(test_url, "test_file.yml", False)


@pytest.mark.unit
def test_field_data_categories(db) -> None:
    """
    Verify that field_data_categories works for fields with and without data categories.
    """

    ctl_dataset = CtlDataset.create_from_dataset_dict(
        db,
        {
            "fides_key": f"dataset_key-f{uuid4()}",
            "collections": [
                {
                    "name": "customer",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                        },
                        {"name": "first_name"},
                    ],
                }
            ],
        },
    )
    assert ctl_dataset.field_data_categories


@pytest.mark.unit
def test_namespace_meta(db) -> None:
    ctl_dataset = CtlDataset.create_from_dataset_dict(
        db,
        {
            "fides_key": f"dataset_key-f{uuid4()}",
            "fides_meta": {"namespace": {"dataset_id": "public"}},
            "collections": [],
        },
    )
    assert ctl_dataset.fides_meta == {
        "resource_id": None,
        "after": None,
        "namespace": {"dataset_id": "public"},
    }


# Generate Dataset Database Integration Tests

# These URLs are for the databases in the docker-compose.integration-tests.yml file
POSTGRES_URL = (
    "postgresql+psycopg2://postgres:postgres@postgres-test:5432/postgres_example?"
)

MYSQL_URL = "mysql+pymysql://mysql_user:mysql_pw@mysql-test:3306/mysql_example"

MSSQL_URL_TEMPLATE = "mssql+pymssql://sa:SQLserver1@sqlserver-test:1433/{}"
MSSQL_URL = MSSQL_URL_TEMPLATE.format("sqlserver_example")
MASTER_MSSQL_URL = MSSQL_URL_TEMPLATE.format("master")

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
        "init_script_path": "tests/ctl/data/example_sql/postgres_example.sql",
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
        "init_script_path": "tests/ctl/data/example_sql/mysql_example.sql",
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
        "server": "sqlserver-test:1433",
        "username": "sa",
        "password": "SQLserver1",
        "init_script_path": "tests/ctl/data/example_sql/sqlserver_example.sql",
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
        "init_script_path": "tests/ctl/data/example_sql/snowflake_example.sql",
        "is_external": True,
        "expected_collection": {
            "PUBLIC": {
                "VISIT": ["EMAIL", "LAST_VISIT"],
                "LOGIN": ["ID", "CUSTOMER_ID", "TIME"],
            }
        },
    },
    "redshift": {
        "url": REDSHIFT_URL,
        "setup_url": REDSHIFT_URL,
        "init_script_path": "tests/ctl/data/example_sql/redshift_example.sql",
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

            try:
                if "pymssql" not in database_parameters.get("setup_url", ""):
                    for query in queries:
                        engine.execute(sqlalchemy.sql.text(query))
                else:
                    with pymssql.connect(
                        database_parameters["server"],
                        database_parameters["username"],
                        database_parameters["password"],
                        autocommit=True,
                    ) as connection:
                        for query in queries:
                            with connection.cursor() as cursor:
                                cursor.execute(query)
            except:
                print(f"> FAILED DB SETUP: {database_parameters.get('setup_url')}")
                # We don't want to error all tests if a single setup fails
                pass
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
        self, test_config: FidesConfig, database_type: str
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
            headers=test_config.user.auth_header,
        )

    def test_generate_dataset_coverage_failure(
        self, test_config: FidesConfig, database_type: str
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
                headers=test_config.user.auth_header,
            )

    def test_dataset_coverage_manifest_passes(
        self, test_config: FidesConfig, tmpdir: LocalPath, database_type: str
    ) -> None:
        database_parameters = TEST_DATABASE_PARAMETERS[database_type]
        datasets: List[Dataset] = _dataset.create_db_datasets(
            database_parameters.get("expected_collection")
        )
        set_field_data_categories(datasets, "system.operations")

        file_name = tmpdir.join("dataset.yml")
        write_manifest(
            file_name, [i.model_dump(mode="json") for i in datasets], "dataset"
        )

        create_server_datasets(test_config, datasets)
        _dataset.scan_dataset_db(
            connection_string=database_parameters.get("url"),
            manifest_dir=f"{tmpdir}",
            coverage_threshold=100,
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
        )
