from abc import abstractmethod
from typing import List, Optional

from sqlalchemy import Boolean, Column

from fides.api.migrations.hash_migration_tracker import HashMigrationTracker
from fides.api.schemas.redis_cache import MultiValue


class HashMigrationMixin:
    """
    A mixin that includes common logic for models that have hashed fields that need be be migrated from using bcrypt to SHA-256.
    """

    # set existing rows to false but set to true on create since we'll
    # be using a new hashing function moving forward
    is_hash_migrated = Column(Boolean, nullable=False, server_default="f", default=True)

    @classmethod
    @abstractmethod
    def bcrypt_hash_value(
        cls,
        value: MultiValue,
        encoding: str = "UTF-8",
    ) -> Optional[str]:
        """Hash value using bcrypt."""

    @classmethod
    @abstractmethod
    def hash_value(
        cls,
        value: MultiValue,
        encoding: str = "UTF-8",
    ) -> Optional[str]:
        """Hash value using SHA-256."""

    @classmethod
    def hash_value_for_search(
        cls,
        value: MultiValue,
    ) -> List[str]:
        """
        Returns the SHA-256 hash and the bcrypt hash if the hash(es) on this table haven't been migrated yet.
        Once the migration is complete for this model, the function will only return the faster,
        SHA-256 and avoid the computationally expensive bcrypt hash.
        """

        hashed_values = []
        if hashed_value := cls.hash_value(value):
            hashed_values.append(hashed_value)
        if not HashMigrationTracker.is_migrated(cls.__name__):
            if hashed_value := cls.bcrypt_hash_value(value):
                hashed_values.append(hashed_value)
        return hashed_values

    @abstractmethod
    def migrate_hashed_fields(self) -> None:
        """
        Abstract method to migrate a single instance of a model with hashed fields.
        This method should be implemented by each model class that uses HashMigrationMixin.

        The implementation should:
        1. Read the encrypted fields
        2. Re-hash them with SHA-256
        3. Assign the new hash values to the hashed fields
        4. Mark the instance as migrated
        """
