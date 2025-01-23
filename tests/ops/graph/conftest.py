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
def directly_reachable_dataset_config(
    db: Session,
    connection_config: ConnectionConfig,
) -> Generator:
    dataset = load_example_dataset("directly_reachable.yml")[0]
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
def unreachable_without_data_categories_dataset_config(
    db: Session,
    connection_config: ConnectionConfig,
) -> Generator:
    dataset = load_example_dataset("unreachable_without_data_categories.yml")[0]
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
