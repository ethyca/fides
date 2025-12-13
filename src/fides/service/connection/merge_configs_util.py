import copy
from typing import Any, List, Optional

import yaml
from deepdiff import DeepDiff
from fideslang.models import Dataset as FideslangDataset
from loguru import logger
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from fides.api.models.detection_discovery.core import MonitorConfig, StagedResource
from fides.api.schemas.saas.saas_config import SaaSConfig
from fides.api.service.connectors import ConnectionConfig
from fides.api.util.saas_util import replace_dataset_placeholders


def _get_fields(field: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Returns the fields of a dataset.
    If the fields attribute does not exist or is None, returns an empty list.
    """
    return field.get("fields", []) or []


def _merge_field(
    upcoming_field: Optional[dict[str, Any]],
    customer_field: Optional[dict[str, Any]],
    original_field: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    """
    Recursively merges a single field.
    If the customer made changes to the field (compared to stored dataset), preserve customer's version.
    If no changes were made by the customer, use the most recent integration version (upcoming).
    Handles nested fields recursively.
    """
    # Check if customer made changes to the field
    customer_made_changes = False
    if customer_field:
        # Compare customer vs original to detect if customer made changes
        diff = DeepDiff(original_field, customer_field, ignore_order=True)
        customer_made_changes = bool(diff)

    # Select the primary field to use
    primary_field = None
    if customer_made_changes:
        # Customer made changes, preserve customer's version
        primary_field = customer_field
    elif upcoming_field:
        # Customer didn't make changes, use most recent integration version (upcoming)
        primary_field = upcoming_field
    elif customer_field:
        # Field only exists in customer dataset, use customer version
        primary_field = customer_field

    if primary_field is None:
        return None

    # Deep copy to avoid mutating original
    merged_field = copy.deepcopy(primary_field)

    # fields can be an empty list or None, we handle both cases by converting to an empty list
    upcoming_nested_fields = _get_fields(upcoming_field) if upcoming_field else []
    customer_nested_fields = _get_fields(customer_field) if customer_field else []
    original_nested_fields = _get_fields(original_field) if original_field else []

    if upcoming_nested_fields or customer_nested_fields:
        nested_upcoming_fields_by_name = {
            field["name"]: field for field in upcoming_nested_fields
        }
        nested_customer_fields_by_name = {
            field["name"]: field for field in customer_nested_fields
        }
        nested_original_fields_by_name = {
            field["name"]: field for field in original_nested_fields
        }

        merged_nested_fields = _merge_fields(
            nested_upcoming_fields_by_name,
            nested_customer_fields_by_name,
            nested_original_fields_by_name,
        )
        # empty field list means the field should be None
        merged_field["fields"] = merged_nested_fields if merged_nested_fields else None

    return merged_field


def _merge_fields(
    upcoming_fields_by_name: dict[str, dict[str, Any]],
    customer_fields_by_name: dict[str, dict[str, Any]],
    original_fields_by_name: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Merges a list of fields by comparing upcoming, customer, and original versions.
    Returns a list of merged fields.

    Logic:
    - If customer made changes to a field (compared to original), preserve customer's version
    - If customer didn't make changes, use the most recent integration version (upcoming)

    Handles deleted fields:
    - If a field exists in original but not in upcoming, it was deleted by integration update
        and should NOT be preserved from customer dataset
    - If a field exists in customer but not in original, it was added by customer
        and should be preserved
    """
    # Get all unique field names from customer, base, and original
    all_field_names = (
        set(upcoming_fields_by_name.keys())
        | set(customer_fields_by_name.keys())
        | set(original_fields_by_name.keys())
    )

    merged_fields = []
    for field_name in all_field_names:
        upcoming_field = upcoming_fields_by_name.get(field_name)
        customer_field = customer_fields_by_name.get(field_name)
        original_field = original_fields_by_name.get(field_name)

        # Check if field was deleted in integration update
        # If it exists in original but not in base, it was deleted - skip it
        if original_field and not upcoming_field:
            # Field was deleted by integration update, don't preserve from customer
            continue

        # Otherwise, merge the field (handles all other cases including customer-added fields)
        merged_field = _merge_field(upcoming_field, customer_field, original_field)
        if merged_field:
            merged_fields.append(merged_field)

    return merged_fields


def _merge_collection(
    upcoming_collection: dict[str, Any],
    customer_collection: dict[str, Any],
    original_collection: dict[str, Any],
) -> dict[str, Any]:
    """
    Merges a collection by merging its fields.
    Returns the merged collection.
    """
    merged_collection = copy.deepcopy(upcoming_collection)

    # Build field maps for easy lookup
    upcoming_fields_by_name = {
        field["name"]: field for field in _get_fields(upcoming_collection)
    }
    original_fields_by_name = {
        field["name"]: field for field in _get_fields(original_collection)
    }
    customer_fields_by_name = {
        field["name"]: field for field in _get_fields(customer_collection)
    }

    # Merge fields recursively
    merged_fields = _merge_fields(
        upcoming_fields_by_name, customer_fields_by_name, original_fields_by_name
    )
    merged_collection["fields"] = merged_fields

    return merged_collection


def merge_datasets(
    customer_dataset: dict[str, Any],
    stored_dataset: dict[str, Any],
    upcoming_dataset: dict[str, Any],
    instance_key: str,
) -> dict[str, Any]:
    """Merges the datasets into a single dataset. Use the upcoming dataset as the base of the merge."""
    stored_dataset_copy = copy.deepcopy(stored_dataset)
    upcoming_dataset_copy = copy.deepcopy(upcoming_dataset)

    # Normalize stored and upcoming datasets to have the same complete structure as customer dataset
    # This ensures consistent field comparison by using the same Pydantic model serialization
    def normalize_dataset(
        dataset: dict[str, Any], dataset_name: str
    ) -> Optional[dict[str, Any]]:
        try:
            return FideslangDataset(**dataset).model_dump(mode="json")
        except PydanticValidationError as e:
            logger.warning(f"{dataset_name} normalization failed validation: {e}")
            return None
        except Exception as e:
            logger.warning(
                f"{dataset_name} normalization failed with unknown error: {e}"
            )
            return None

    normalized_stored_dataset = normalize_dataset(stored_dataset_copy, "stored")
    normalized_upcoming_dataset = normalize_dataset(upcoming_dataset_copy, "upcoming")
    if normalized_stored_dataset is None or normalized_upcoming_dataset is None:
        return upcoming_dataset

    stored_dataset_copy = normalized_stored_dataset
    upcoming_dataset_copy = normalized_upcoming_dataset

    # convert dataset to yaml string and then replace the instance key placeholder
    wrapped_dataset = {"dataset": [stored_dataset_copy]}
    stored_dataset_yaml = yaml.dump(wrapped_dataset)
    stored_dataset_copy = replace_dataset_placeholders(
        stored_dataset_yaml, "<instance_fides_key>", instance_key
    )

    upcoming_collections = {
        collection["name"]: collection
        for collection in upcoming_dataset_copy.get("collections", [])
    }
    original_collections = {
        collection["name"]: collection
        for collection in stored_dataset_copy.get("collections", [])
    }
    customer_collections_by_name = {
        collection["name"]: collection
        for collection in customer_dataset.get("collections", [])
    }

    # Collections can't be edited by customers, so we only process collections
    # that exist in the base dataset. Any new collections from customer are ignored.
    for collection_name, upcoming_collection in upcoming_collections.items():
        if collection_name in original_collections:
            # Collection exists in original, merge with customer version if available
            original_collection = original_collections[collection_name]
            customer_collection = customer_collections_by_name.get(collection_name)

            if customer_collection:
                # Merge the collection (recursively merges fields)
                merged_collection = _merge_collection(
                    upcoming_collection, customer_collection, original_collection
                )
                upcoming_collections[collection_name] = merged_collection

    # overwrite upcoming_dataset with merged collections + new official collections
    upcoming_dataset_copy["collections"] = list(upcoming_collections.values())

    merged_dataset = upcoming_dataset_copy
    return merged_dataset


def get_monitored_endpoint_resources_for_connection(
    db: Session, connection_config: ConnectionConfig
) -> List[StagedResource]:
    """
    Get monitored endpoint staged resources for a given connection config.
    Only returns Endpoint type resources since those are what we need to preserve.

    Returns:
        List of monitored endpoint staged resources
    """
    # Get all monitor configs for this connection
    monitor_configs = MonitorConfig.filter(
        db=db,
        conditions=(MonitorConfig.connection_config_id == connection_config.id),
    ).all()

    if not monitor_configs:
        return []

    monitor_config_ids = [mc.key for mc in monitor_configs]

    # Query staged resources with monitored status for these monitor configs
    # Only get Endpoint type resources since those represent SaaS endpoints/collections
    monitored_endpoints = StagedResource.filter(
        db=db,
        conditions=(
            (StagedResource.monitor_config_id.in_(monitor_config_ids))
            & (StagedResource.resource_type == "Endpoint")
        ),
    ).all()

    return monitored_endpoints


def merge_saas_config_with_monitored_resources(
    new_saas_config: SaaSConfig,
    monitored_endpoints: List[StagedResource],
    existing_saas_config: Optional[SaaSConfig] = None,
) -> SaaSConfig:
    """
    Merge new SaaS config with monitored endpoints from existing config.

    Args:
        new_saas_config: The new SaaS config from template
        monitored_endpoints: List of monitored endpoint staged resources
        existing_saas_config: The existing SaaS config that may contain promoted endpoints

    Returns:
        Merged SaaS config with preserved monitored endpoints
    """
    if not monitored_endpoints or not existing_saas_config:
        return new_saas_config

    # Create a copy of the new config to modify
    merged_config_dict = new_saas_config.model_dump()

    # Extract endpoint names from monitored resources (using description field)
    monitored_endpoint_names = {
        resource.name for resource in monitored_endpoints if resource.name
    }

    # Get existing endpoints from the current config
    existing_endpoints = {ep.name: ep for ep in existing_saas_config.endpoints}
    new_endpoints = {
        ep.get("name"): ep for ep in merged_config_dict.get("endpoints", [])
    }

    # Preserve monitored endpoints from existing config that aren't in the new template
    if "endpoints" in merged_config_dict:
        for endpoint_name in monitored_endpoint_names:
            if (
                endpoint_name not in new_endpoints
                and endpoint_name in existing_endpoints
            ):
                # Preserve the full endpoint from existing config (with all fields)
                merged_config_dict["endpoints"].append(
                    existing_endpoints[endpoint_name]
                )
                logger.info(
                    f"Preserved monitored endpoint from existing config: {endpoint_name}"
                )

    return SaaSConfig(**merged_config_dict)


def preserve_monitored_collections_in_dataset_merge(
    monitored_endpoints: List[StagedResource],
    customer_dataset: dict[str, Any],
    upcoming_dataset: dict[str, Any],
) -> dict[str, Any]:
    """
    Preserve monitored collections from customer dataset in the upcoming dataset.

    This ensures that promoted collections with all their fields are preserved
    when the dataset template is updated.

    Args:
        monitored_endpoints: List of monitored endpoint staged resources
        customer_dataset: The existing customer dataset (contains promoted collections)
        upcoming_dataset: The new dataset from template (may be missing promoted collections)

    Returns:
        Updated upcoming dataset with preserved monitored collections
    """
    if not monitored_endpoints or not customer_dataset.get("collections"):
        return upcoming_dataset

    # Extract collection names from monitored resources (using description field)
    monitored_collection_names = {
        resource.name for resource in monitored_endpoints if resource.name
    }

    # Get collections from customer and upcoming datasets
    customer_collections = {
        col.get("name"): col for col in customer_dataset.get("collections", [])
    }
    upcoming_collections = {
        col.get("name"): col for col in upcoming_dataset.get("collections", [])
    }

    # Create a copy of upcoming dataset to modify
    merged_dataset = copy.deepcopy(upcoming_dataset)

    # Preserve monitored collections from customer dataset that aren't in upcoming dataset
    for collection_name in monitored_collection_names:
        if (
            collection_name in customer_collections
            and collection_name not in upcoming_collections
        ):
            # Preserve the full collection from customer dataset (with all fields)
            merged_dataset["collections"].append(customer_collections[collection_name])
            logger.info(
                f"Preserved monitored collection from customer dataset: {collection_name}"
            )

    return merged_dataset
