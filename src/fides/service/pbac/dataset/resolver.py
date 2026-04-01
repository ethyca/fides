"""Dataset resolution — maps table references to Fides dataset keys."""

from __future__ import annotations

from fides.service.pbac.types import TableRef


class DatasetResolver:
    """Resolve platform table references to Fides dataset fides_keys.

    Uses a configurable mapping strategy:
    - Direct match: ``{schema}.{table}`` → Fides dataset ``fides_key``
    - Qualified match: ``{catalog}.{schema}.{table}`` → Fides dataset
    - Custom prefix mapping (e.g., strip catalog prefix)
    """

    def __init__(
        self,
        dataset_mappings: dict[str, str] | None = None,
    ) -> None:
        self._mappings: dict[str, str] = dataset_mappings or {}

    def resolve(self, table_ref: TableRef) -> str | None:
        """Resolve a table reference to a Fides dataset fides_key."""
        if table_ref.qualified_name in self._mappings:
            return self._mappings[table_ref.qualified_name]

        short_name = f"{table_ref.schema}.{table_ref.table}"
        if short_name in self._mappings:
            return self._mappings[short_name]

        if table_ref.schema in self._mappings:
            return self._mappings[table_ref.schema]

        return table_ref.schema

    def add_mapping(self, platform_ref: str, fides_key: str) -> None:
        """Add a table reference → fides_key mapping."""
        self._mappings[platform_ref] = fides_key
