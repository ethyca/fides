"""
Domain-specific repository interfaces for the Dataset service.

These protocols define the data access contracts that DatasetService depends on.
Production implementations use SqlAlchemy; tests use mocks.
"""

from __future__ import annotations

from typing import Any, List, Optional, Protocol

from fides.api.models.datasetconfig import DatasetConfig  # type: ignore[attr-defined]

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    Dataset as CtlDataset,
)


class DatasetRepository(Protocol):
    """Data access interface for CtlDataset records."""

    def get_by_fides_key(self, fides_key: str) -> Optional[CtlDataset]: ...

    def create(self, *, data: dict[str, Any]) -> CtlDataset: ...

    def update(self, dataset: CtlDataset, *, data: dict[str, Any]) -> CtlDataset: ...

    def delete(self, dataset: CtlDataset) -> None: ...

    def get_all(self) -> List[CtlDataset]: ...


class DatasetConfigRepository(Protocol):
    """Data access interface for DatasetConfig records."""

    def get_configs_for_dataset(self, dataset_id: str) -> List[DatasetConfig]: ...
