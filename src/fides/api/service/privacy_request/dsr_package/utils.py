from typing import Any, List, Optional

from fideslang.models import Dataset, DatasetField
from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType


# TODO: keeping this for a bit to help with development and testing
def get_redaction_entities_map(db: Session) -> set[str]:
    """
    Create a set of hierarchical entity keys that should be redacted based on fides_meta.redact: name.

    This utility function reads all enabled dataset configurations from the database
    and builds a set of hierarchical entity keys (dataset_name, dataset_name.collection_name,
    dataset_name.collection_name.field_name) that have fides_meta.redact set to "name".

    Supports deeply nested field structures with unlimited nesting depth.

    Args:
        db: Database session

    Returns:
        Set of hierarchical entity keys that should be redacted
    """
    redaction_entities = set()

    try:
        dataset_configs = DatasetConfig.all(db=db)

        for dataset_config in dataset_configs:
            ctl_dataset = dataset_config.ctl_dataset
            if not ctl_dataset:
                continue

            dataset = Dataset.model_validate(dataset_config.ctl_dataset)
            # Intentionally using the fides_key instead of name since it's always provided
            dataset_name = dataset.fides_key

            # Check dataset level
            if dataset.fides_meta and dataset.fides_meta.redact == "name":
                redaction_entities.add(dataset_name)

            # Check collection level
            for collection_dict in dataset.collections:
                # Collections are stored as dictionaries in the database
                collection_name = collection_dict.name
                if not collection_name:
                    continue

                collection_path = f"{dataset_name}.{collection_name}"
                collection_fides_meta = collection_dict.fides_meta

                if collection_fides_meta and collection_fides_meta.redact == "name":
                    redaction_entities.add(collection_path)

                # Check field level (with recursive nested field support)
                _traverse_fields_for_redaction(
                    collection_dict.fields, collection_path, redaction_entities
                )

    except Exception as exc:
        # Log error but don't fail, just return empty set
        logger.warning(f"Error extracting redaction configurations: {exc}")

    return redaction_entities


