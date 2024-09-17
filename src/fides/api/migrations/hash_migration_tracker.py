from typing import Set


class HashMigrationTracker:
    """
    Singleton to track the status of the hash migration for various models.
    """

    _migrated_models: Set[str] = set()

    @classmethod
    def is_migrated(cls, model_name: str) -> bool:
        """
        Returns True if the hash migration is complete for the given model.
        """

        return model_name in cls._migrated_models

    @classmethod
    def set_migrated(cls, model_name: str) -> None:
        """
        Sets the hash migration as complete for the given model.
        """

        cls._migrated_models.add(model_name)

    @classmethod
    def clear(cls) -> None:
        """
        Clear the tracker for testing purposes.
        """

        cls._migrated_models = set()
