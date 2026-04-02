"""Generic Redis-backed repository base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from fastapi_pagination import Page, Params
from loguru import logger

from fides.api.common_exceptions import RedisConnectionError
from fides.api.util.cache import FidesopsRedis

T = TypeVar("T")


class RedisRepository(ABC, Generic[T]):
    """Reusable base class for Redis-backed entity storage.

    Subclasses declare PREFIX, implement serialization hooks, and optionally
    declare secondary indexes.

    Public interface:
        save, get, delete, exists          — single-entity CRUD
        get_many, get_all                  — bulk reads
        list_page                          — paginated listing with optional filters
        get_by_index                       — fetch all entities matching a field value
    """

    PREFIX: str  # e.g. "data_purpose"

    def __init__(self, cache: FidesopsRedis) -> None:
        self._cache = cache

    # ── Key construction (private) ────────────────────────────────────

    def _entity_key(self, pk: str) -> str:
        return f"{self.PREFIX}:{pk}"

    def _all_key(self) -> str:
        return f"{self.PREFIX}:_all"

    def _index_key(self, field: str, value: str) -> str:
        return f"{self.PREFIX}:idx:{field}:{value}"

    # ── Subclass hooks ────────────────────────────────────────────────

    @abstractmethod
    def _serialize(self, entity: T) -> str:
        """Entity -> JSON string."""

    @abstractmethod
    def _deserialize(self, data: str) -> T:
        """JSON string -> Entity."""

    @abstractmethod
    def _get_pk(self, entity: T) -> str:
        """Extract primary key from entity."""

    def _get_index_entries(self, entity: T) -> list[tuple[str, str]]:
        """Return (field, value) pairs for secondary indexes."""
        return []

    # ── CRUD ──────────────────────────────────────────────────────────

    def save(self, entity: T) -> T:
        """Write entity + update indexes using a pipeline."""
        pk = self._get_pk(entity)
        key = self._entity_key(pk)

        try:
            pipe = self._cache.pipeline()
            # Remove stale index entries if entity already exists
            existing_data = self._cache.get(key)
            if existing_data:
                old_entity = self._deserialize(existing_data)
                for field, value in self._get_index_entries(old_entity):
                    pipe.srem(self._index_key(field, value), pk)

            # Write entity + add new indexes
            pipe.set(key, self._serialize(entity))
            pipe.sadd(self._all_key(), pk)
            for field, value in self._get_index_entries(entity):
                pipe.sadd(self._index_key(field, value), pk)
            pipe.execute()
        except RedisConnectionError:
            logger.error("Redis connection error during save of {}:{}", self.PREFIX, pk)
            raise

        return entity

    def get(self, pk: str) -> Optional[T]:
        """Read a single entity by primary key."""
        try:
            data = self._cache.get(self._entity_key(pk))
            if data:
                return self._deserialize(data)
            return None
        except RedisConnectionError:
            logger.error("Redis connection error during get of {}:{}", self.PREFIX, pk)
            raise

    def delete(self, pk: str) -> bool:
        """Remove entity + clean indexes. Returns True if entity existed."""
        try:
            key = self._entity_key(pk)
            data = self._cache.get(key)
            if not data:
                return False

            entity = self._deserialize(data)
            pipe = self._cache.pipeline()
            pipe.delete(key)
            pipe.srem(self._all_key(), pk)
            for field, value in self._get_index_entries(entity):
                pipe.srem(self._index_key(field, value), pk)
            pipe.execute()
            return True
        except RedisConnectionError:
            logger.error(
                "Redis connection error during delete of {}:{}", self.PREFIX, pk
            )
            raise

    def exists(self, pk: str) -> bool:
        """Check if an entity exists by primary key."""
        try:
            return bool(self._cache.exists(self._entity_key(pk)))
        except RedisConnectionError:
            logger.error(
                "Redis connection error during exists check of {}:{}", self.PREFIX, pk
            )
            raise

    # ── Bulk / pagination ─────────────────────────────────────────────

    def get_many(self, pks: list[str]) -> list[T]:
        """Fetch multiple entities by primary key."""
        if not pks:
            return []
        try:
            keys = [self._entity_key(pk) for pk in pks]
            values = self._cache.mget(keys)
            return [self._deserialize(v) for v in values if v is not None]
        except RedisConnectionError:
            logger.error("Redis connection error during get_many of {}", self.PREFIX)
            raise

    def get_all(self) -> list[T]:
        """Return all entities."""
        try:
            pks = self._cache.smembers(self._all_key())
            if not pks:
                return []
            return self.get_many(sorted(pks))
        except RedisConnectionError:
            logger.error("Redis connection error during get_all of {}", self.PREFIX)
            raise

    def list_page(
        self,
        params: Params,
        filters: Optional[list[tuple[str, str]]] = None,
    ) -> Page[T]:
        """Paginate over entities, optionally filtered by index values.

        Args:
            params: Pagination parameters.
            filters: Optional list of (field, value) tuples. When provided,
                only entities matching ALL filters are returned (intersection).
        """
        try:
            pks = self._resolve_pks(filters)
            sorted_pks = sorted(pks) if pks else []
            total = len(sorted_pks)

            page_num = params.page or 1
            page_size = params.size or 50
            start = (page_num - 1) * page_size
            end = start + page_size
            page_pks = sorted_pks[start:end]

            items = self.get_many(page_pks) if page_pks else []

            return Page.create(
                items=items,
                params=params,
                total=total,
            )
        except RedisConnectionError:
            logger.error("Redis connection error during list_page of {}", self.PREFIX)
            raise

    def get_by_index(self, field: str, value: str) -> list[T]:
        """Return all entities matching a secondary index value."""
        try:
            pks = self._cache.smembers(self._index_key(field, value))
            if not pks:
                return []
            return self.get_many(sorted(pks))
        except RedisConnectionError:
            logger.error(
                "Redis connection error during get_by_index of {}", self.PREFIX
            )
            raise

    # ── Private helpers ───────────────────────────────────────────────

    def _resolve_pks(self, filters: Optional[list[tuple[str, str]]] = None) -> set[str]:
        """Resolve the set of primary keys matching the given filters."""
        if not filters:
            return self._cache.smembers(self._all_key()) or set()

        index_keys = [self._index_key(field, value) for field, value in filters]

        if len(index_keys) == 1:
            return self._cache.smembers(index_keys[0]) or set()

        return self._cache.sinter(index_keys) or set()
