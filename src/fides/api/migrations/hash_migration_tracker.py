from typing import Set, Type

from fides.api.db.base_class import Base


class HashMigrationTracker:
    """
    Singleton to track the status of the hash migration for various models.
    """

    _migrated_models: Set[str] = set()

    @classmethod
    def is_migrated(cls, model: type[Base]) -> bool:
        """
        Returns True if the hash migration is complete for the given model.
        """

        return model.__name__ in cls._migrated_models  # type:ignore[attr-defined]

    @classmethod
    def set_migrated(cls, model: type[Base]) -> None:
        """
        Sets the hash migration as complete for the given model.
        """

        cls._migrated_models.add(model.__name__)  # type:ignore[attr-defined]

    @classmethod
    def clear(cls) -> None:
        """
        Clear the tracker for testing purposes.
        """

        cls._migrated_models = set()
