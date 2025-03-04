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


def create_dataset_config_fixture(filename: str):
    """Factory function to create dataset config fixtures"""

    @pytest.fixture
    def _dataset_config(db: Session, connection_config: ConnectionConfig) -> Generator:
        dataset = load_example_dataset(filename)[0]
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

    return _dataset_config


directly_reachable_dataset_config = create_dataset_config_fixture(
    "directly_reachable.yml"
)

unreachable_without_data_categories_dataset_config = create_dataset_config_fixture(
    "unreachable_without_data_categories.yml"
)

unreachable_with_data_categories_dataset_config = create_dataset_config_fixture(
    "unreachable_with_data_categories.yml"
)

optional_identities_dataset_config = create_dataset_config_fixture(
    "optional_identities.yml"
)

unreachable_collection_dataset_config = create_dataset_config_fixture(
    "unreachable_collection.yml"
)

multiple_identities_dataset_config = create_dataset_config_fixture(
    "multiple_identities.yml"
)

reachable_by_reference_dataset_config = create_dataset_config_fixture(
    "reachable_by_reference.yml"
)
