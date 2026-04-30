from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi_pagination import Page, Params

from fides.api.util.cache import FidesopsRedis
from fides.service.pbac.consumers.entities import DataConsumerEntity
from fides.service.pbac.exceptions import ResourceNotFoundError
from fides.service.pbac.purposes.repository import DataPurposeRedisRepository
from fides.service.pbac.redis_repository import RedisRepository


class DataConsumerRedisRepository(RedisRepository[DataConsumerEntity]):
    """Redis-backed repository for non-system DataConsumer entities."""

    PREFIX = "data_consumer"

    def __init__(
        self,
        cache: FidesopsRedis,
        purpose_repo: DataPurposeRedisRepository,
    ) -> None:
        super().__init__(cache)
        self._purpose_repo = purpose_repo

    def _serialize(self, entity: DataConsumerEntity) -> str:
        return json.dumps(entity.to_dict())

    def _deserialize(self, data: str) -> DataConsumerEntity:
        return DataConsumerEntity.from_dict(json.loads(data))

    def _get_pk(self, entity: DataConsumerEntity) -> str:
        return entity.id

    def _get_index_entries(self, entity: DataConsumerEntity) -> list[tuple[str, str]]:
        entries: list[tuple[str, str]] = [("type", entity.type)]
        if entity.contact_email:
            entries.append(("contact_email", entity.contact_email))
        # Index each scope key individually for filtering
        for key, value in sorted(entity.scope.items()):
            entries.append(("scope", f"{key}={value}"))
        for tag in entity.tags:
            entries.append(("tag", tag))
        for fk in entity.purpose_fides_keys:
            entries.append(("purpose", fk))
        return entries

    def _resolve_purposes(self, entity: DataConsumerEntity) -> DataConsumerEntity:
        """Populate the purposes list from purpose_fides_keys."""
        if entity.purpose_fides_keys:
            entity.purposes = [
                p
                for fk in entity.purpose_fides_keys
                if (p := self._purpose_repo.get(fk)) is not None
            ]
        else:
            entity.purposes = []
        return entity

    # Override get/get_many to auto-resolve purposes

    def get(self, pk: str) -> Optional[DataConsumerEntity]:
        entity = super().get(pk)
        if entity:
            return self._resolve_purposes(entity)
        return None

    def get_many(self, pks: list[str]) -> list[DataConsumerEntity]:
        entities = super().get_many(pks)
        return [self._resolve_purposes(e) for e in entities]

    # ── Domain methods ────────────────────────────────────────────────

    def create(self, data: dict) -> DataConsumerEntity:
        now = datetime.now(timezone.utc)
        entity = DataConsumerEntity(
            id=str(uuid4()),
            name=data["name"],
            type=data["type"],
            description=data.get("description"),
            scope=data.get("scope") or {},
            egress=data.get("egress"),
            ingress=data.get("ingress"),
            data_shared_with_third_parties=data.get("data_shared_with_third_parties"),
            third_parties=data.get("third_parties"),
            shared_categories=data.get("shared_categories"),
            tags=data.get("tags") or [],
            contact_email=data.get("contact_email"),
            contact_slack_channel=data.get("contact_slack_channel"),
            contact_details=data.get("contact_details"),
            purpose_fides_keys=[],
            purposes=[],
            created_at=now,
            updated_at=now,
        )
        return self.save(entity)

    def update(self, id: str, data: dict) -> DataConsumerEntity:
        entity = self.get(id)
        if not entity:
            raise ResourceNotFoundError("DataConsumer", id)
        MUTABLE_FIELDS = {
            "name",
            "description",
            "scope",
            "egress",
            "ingress",
            "data_shared_with_third_parties",
            "third_parties",
            "shared_categories",
            "tags",
            "contact_email",
            "contact_slack_channel",
            "contact_details",
            "vendor_id",
            "type",
        }
        for field, value in data.items():
            if field in MUTABLE_FIELDS:
                setattr(entity, field, value)
        entity.updated_at = datetime.now(timezone.utc)
        self.save(entity)
        return self._resolve_purposes(entity)

    def delete_by_id(self, id: str) -> None:
        if not self.delete(id):
            raise ResourceNotFoundError("DataConsumer", id)

    def assign_purposes(
        self,
        id: str,
        purpose_fides_keys: list[str],
    ) -> DataConsumerEntity:
        """Replace all purposes (replace semantics)."""
        entity = self.get(id)
        if not entity:
            raise ResourceNotFoundError("DataConsumer", id)
        # Validate all purpose keys exist
        self._validate_purpose_keys(purpose_fides_keys)
        entity.purpose_fides_keys = purpose_fides_keys
        entity.updated_at = datetime.now(timezone.utc)
        self.save(entity)
        return self._resolve_purposes(entity)

    def add_purpose(
        self,
        id: str,
        purpose_fides_key: str,
    ) -> DataConsumerEntity:
        """Add a single purpose (idempotent)."""
        entity = self.get(id)
        if not entity:
            raise ResourceNotFoundError("DataConsumer", id)
        self._validate_purpose_keys([purpose_fides_key])
        if purpose_fides_key not in entity.purpose_fides_keys:
            entity.purpose_fides_keys.append(purpose_fides_key)
            entity.updated_at = datetime.now(timezone.utc)
            self.save(entity)
        return self._resolve_purposes(entity)

    def remove_purpose(
        self,
        id: str,
        purpose_fides_key: str,
    ) -> DataConsumerEntity:
        """Remove a single purpose."""
        entity = self.get(id)
        if not entity:
            raise ResourceNotFoundError("DataConsumer", id)
        if purpose_fides_key in entity.purpose_fides_keys:
            entity.purpose_fides_keys.remove(purpose_fides_key)
            entity.updated_at = datetime.now(timezone.utc)
            self.save(entity)
        return self._resolve_purposes(entity)

    def remove_purpose_from_all(self, purpose_fides_key: str) -> None:
        """Remove a purpose reference from all consumers that have it."""
        consumers = self.get_by_index("purpose", purpose_fides_key)
        for consumer in consumers:
            if purpose_fides_key in consumer.purpose_fides_keys:
                consumer.purpose_fides_keys.remove(purpose_fides_key)
                consumer.updated_at = datetime.now(timezone.utc)
                # Use base save to skip purpose resolution overhead
                RedisRepository.save(self, consumer)

    def list_page(  # type: ignore[override]
        self,
        params: Params,
        type: Optional[str] = None,
        purpose_fides_key: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> Page[DataConsumerEntity]:
        filters: list[tuple[str, str]] = []
        if type:
            filters.append(("type", type))
        if purpose_fides_key:
            filters.append(("purpose", purpose_fides_key))
        if tags:
            for tag in tags:
                filters.append(("tag", tag))
        return super().list_page(params, filters=filters or None)

    def _validate_purpose_keys(self, fides_keys: list[str]) -> None:
        """Check that all purpose fides_keys exist in the purpose repo."""
        for fk in fides_keys:
            if not self._purpose_repo.exists(fk):
                raise ResourceNotFoundError("DataPurpose", fk)
