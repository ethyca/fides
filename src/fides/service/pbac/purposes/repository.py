from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi_pagination import Page, Params

from fides.service.pbac.exceptions import (
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
)
from fides.service.pbac.purposes.entities import DataPurposeEntity
from fides.service.pbac.redis_repository import RedisRepository


class DataPurposeRedisRepository(RedisRepository[DataPurposeEntity]):
    """Redis-backed repository for DataPurpose entities."""

    PREFIX = "data_purpose"

    def _serialize(self, entity: DataPurposeEntity) -> str:
        return json.dumps(entity.to_dict())

    def _deserialize(self, data: str) -> DataPurposeEntity:
        return DataPurposeEntity.from_dict(json.loads(data))

    def _get_pk(self, entity: DataPurposeEntity) -> str:
        return entity.fides_key

    def _get_index_entries(self, entity: DataPurposeEntity) -> list[tuple[str, str]]:
        entries: list[tuple[str, str]] = [("data_use", entity.data_use)]
        if entity.data_subject:
            entries.append(("data_subject", entity.data_subject))
        return entries

    # ── Domain methods ────────────────────────────────────────────────

    def get_by_fides_key(self, fides_key: str) -> Optional[DataPurposeEntity]:
        return self.get(fides_key)

    def create(self, **kwargs: Any) -> DataPurposeEntity:
        fides_key = kwargs["fides_key"]
        if self.exists(fides_key):
            raise ResourceAlreadyExistsError(
                f"DataPurpose with fides_key '{fides_key}' already exists."
            )
        now = datetime.now(timezone.utc)
        entity = DataPurposeEntity(
            id=kwargs.get("id", str(uuid4())),
            fides_key=fides_key,
            name=kwargs["name"],
            description=kwargs.get("description"),
            organization_fides_key=kwargs.get("organization_fides_key"),
            tags=kwargs.get("tags"),
            data_use=kwargs["data_use"],
            data_subject=kwargs.get("data_subject"),
            data_categories=kwargs.get("data_categories", []),
            legal_basis_for_processing=kwargs.get("legal_basis_for_processing"),
            flexible_legal_basis_for_processing=kwargs.get(
                "flexible_legal_basis_for_processing", False
            ),
            special_category_legal_basis=kwargs.get("special_category_legal_basis"),
            impact_assessment_location=kwargs.get("impact_assessment_location"),
            retention_period=kwargs.get("retention_period"),
            features=kwargs.get("features", []),
            created_at=now,
            updated_at=now,
        )
        return self.save(entity)

    def update(self, fides_key: str, **kwargs: Any) -> DataPurposeEntity:
        entity = self.get(fides_key)
        if not entity:
            raise ResourceNotFoundError("DataPurpose", fides_key)
        MUTABLE_FIELDS = {
            "name",
            "description",
            "organization_fides_key",
            "tags",
            "data_use",
            "data_subject",
            "data_categories",
            "legal_basis_for_processing",
            "flexible_legal_basis_for_processing",
            "special_category_legal_basis",
            "impact_assessment_location",
            "retention_period",
            "features",
        }
        for field, value in kwargs.items():
            if field in MUTABLE_FIELDS:
                setattr(entity, field, value)
        entity.updated_at = datetime.now(timezone.utc)
        return self.save(entity)

    def delete_by_fides_key(self, fides_key: str) -> None:
        if not self.delete(fides_key):
            raise ResourceNotFoundError("DataPurpose", fides_key)

    def list_page(  # type: ignore[override]
        self,
        params: Params,
        data_use: Optional[str] = None,
        data_subject: Optional[str] = None,
    ) -> Page[DataPurposeEntity]:
        filters: list[tuple[str, str]] = []
        if data_use:
            filters.append(("data_use", data_use))
        if data_subject:
            filters.append(("data_subject", data_subject))
        return super().list_page(params, filters=filters or None)
