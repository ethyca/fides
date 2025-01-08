from enum import Enum
from typing import ByteString, Optional

from sqlalchemy import Column, Index, String
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base


class DBCacheNamespace(Enum):
    """Namespaces for the DBCache"""

    LIST_PRIVACY_EXPERIENCE = "list-privacy-experience"


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
        Index("ix_dbcache_namespace_cache_key", "namespace", "cache_key"),
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
