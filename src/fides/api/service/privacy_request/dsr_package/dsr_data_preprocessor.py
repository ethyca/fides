import re
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.privacy_request_redaction_pattern import (
    PrivacyRequestRedactionPattern,
)
from fides.api.service.privacy_request.dsr_package.utils import (
    get_redaction_entities_map_db,
)


class DSRDataPreprocessor:
    """
    Processes DSR data to apply name redaction before report generation.
    """

    def __init__(self, db: Session):
        self.db = db
        self.redaction_patterns: List[str] = (
            PrivacyRequestRedactionPattern.get_patterns(db) or []
        )
        self.entities_to_redact: Set[str] = get_redaction_entities_map_db(db)

    def process_dsr_data(self, dsr_data: dict[str, Any]) -> dict[str, Any]:
        """Process the DSR data to apply all redaction upfront."""
        if not self.redaction_patterns and not self.entities_to_redact:
            return dsr_data

        # First pass: collect and map dataset names
        dataset_mapping = self._create_dataset_mapping(dsr_data)

        # Second pass: process data with redaction
        processed_data = {}
        collection_indices: Dict[str, Dict[str, int]] = (
            {}
        )  # Track collection indices within each dataset

        for key, rows in dsr_data.items():
            # The "attachment" key is used to pass in the privacy request's attachments into `dsr_data`.
            # We don't need to redact these.
            if key == "attachments":
                processed_data[key] = rows
                continue

            dataset_name, collection_name = self._parse_key(key, rows)

            # Get redacted dataset name
            redacted_dataset = dataset_mapping.get(dataset_name, dataset_name)

            # Get redacted collection name (index per dataset)
            if dataset_name not in collection_indices:
                collection_indices[dataset_name] = {}

            if collection_name not in collection_indices[dataset_name]:
                collection_indices[dataset_name][collection_name] = (
                    len(collection_indices[dataset_name]) + 1
                )

            collection_index = collection_indices[dataset_name][collection_name]
            redacted_collection = self._redact_name(
                "collection", collection_name, collection_index, dataset_name
            )

            # Process rows
            new_key = f"{redacted_dataset}:{redacted_collection}"
            processed_data[new_key] = [
                self._process_row(row, dataset_name, collection_name) for row in rows
            ]

        return processed_data

    def _create_dataset_mapping(self, dsr_data: dict[str, Any]) -> Dict[str, str]:
        """Create dataset name mapping with ordered numbering for redacted datasets."""

        # Extract unique dataset names in order of appearance
        dataset_names = []
        for key, rows in dsr_data.items():
            if key not in ["attachments", "dataset"]:
                dataset_name, _ = self._parse_key(key, rows)
                dataset_names.append(dataset_name)

        unique_datasets = list(dict.fromkeys(dataset_names))

        # Create mapping using position-based numbering for redacted datasets
        mapping = {}

        # Handle regular datasets
        for index, name in enumerate(unique_datasets, 1):
            hierarchical_key = self._build_hierarchical_key("dataset", name)
            if self._should_redact(name, hierarchical_key):
                mapping[name] = f"dataset_{index}"
            else:
                mapping[name] = name  # Keep original name

        # Special "dataset" and "attachment" cases comes last
        # These keys are reserved for additional data and do not need to be redacted
        if "dataset" in dsr_data.keys():
            mapping["dataset"] = "dataset"

        if "attachments" in dsr_data.keys():
            mapping["attachments"] = "attachments"

        return mapping

    def _parse_key(self, key: str, rows: List[dict]) -> Tuple[str, str]:
        """Parse a key into dataset and collection names."""
        if ":" in key:
            parts = key.split(":", 1)
            return parts[0], parts[1]

        # Fallback logic
        for row in rows:
            if "system_name" in row:
                return row["system_name"], key
        return "manual", key

    def _should_redact(self, name: str, hierarchical_key: str) -> bool:
        """Check if a name should be redacted."""
        if hierarchical_key in self.entities_to_redact:
            return True

        for pattern in self.redaction_patterns:
            try:
                if re.search(pattern, name, re.IGNORECASE):
                    return True
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern}")

        return False

    def _redact_name(
        self,
        name_type: Literal["dataset", "collection", "field"],
        name: str,
        index: int,
        dataset_name: Optional[str] = None,
        collection_name: Optional[str] = None,
    ) -> str:
        """Apply redaction to a name based on patterns and configurations."""
        hierarchical_key = self._build_hierarchical_key(
            name_type, name, dataset_name, collection_name
        )

        if self._should_redact(name, hierarchical_key):
            return f"{name_type}_{index}"

        return name

    def _build_hierarchical_key(
        self,
        name_type: Literal["dataset", "collection", "field"],
        name: str,
        dataset_name: Optional[str] = None,
        collection_name: Optional[str] = None,
    ) -> str:
        """Build hierarchical key for entity lookup."""
        if name_type == "dataset":
            return name
        if name_type == "collection" and dataset_name:
            return f"{dataset_name}.{name}"
        if name_type == "field" and dataset_name and collection_name:
            return f"{dataset_name}.{collection_name}.{name}"
        return name

    def _process_row(
        self, row: dict[str, Any], dataset_name: str, collection_name: str
    ) -> dict[str, Any]:
        """Process a single row with field redaction."""
        processed = {}

        # Use enumerate for positional indexing (matches original)
        for field_index, (field_name, value) in enumerate(row.items(), start=1):
            redacted_field = self._redact_name(
                "field", field_name, field_index, dataset_name, collection_name
            )

            # Process nested values
            base_path = f"{dataset_name}.{collection_name}.{field_name}"
            processed[redacted_field] = self._process_nested_value(value, base_path)

        return processed

    def _process_nested_value(
        self,
        value: Any,
        current_path: str,
        field_index_counter: Optional[Dict[str, Dict[str, int]]] = None,
    ) -> Any:
        """Recursively process nested values matching original logic."""
        if field_index_counter is None:
            field_index_counter = {}

        if isinstance(value, dict):
            processed = {}
            level_key = f"{current_path}_fields"

            if level_key not in field_index_counter:
                field_index_counter[level_key] = {}

            for field_name, field_value in value.items():
                full_path = f"{current_path}.{field_name}"

                # Get or create index for this field at this level
                if field_name not in field_index_counter[level_key]:
                    field_index_counter[level_key][field_name] = (
                        len(field_index_counter[level_key]) + 1
                    )

                if self._should_redact(field_name, full_path):
                    redacted_name = (
                        f"field_{field_index_counter[level_key][field_name]}"
                    )
                else:
                    redacted_name = field_name

                processed[redacted_name] = self._process_nested_value(
                    field_value, full_path, field_index_counter
                )

            return processed

        if isinstance(value, list):
            return [
                self._process_nested_value(item, current_path, field_index_counter)
                for item in value
            ]

        return value
