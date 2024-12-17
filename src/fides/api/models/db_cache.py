from enum import Enum
from typing import Any, Optional

from sqlalchemy import Column, String
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
    """

    namespace = Column(
        String, nullable=False, index=True
    )  # Add a namespace since the same cache key could technically be used for different contexts
    cache_key = Column(String, nullable=False, index=True)
    cache_value = Column(BYTEA, nullable=False)

    @classmethod
    def get_cache_value(
        cls,
        db: Session,
        namespace: DBCacheNamespace,
        cache_key: str,
    ) -> Optional[Any]:
        """
        Retrieves the cache value for the given cache_key
        """
        cache_entry = (
            db.query(cls)
            .filter(cls.namespace == namespace, cls.cache_key == cache_key)
            .first()
        )

        return cache_entry.cache_value if cache_entry else None
