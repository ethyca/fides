from enum import Enum
from typing import ByteString, Optional

from sqlalchemy import Column, Index, String
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from fides.api.db.base_class import Base


class DBCacheNamespace(Enum):
    """Namespaces for the DBCache"""

    LIST_PRIVACY_EXPERIENCE = "list-privacy-experience"

    # NOTE: monitor config key mapping entry is populated by migration
    # 2f3c1a2d6b10_disallow_dot_in_monitor_key_and_update_refs as a temporary means of
    # storing the mapping of 'old' monitor config keys with dots in them
    # to their new keys without dots.
    # This is a safety measure, in case we need to revert that data migration for whatever reason.
    # TODO: remove this cache entry in a future migration.
    MONITOR_CONFIG_KEY_MAPPING = "monitor-config-key-mapping"


class DBCache(Base):
    """
    Cache table for storing arbitrary data, useful when in-memory caches aren't enough.
    For example if cache contents need to be persisted across server restarts,
    or if the cache needs to be shared across different Fides instances.

    Warning: Cache contents are NOT encrypted, this shouldn't be used for storing
    any sort of personal data or sensitive information.
    """

    namespace = Column(
        String, nullable=False, index=True
    )  # Add a namespace since the same cache key could technically be used for different contexts
    cache_key = Column(String, nullable=False)
    cache_value = Column(BYTEA, nullable=False)

    __table_args__ = (
        Index("ix_dbcache_namespace_cache_key", "namespace", "cache_key", unique=True),
    )

    @classmethod
    def get_cache_entry(
        cls,
        db: Session,
        namespace: DBCacheNamespace,
        cache_key: str,
    ) -> Optional["DBCache"]:
        """
        Retrieves the cache entry for the given cache_key
        """
        return (
            db.query(cls)
            .filter(cls.namespace == namespace.value, cls.cache_key == cache_key)
            .first()
        )

    @classmethod
    def get_cache_value(
        cls,
        db: Session,
        namespace: DBCacheNamespace,
        cache_key: str,
    ) -> Optional[ByteString]:
        """
        Retrieves the cache value for the given cache_key
        """
        cache_entry = cls.get_cache_entry(db, namespace, cache_key)

        return cache_entry.cache_value if cache_entry else None

    @classmethod
    def set_cache_value(
        cls,
        db: Session,
        namespace: DBCacheNamespace,
        cache_key: str,
        cache_value: ByteString,
    ) -> "DBCache":
        """
        Upserts the cache value for the given cache_key
        """
        db_cache_entry = cls.get_cache_entry(db, namespace, cache_key)
        if db_cache_entry:
            db_cache_entry.cache_value = cache_value
            # We manually flag it as modified so that the update runs even if the cache_value hasn't changed
            # so the updated_at field of the cache entry gets updated.
            flag_modified(db_cache_entry, "cache_value")
        else:
            db_cache_entry = cls(
                namespace=namespace.value, cache_key=cache_key, cache_value=cache_value
            )

        db.add(db_cache_entry)
        db.commit()
        db.refresh(db_cache_entry)
        return db_cache_entry

    @classmethod
    def delete_cache_entry(
        cls,
        db: Session,
        namespace: DBCacheNamespace,
        cache_key: str,
    ) -> None:
        """
        Deletes the cache entry for the given cache_key
        """
        db.query(cls).filter(
            cls.namespace == namespace.value, cls.cache_key == cache_key
        ).delete()
        db.commit()

    @classmethod
    def clear_cache_for_namespace(
        cls,
        db: Session,
        namespace: DBCacheNamespace,
    ) -> None:
        """
        Deletes all cache entries for the given namespace
        """
        db.query(cls).filter(cls.namespace == namespace.value).delete()
        db.commit()

    @classmethod
    def clear_cache(
        cls,
        db: Session,
    ) -> None:
        """
        Deletes all cache entries
        """
        db.query(cls).delete()
        db.commit()
