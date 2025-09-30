from datetime import datetime, timezone
from typing import List, Tuple

from fideslang.models import Dataset as FideslangDataset
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from fides.api.models.datasetconfig import DatasetConfig  # type: ignore[attr-defined]
from fides.api.schemas.dataset import ValidateDatasetResponse
from fides.service.dataset.dataset_validator import DatasetValidator

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    Dataset as CtlDataset,
)


class DatasetError(Exception):
    """Base class for dataset-related errors"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DatasetNotFoundException(DatasetError):
    """Raised when a dataset is not found"""


class LinkedDatasetException(DatasetError):
    """Raised when attempting to delete a dataset that's associated to a DatasetConfig"""


class DatasetService:
    def __init__(self, db: Session):
        self.db = db

    def validate_dataset(
        self,
        dataset: FideslangDataset,
    ) -> ValidateDatasetResponse:
        """
        Validates a standalone dataset for create/update operations, performing all necessary validations.
        """

        return DatasetValidator(self.db, dataset).validate()

    def create_dataset(self, dataset: FideslangDataset) -> CtlDataset:
        """Create a new dataset with validation"""
        self.validate_dataset(dataset)
        data_dict = dataset.model_dump(mode="json")
        return CtlDataset.create(self.db, data=data_dict)

    def update_dataset(self, dataset: FideslangDataset) -> CtlDataset:
        """Update an existing dataset with validation"""

        self.validate_dataset(dataset)
        existing = _get_ctl_dataset(self.db, dataset.fides_key)
        if not existing:
            raise DatasetNotFoundException(f"Dataset {dataset.fides_key} not found")

        # Update the dataset
        data_dict = dataset.model_dump(mode="json")
        return existing.update(self.db, data=data_dict)

    def get_dataset(self, fides_key: str) -> CtlDataset:
        """Get a single dataset by fides key"""
        dataset = _get_ctl_dataset(self.db, fides_key)
        if not dataset:
            raise DatasetNotFoundException(f"Dataset {fides_key} not found")
        return dataset

    def delete_dataset(self, fides_key: str) -> CtlDataset:
        """Delete a dataset by fides key"""
        dataset = self.get_dataset(fides_key)

        # Check if dataset is associated with any DatasetConfigs
        associated_configs = (
            self.db.query(DatasetConfig)
            .filter(DatasetConfig.ctl_dataset_id == dataset.id)
            .all()
        )

        if associated_configs:
            # Create detailed error message
            integration_details = []
            for config in associated_configs:
                connection_name = (
                    config.connection_config.name or config.connection_config.key
                )
                detail = f"'{connection_name}' ({config.connection_config.connection_type.value})"  # type: ignore[attr-defined]

                # Add system information if available
                if config.connection_config.system_id:
                    system = config.connection_config.system
                    if system:
                        system_name = system.name or system.fides_key
                        detail += f" in system '{system_name}'"

                integration_details.append(detail)

            message = (
                f"Cannot delete dataset '{fides_key}' because it is associated with "
                f"the following integration(s): {', '.join(integration_details)}. "
                f"Remove the dataset from these integrations before deleting."
            )

            raise LinkedDatasetException(message)

        dataset.delete(self.db)
        return dataset

    def upsert_datasets(self, datasets: List[FideslangDataset]) -> Tuple[int, int]:
        """
        For any dataset in `datasets` that already exists in the database,
        update the dataset by its `fides_key`. Otherwise, create a new dataset.

        Returns a tuple of (inserted_count, updated_count).
        """
        inserted = 0
        updated = 0

        for dataset in datasets:
            try:
                existing = (
                    self.db.query(CtlDataset)
                    .filter(CtlDataset.fides_key == dataset.fides_key)
                    .first()
                )

                if existing:
                    self.validate_dataset(dataset)
                    data_dict = dataset.model_dump(mode="json")
                    existing.update(self.db, data=data_dict)
                    updated += 1
                else:
                    self.create_dataset(dataset)
                    inserted += 1
            except Exception as e:
                logger.error(f"Error upserting dataset {dataset.fides_key}: {str(e)}")
                raise

        return inserted, updated

    def clean_datasets(self) -> Tuple[List[str], List[str]]:
        datasets = self.db.execute(select([CtlDataset])).scalars().all()
        return _run_clean_datasets(self.db, datasets)


def _get_ctl_dataset(db: Session, fides_key: str) -> CtlDataset:
    """Helper to get CTL dataset by fides_key"""
    ctl_dataset = db.query(CtlDataset).filter(CtlDataset.fides_key == fides_key).first()
    if not ctl_dataset:
        raise DatasetNotFoundException(
            f"No CTL dataset found with fides_key '{fides_key}'"
        )
    return ctl_dataset


def _run_clean_datasets(
    db: Session, datasets: List[FideslangDataset]
) -> tuple[List[str], List[str]]:
    """
    Clean the dataset name and structure to remove any malformed data possibly present from nested field regressions.
    Changes dot separated positional names to source names (ie. `user.address.street` -> `street`).
    """

    for dataset in datasets:
        logger.info(f"Cleaning field names for dataset: {dataset.fides_key}")
        for collection in dataset.collections:
            collection["fields"] = _recursive_clean_fields(collection["fields"])  # type: ignore # pylint: disable=unsupported-assignment-operation

        # manually upsert the dataset

        logger.info(f"Upserting dataset: {dataset.fides_key}")
        failed = []
        try:
            dataset_ctl_obj = (
                db.query(CtlDataset)
                .filter(CtlDataset.fides_key == dataset.fides_key)
                .first()
            )
            if dataset_ctl_obj:
                db.query(CtlDataset).filter(
                    CtlDataset.fides_key == dataset.fides_key
                ).update(
                    {
                        "collections": dataset.collections,
                        "updated_at": datetime.now(timezone.utc),
                    },
                    synchronize_session=False,
                )
                db.commit()
            else:
                logger.error(f"Dataset with fides_key {dataset.fides_key} not found.")
        except Exception as e:
            logger.error(f"Error upserting dataset: {dataset.fides_key} {e}")
            db.rollback()
            failed.append(dataset.fides_key)

    succeeded = [dataset.fides_key for dataset in datasets]
    return succeeded, failed


def _recursive_clean_fields(fields: List[dict]) -> List[dict]:
    """
    Recursively clean the fields of a dataset.
    """
    cleaned_fields = []
    for field in fields:
        field["name"] = field["name"].split(".")[-1]
        if field["fields"]:
            field["fields"] = _recursive_clean_fields(field["fields"])
        cleaned_fields.append(field)
    return cleaned_fields
