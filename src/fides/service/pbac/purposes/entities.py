from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from fides.api.models.data_purpose import (
        DataPurpose,  # type: ignore[import-not-found]
    )


@dataclass
class DataPurposeEntity:
    id: str
    fides_key: str
    name: str
    description: Optional[str]
    organization_fides_key: Optional[str]
    tags: Optional[list[str]]
    data_use: str
    data_subject: Optional[str]
    data_categories: list[str]
    legal_basis_for_processing: Optional[str]
    flexible_legal_basis_for_processing: bool
    special_category_legal_basis: Optional[str]
    impact_assessment_location: Optional[str]
    retention_period: Optional[str]
    features: list[str]
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["created_at"] = self.created_at.isoformat()
        d["updated_at"] = self.updated_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> DataPurposeEntity:
        d = dict(d)
        d["created_at"] = datetime.fromisoformat(d["created_at"])
        d["updated_at"] = datetime.fromisoformat(d["updated_at"])
        return cls(**d)

    @classmethod
    def from_orm(cls, obj: DataPurpose) -> DataPurposeEntity:
        return cls(
            id=obj.id,
            fides_key=obj.fides_key,
            name=obj.name,
            description=obj.description,
            organization_fides_key=obj.organization_fides_key,
            tags=obj.tags,
            data_use=obj.data_use,
            data_subject=obj.data_subject,
            data_categories=obj.data_categories or [],
            legal_basis_for_processing=obj.legal_basis_for_processing,
            flexible_legal_basis_for_processing=obj.flexible_legal_basis_for_processing,
            special_category_legal_basis=obj.special_category_legal_basis,
            impact_assessment_location=obj.impact_assessment_location,
            retention_period=obj.retention_period,
            features=obj.features or [],
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )
