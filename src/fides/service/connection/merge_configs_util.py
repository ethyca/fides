import copy
from typing import Any, List, Optional, cast

import yaml
from deepdiff import DeepDiff
from fideslang.models import Dataset as FideslangDataset
from loguru import logger
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from fides.api.models.detection_discovery.core import (
    MonitorConfig,
    StagedResource,
    StagedResourceAncestor,
)
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
        logger.warning(f"{dataset_name} normalization failed with unknown error: {e}")
        return None


def merge_datasets(
    customer_dataset: dict[str, Any],
    stored_dataset: dict[str, Any],
    upcoming_dataset: dict[str, Any],
    instance_key: str,
) -> dict[str, Any]:
    """Merges the datasets into a single dataset. Use the upcoming dataset as the base of the merge."""
    stored_dataset_copy = copy.deepcopy(stored_dataset)
    upcoming_dataset_copy = copy.deepcopy(upcoming_dataset)

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


def _get_endpoint_urns_with_monitored_fields(
    db: Session, monitor_config_ids: list[str]
) -> set[str]:
    """
    Helper function to get endpoint URNs that contain monitored field resources.

    Args:
        db: Database session
        monitor_config_ids: List of monitor config IDs to search within

    Returns:
        Set of endpoint URNs that contain monitored fields
    """

    # Find all field resources that are monitored for these monitor configs
    # Then get their ancestor URNs (which will be endpoint URNs) using StagedResourceAncestor
    # This gives us endpoints that contain at least one monitored field
    subquery = select(StagedResource.urn).where(  # type: ignore[arg-type]
        (StagedResource.monitor_config_id.in_(monitor_config_ids))
        & (StagedResource.resource_type == "Field")
        & (StagedResource.diff_status == "monitored")
    )

    monitored_fields_query = (
        select(StagedResourceAncestor.ancestor_urn)  # type: ignore[arg-type]
        .where(StagedResourceAncestor.descendant_urn.in_(subquery))
        .distinct()
    )

    result = db.execute(monitored_fields_query)
    return set(result.scalars().all())


def get_endpoint_resources(
    db: Session, connection_config: ConnectionConfig
) -> list[StagedResource]:
    """
    Get endpoint staged resources for a given connection config that have monitored fields.
    Since endpoint resources themselves are never monitored, we look for endpoints that
    contain field resources with monitored status.

    Returns:
        List of endpoint staged resources that contain monitored fields
    """
    # Get all monitor configs for this connection
    monitor_configs = MonitorConfig.filter(
        db=db,
        conditions=(MonitorConfig.connection_config_id == connection_config.id),
    ).all()

    if not monitor_configs:
        return []

    monitor_config_ids = [mc.key for mc in monitor_configs]

    # Get endpoint URNs that have monitored fields
    endpoint_urns_with_monitored_fields = _get_endpoint_urns_with_monitored_fields(
        db, monitor_config_ids
    )

    if not endpoint_urns_with_monitored_fields:
        return []

    # Now get the actual endpoint resources that have monitored fields
    endpoint_resources = StagedResource.filter(
        db=db,
        conditions=(
            (StagedResource.monitor_config_id.in_(monitor_config_ids))
            & (StagedResource.resource_type == "Endpoint")
            & (StagedResource.urn.in_(endpoint_urns_with_monitored_fields))
        ),
    ).all()

    return endpoint_resources


def merge_saas_config_with_monitored_resources(
    new_saas_config: SaaSConfig,
    monitored_endpoints: list[StagedResource],
    existing_saas_config: Optional[SaaSConfig] = None,
) -> SaaSConfig:
    """
    Merge new SaaS config with endpoint resources that contain monitored fields.

    Args:
        new_saas_config: The new SaaS config from template
        monitored_endpoints: List of endpoint staged resources that contain monitored fields
        existing_saas_config: The existing SaaS config that may contain promoted endpoints

    Returns:
        Merged SaaS config with preserved endpoints that have monitored fields
    """
    if not monitored_endpoints or not existing_saas_config:
        return new_saas_config

    # Create a copy of the new config to modify
    merged_config_dict = new_saas_config.model_dump()

    # Extract endpoint names from monitored resources (using name field)
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
                # Convert Pydantic model to dict to match the expected type
                merged_config_dict["endpoints"].append(
                    existing_endpoints[endpoint_name].model_dump()
                )
                logger.info(
                    f"Preserved monitored endpoint from existing config: {endpoint_name}"
                )

    return SaaSConfig(**merged_config_dict)


def _get_monitored_fields_by_endpoint(
    db: Session, monitor_config_ids: list[str], endpoint_urns: set[str]
) -> dict[str, list[StagedResource]]:
    """
    Helper function to get monitored field resources grouped by their endpoint URN.

    Args:
        db: Database session
        monitor_config_ids: List of monitor config IDs to search within
        endpoint_urns: Set of endpoint URNs to get monitored fields for

    Returns:
        Dictionary mapping endpoint URN to list of monitored field resources
    """
    if not endpoint_urns:
        return {}

    # Get all monitored field resources that belong to the specified endpoints
    # Note: ignore comments needed below due to outdated sqlalchemy-stubs
    monitored_fields_query = (
        select(StagedResource, StagedResourceAncestor.ancestor_urn)  # type: ignore[arg-type]
        .select_from(
            StagedResource.__table__.join(
                StagedResourceAncestor.__table__,
                StagedResourceAncestor.descendant_urn == StagedResource.urn,
            )
        )
        .where(
            (StagedResource.monitor_config_id.in_(monitor_config_ids))
            & (StagedResource.resource_type == "Field")
            & (StagedResource.diff_status == "monitored")
            & (StagedResourceAncestor.ancestor_urn.in_(endpoint_urns))
        )
    )

    result = db.execute(monitored_fields_query)

    # Group fields by endpoint URN
    fields_by_endpoint: dict[str, list[StagedResource]] = {}
    for staged_resource, ancestor_urn in result.fetchall():
        if ancestor_urn not in fields_by_endpoint:
            fields_by_endpoint[ancestor_urn] = []
        fields_by_endpoint[ancestor_urn].append(staged_resource)

    return fields_by_endpoint


