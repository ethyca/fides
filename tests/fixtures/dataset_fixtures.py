from typing import Dict, Generator, List

import pytest
import yaml
from fideslang.models import Dataset
from sqlalchemy.orm import Session

from fides.api.graph.graph import DatasetGraph
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig, convert_dataset_to_graph
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.models.sql_models import Organization
from fides.config.utils import load_file


def load_dataset(filename: str) -> Dict:
    yaml_file = load_file([filename])
    with open(yaml_file, "r") as file:
        return yaml.safe_load(file).get("dataset", [])


def load_dataset_as_string(filename: str) -> str:
    yaml_file = load_file([filename])
    with open(yaml_file, "r") as file:
        return file.read()


@pytest.fixture(scope="function")
def ctl_dataset(db: Session, example_datasets):
    ds = Dataset(
        fides_key="postgres_example_subscriptions_dataset",
        organization_fides_key="default_organization",
        name="Postgres Example Subscribers Dataset",
        description="Example Postgres dataset created in test fixtures",
        collections=[
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
    )
    dataset = CtlDataset(**ds.model_dump(mode="json"))
    db.add(dataset)
    db.commit()
    yield dataset
    dataset.delete(db)


@pytest.fixture(scope="function")
def unlinked_dataset(db: Session):
    ds = Dataset(
        fides_key="unlinked_dataset",
        organization_fides_key="default_organization",
        name="Unlinked Dataset",
        description="Example dataset created in test fixtures",
        collections=[
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
    )
    dataset = CtlDataset(**ds.model_dump(mode="json"))
    db.add(dataset)
    db.commit()
    yield dataset
    dataset.delete(db)


@pytest.fixture(scope="function")
def linked_dataset(db: Session, connection_config: ConnectionConfig) -> Generator:
    ds = Dataset(
        fides_key="linked_dataset",
        organization_fides_key="default_organization",
        name="Linked Dataset",
        description="Example dataset created in test fixtures",
        collections=[
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
    )
    dataset = CtlDataset(**ds.model_dump(mode="json"))
    db.add(dataset)
    db.commit()
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": "postgres_example_subscriptions_dataset",
            "ctl_dataset_id": dataset.id,
        },
    )

    yield dataset
    dataset_config.delete(db)
    dataset.delete(db)


@pytest.fixture(scope="function")
def dataset_config(
    connection_config: ConnectionConfig,
    ctl_dataset,
    db: Session,
) -> Generator:
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": "postgres_example_subscriptions_dataset",
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset_config
    dataset_config.delete(db)


@pytest.fixture(scope="function")
def dataset_config_preview(
    connection_config: ConnectionConfig, db: Session, ctl_dataset
) -> Generator:
    ctl_dataset.fides_key = "postgres"
    db.add(ctl_dataset)
    db.commit()
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": "postgres",
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset_config
    dataset_config.delete(db)


@pytest.fixture
def example_datasets() -> List[Dict]:
    example_datasets = []
    example_filenames = [
        "data/dataset/postgres_example_test_dataset.yml",
        "data/dataset/mongo_example_test_dataset.yml",
        "data/dataset/snowflake_example_test_dataset.yml",
        "data/dataset/redshift_example_test_dataset.yml",
        "data/dataset/mssql_example_test_dataset.yml",
        "data/dataset/mysql_example_test_dataset.yml",
        "data/dataset/mariadb_example_test_dataset.yml",
        "data/dataset/bigquery_example_test_dataset.yml",
        "data/dataset/manual_dataset.yml",
        "data/dataset/email_dataset.yml",
        "data/dataset/remote_fides_example_test_dataset.yml",
        "data/dataset/dynamodb_example_test_dataset.yml",
        "data/dataset/postgres_example_test_extended_dataset.yml",
        "data/dataset/google_cloud_sql_mysql_example_test_dataset.yml",
        "data/dataset/google_cloud_sql_postgres_example_test_dataset.yml",
        "data/dataset/scylladb_example_test_dataset.yml",
        "data/dataset/bigquery_enterprise_test_dataset.yml",
    ]
    for filename in example_filenames:
        example_datasets += load_dataset(filename)
    return example_datasets


@pytest.fixture
def example_yaml_datasets() -> str:
    example_filename = "data/dataset/example_test_datasets.yml"
    return load_dataset_as_string(example_filename)


@pytest.fixture
def example_yaml_dataset() -> str:
    example_filename = "data/dataset/postgres_example_test_dataset.yml"
    return load_dataset_as_string(example_filename)


@pytest.fixture
def example_invalid_yaml_dataset() -> str:
    example_filename = "data/dataset/example_test_dataset.invalid"
    return load_dataset_as_string(example_filename)


@pytest.fixture()
def postgres_dataset_graph(example_datasets, connection_config):
    dataset_postgres = Dataset(**example_datasets[0])
    graph = convert_dataset_to_graph(dataset_postgres, connection_config.key)

    dataset_graph = DatasetGraph(*[graph])
    return dataset_graph


@pytest.fixture()
def postgres_and_mongo_dataset_graph(
    example_datasets, connection_config, mongo_connection_config
):
    dataset_postgres = Dataset(**example_datasets[0])
    graph = convert_dataset_to_graph(dataset_postgres, connection_config.key)
    dataset_mongo = Dataset(**example_datasets[1])
    mongo_graph = convert_dataset_to_graph(dataset_mongo, mongo_connection_config.key)
    return DatasetGraph(*[graph, mongo_graph])


@pytest.fixture(scope="function")
def dataset_with_unreachable_collections(
    db: Session, test_fides_org: Organization
) -> Generator[CtlDataset, None, None]:
    dataset = Dataset(
        **{
            "name": "dataset with unreachable collections",
            "fides_key": "dataset_with_unreachable_collections",
            "organization_fides_key": test_fides_org.fides_key,
            "collections": [
                {
                    "name": "login",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["user.unique_id"],
                        },
                        {
                            "name": "customer_id",
                            "data_categories": ["user.unique_id"],
                        },
                    ],
                    "fides_meta": {"skip_processing": False},
                },
                {
                    "name": "report",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["user.unique_id"],
                        },
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                        },
                    ],
                    "fides_meta": {"skip_processing": False},
                },
            ],
        },
    )

    yield dataset


@pytest.fixture(scope="function")
def dataset_graph_with_unreachable_collections(
    dataset_with_unreachable_collections: Dataset,
) -> Generator[DatasetGraph, None, None]:
    graph = convert_dataset_to_graph(
        dataset_with_unreachable_collections, "unreachable-dataset-test"
    )
    dataset_graph = DatasetGraph(graph)
    yield dataset_graph
