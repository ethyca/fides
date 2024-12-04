import os
from typing import Any, Dict, Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from tests.fixtures.application_fixtures import load_dataset


def load_example_dataset(filename: str) -> Dict[str, Any]:
    """Helper function specifically for loading example dataset files"""

    test_dir = os.path.dirname(__file__)
    file_path = os.path.join(test_dir, "example_datasets", filename)

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Example dataset file not found: {file_path}. "
            f"Make sure the file exists in {os.path.join(test_dir, 'example_datasets')}"
        )

    return load_dataset(file_path)


@pytest.fixture
def single_identity_dataset_config(
    db: Session,
    connection_config: ConnectionConfig,
) -> Generator:
    dataset = load_example_dataset("single_identity.yml")[0]
    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)

    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": dataset["fides_key"],
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset_config
    dataset_config.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def single_identity_with_internal_dependency_dataset_config(
    db: Session,
    connection_config: ConnectionConfig,
) -> Generator:
    dataset = load_example_dataset("single_identity_with_internal_dependency.yml")[0]
    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)

    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": dataset["fides_key"],
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset_config
    dataset_config.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def multiple_identities_dataset_config(
    db: Session,
    connection_config: ConnectionConfig,
) -> Generator:
    dataset = load_example_dataset("multiple_identities.yml")[0]
    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)

    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": dataset["fides_key"],
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset_config
    dataset_config.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def multiple_identities_with_external_dependencies_dataset_config(
    db: Session,
    connection_config: ConnectionConfig,
) -> Generator:
    dataset = load_example_dataset("multiple_identities_with_external_dependency.yml")[
        0
    ]
    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)

    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": dataset["fides_key"],
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset_config
    dataset_config.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def optional_identities_dataset_config(
    db: Session,
    connection_config: ConnectionConfig,
) -> Generator:
    dataset = load_example_dataset("optional_identities.yml")[0]
    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)

    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": dataset["fides_key"],
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset_config
    dataset_config.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture
def no_identities_dataset_config(
    db: Session,
    connection_config: ConnectionConfig,
) -> Generator:
    dataset = load_example_dataset("no_identities.yml")[0]
    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)

    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": dataset["fides_key"],
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset_config
    dataset_config.delete(db=db)
    ctl_dataset.delete(db=db)
