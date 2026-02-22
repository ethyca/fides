"""
SqlAlchemy-backed implementations of the Dataset repository interfaces.

These are thin wrappers that delegate to OrmWrappedFidesBase class methods.
"""

from __future__ import annotations

from typing import Any, List, Optional

from sqlalchemy.orm import Session

from fides.api.models.datasetconfig import DatasetConfig  # type: ignore[attr-defined]

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    Dataset as CtlDataset,
)


class SqlAlchemyDatasetRepository:
    """Production DatasetRepository backed by SqlAlchemy."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_fides_key(self, fides_key: str) -> Optional[CtlDataset]:
        return (
            self._db.query(CtlDataset)
            .filter(CtlDataset.fides_key == fides_key)
            .first()
        )

    def create(self, *, data: dict[str, Any]) -> CtlDataset:
        return CtlDataset.create(self._db, data=data)

    def update(self, dataset: CtlDataset, *, data: dict[str, Any]) -> CtlDataset:
        return dataset.update(self._db, data=data)

    def delete(self, dataset: CtlDataset) -> None:
        dataset.delete(self._db)

    def get_all(self) -> List[CtlDataset]:
        return self._db.query(CtlDataset).all()


class SqlAlchemyDatasetConfigRepository:
    """Production DatasetConfigRepository backed by SqlAlchemy."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_configs_for_dataset(self, dataset_id: str) -> List[DatasetConfig]:
        return (
            self._db.query(DatasetConfig)
            .filter(DatasetConfig.ctl_dataset_id == dataset_id)
            .all()
        )