def get_redaction_entities_map_db(db: Session) -> set[str]:
    """
    Create a set of hierarchical entity keys that should be redacted based on fides_meta.redact: name.

    This function uses a hybrid approach:
    1. First identifies datasets that contain ANY redaction metadata at any level
    2. Then processes only those datasets with redaction metadata


    Args:
        db: Database session

    Returns:
        Set of hierarchical entity keys that should be redacted
    """
    redaction_entities: set[str] = set()

    try:
        # Step 1: Pre-filter to find datasets with ANY redaction metadata
        # Simple existence check - no paths needed, just check if redaction exists anywhere
        pre_filter_query = """
        SELECT DISTINCT dc.ctl_dataset_id
        FROM datasetconfig dc
        JOIN ctl_datasets ds ON dc.ctl_dataset_id = ds.id
        WHERE
            -- Dataset-level redaction
            ds.fides_meta->>'redact' = 'name'
            OR
            -- Collection-level redaction
            EXISTS (
                SELECT 1 FROM jsonb_array_elements(ds.collections::jsonb) AS collection
                WHERE collection->'fides_meta'->>'redact' = 'name'
                LIMIT 1
            )
            OR
            -- Field-level redaction using jsonb_path_query
            EXISTS (
                SELECT 1
                FROM jsonb_path_query(ds.collections::jsonb, '$.**.fides_meta') AS fides_meta
                WHERE fides_meta->>'redact' = 'name'
                LIMIT 1
            )
        """

        candidate_datasets = db.execute(pre_filter_query).fetchall()

        if not candidate_datasets:
            logger.debug("No datasets found with redaction metadata")
            return redaction_entities

        logger.debug(
            f"Pre-filtered to {len(candidate_datasets)} datasets with redaction metadata"
        )

        # Step 2: Process only the candidate datasets with targeted queries
        # Convert to a format we can use in SQL ANY clause
        dataset_ids = [row[0] for row in candidate_datasets]

        # Query for dataset-level redactions (only on candidate datasets)
        dataset_query = text(
            """
        SELECT ds.fides_key as entity_path
        FROM datasetconfig dc
        JOIN ctl_datasets ds ON dc.ctl_dataset_id = ds.id
        WHERE ds.id = ANY(:dataset_ids)
            AND ds.fides_meta->>'redact' = 'name'
        """
        )

        dataset_results = db.execute(
            dataset_query, {"dataset_ids": dataset_ids}
        ).fetchall()
        for row in dataset_results:
            redaction_entities.add(row[0])

        # Query for collection-level redactions (only on candidate datasets)
        collection_query = text(
            """
        SELECT ds.fides_key || '.' || (collection->>'name') as entity_path
        FROM datasetconfig dc
        JOIN ctl_datasets ds ON dc.ctl_dataset_id = ds.id
        CROSS JOIN LATERAL jsonb_array_elements(ds.collections::jsonb) AS collection
        WHERE ds.id = ANY(:dataset_ids)
            AND collection->'fides_meta'->>'redact' = 'name'
            AND collection->>'name' IS NOT NULL
        """
        )

        collection_results = db.execute(
            collection_query, {"dataset_ids": dataset_ids}
        ).fetchall()
        for row in collection_results:
            redaction_entities.add(row[0])

        # Query for field-level redactions (including nested fields)
        # This uses a recursive CTE to handle arbitrary nesting levels
        field_query = text(
            """
        WITH RECURSIVE field_hierarchy AS (
            -- Base case: top-level fields in collections (only candidate datasets)
            SELECT
                ds.fides_key || '.' ||
                    (collection->>'name') || '.' ||
                    (field->>'name') as entity_path,
                field->'fields' as nested_fields,
                field->'fides_meta'->>'redact' as redact_value
            FROM datasetconfig dc
            JOIN ctl_datasets ds ON dc.ctl_dataset_id = ds.id
            CROSS JOIN LATERAL jsonb_array_elements(ds.collections::jsonb) AS collection
            CROSS JOIN LATERAL jsonb_array_elements(collection->'fields') AS field
            WHERE ds.id = ANY(:dataset_ids)
                AND collection->>'name' IS NOT NULL
                AND field->>'name' IS NOT NULL

            UNION ALL

            -- Recursive case: nested fields
            SELECT
                fh.entity_path || '.' || (nested_field->>'name') as entity_path,
                nested_field->'fields' as nested_fields,
                nested_field->'fides_meta'->>'redact' as redact_value
            FROM field_hierarchy fh
            CROSS JOIN LATERAL jsonb_array_elements(fh.nested_fields) AS nested_field
            WHERE jsonb_typeof(fh.nested_fields) = 'array'
                AND nested_field->>'name' IS NOT NULL
        )
        SELECT DISTINCT entity_path
        FROM field_hierarchy
        WHERE redact_value = 'name'
        """
        )

        field_results = db.execute(field_query, {"dataset_ids": dataset_ids}).fetchall()
        for row in field_results:
            redaction_entities.add(row[0])

        logger.debug(f"Found {len(redaction_entities)} entities requiring redaction")

    except Exception as exc:
        # Log error but don't fail, just return empty set
        logger.warning(
            f"Error extracting redaction configurations from database: {exc}"
        )

    return redaction_entities


def map_privacy_request(privacy_request: PrivacyRequest) -> dict[str, Any]:
    """Creates a map with a subset of values from the privacy request"""
    request_data: dict[str, Any] = {}
    request_data["id"] = privacy_request.id

    action_type: Optional[ActionType] = privacy_request.policy.get_action_type()
    if action_type:
        request_data["type"] = action_type.value

    request_data["identity"] = {
        key: value
        for key, value in privacy_request.get_persisted_identity()
        .labeled_dict(include_default_labels=True)
        .items()
        if value["value"] is not None
    }

    if privacy_request.requested_at:
        request_data["requested_at"] = privacy_request.requested_at.strftime(
            "%m/%d/%Y %H:%M %Z"
        )
    return request_data


def _traverse_fields_for_redaction(
    fields: List[DatasetField], current_path: str, redaction_entities: set[str]
) -> None:
    """
    Recursively traverse nested fields to find redaction entities.

    Args:
        fields: List of field dictionaries to traverse
        current_path: Current hierarchical path (e.g., "dataset.collection")
        redaction_entities: Set to add redacted field paths to
    """
    for field in fields:
        field_name = field.name
        if not field_name:
            continue

        field_path = f"{current_path}.{field_name}"
        field_fides_meta = field.fides_meta

        if field_fides_meta and field_fides_meta.redact == "name":
            redaction_entities.add(field_path)

        # Recursively check nested fields
        if field.fields:
            _traverse_fields_for_redaction(field.fields, field_path, redaction_entities)