def _extract_auto_classified_data_categories(
    classifications: Optional[list[dict[str, Any]]],
) -> list[str]:
    """
    Extract data categories from auto-classified results.

    Args:
        classifications: List of classification objects with 'label' field containing data categories

    Returns:
        List of data category labels from classifications
    """
    if not classifications:
        return []

    auto_classified_categories: list[str] = []
    for classification in classifications:
        if isinstance(classification, dict) and "label" in classification:
            label = classification["label"]
            if label and isinstance(label, str):
                auto_classified_categories.append(label)

    return auto_classified_categories


def _build_field_from_staged_resource(field_resource: StagedResource) -> dict[str, Any]:
    """
    Build a dataset field from a staged resource.

    Args:
        field_resource: The field staged resource

    Returns:
        Dictionary representing a dataset field
    """
    field: dict[str, Any] = {
        "name": field_resource.name,
    }

    # Add description if available
    if field_resource.description:
        field["description"] = field_resource.description

    # Add data categories (combine user-assigned and auto-classified)
    data_categories: list[str] = []

    # Start with user-assigned categories (these take precedence)
    if field_resource.user_assigned_data_categories:
        data_categories.extend(field_resource.user_assigned_data_categories)

    # Add auto-classified categories that aren't already present
    classifications_list = cast(
        Optional[list[dict[str, Any]]], field_resource.classifications
    )
    auto_classified_categories = _extract_auto_classified_data_categories(
        classifications_list
    )
    for category in auto_classified_categories:
        if category not in data_categories:
            data_categories.append(category)

    # Only add data_categories field if we have any categories
    if data_categories:
        field["data_categories"] = data_categories

    # Add data uses if available
    if field_resource.user_assigned_data_uses:
        field["data_uses"] = field_resource.user_assigned_data_uses

    # Add data type from meta if available
    if hasattr(field_resource, "meta") and field_resource.meta:
        if isinstance(field_resource.meta, dict) and "data_type" in field_resource.meta:
            field["fides_meta"] = {"data_type": field_resource.meta["data_type"]}

    return field


def _build_collection_from_staged_resources(
    endpoint: StagedResource, monitored_fields: list[StagedResource]
) -> dict[str, Any]:
    """
    Build a dataset collection from an endpoint and its monitored fields.

    Args:
        endpoint: The endpoint staged resource
        monitored_fields: List of monitored field staged resources under this endpoint

    Returns:
        Dictionary representing a dataset collection
    """
    collection: dict[str, Any] = {
        "name": endpoint.name,
        "description": None,
        "data_categories": None,
        "fields": [],
        "fides_meta": None,
    }

    # Add description if available
    if endpoint.description:
        collection["description"] = endpoint.description

    # Build fields from monitored staged resources
    for field_resource in monitored_fields:
        field_dict = _build_field_from_staged_resource(field_resource)
        if field_dict:
            collection["fields"].append(field_dict)

    return collection


def preserve_monitored_collections_in_dataset_merge(
    monitored_endpoints: list[StagedResource],
    upcoming_dataset: dict[str, Any],
    db: Session,
    monitor_config_ids: list[str],
) -> dict[str, Any]:
    """
    Build and preserve collections from monitored staged resources for collections that don't exist in upcoming dataset.

    This creates collections directly from staged resource data (endpoints and their monitored fields)
    ensuring we get the latest monitored data with proper classifications and metadata.

    Args:
        monitored_endpoints: List of endpoint staged resources that contain monitored fields
        upcoming_dataset: The new dataset from template
        db: Database session for querying monitored fields
        monitor_config_ids: List of monitor config IDs to search within

    Returns:
        Updated upcoming dataset with built collections for monitored endpoints
    """
    if not monitored_endpoints:
        return upcoming_dataset

    # Get collections that already exist in upcoming dataset
    upcoming_collections = {
        col.get("name"): col for col in upcoming_dataset.get("collections", [])
    }

    # Create a copy of upcoming dataset to modify
    merged_dataset = copy.deepcopy(upcoming_dataset)

    # Get monitored fields grouped by endpoint URN
    endpoint_urns = {resource.urn for resource in monitored_endpoints}
    monitored_fields_by_endpoint = _get_monitored_fields_by_endpoint(
        db, monitor_config_ids, endpoint_urns
    )

    # Build collections for endpoints that don't exist in upcoming dataset
    for endpoint in monitored_endpoints:
        collection_name = endpoint.name

        # Only process if collection doesn't exist in upcoming dataset
        if collection_name and collection_name not in upcoming_collections:
            if endpoint.urn in monitored_fields_by_endpoint:
                # Build collection from staged resources
                built_collection = _build_collection_from_staged_resources(
                    endpoint, monitored_fields_by_endpoint[endpoint.urn]
                )

                if built_collection and built_collection.get("fields"):
                    merged_dataset["collections"].append(built_collection)
                    logger.info(
                        f"Built collection '{collection_name}' with {len(built_collection['fields'])} monitored fields"
                    )

    return merged_dataset
