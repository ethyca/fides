import asyncio
import os
from typing import Any, Dict, List, Optional

from loguru import logger
from onepassword.client import Client  # Official SDK import

from fides.api.common_exceptions import FidesopsException

# Parameters for the 1Password client
params = {
    "SAAS_SECRETS_OP_VAULT_ID": os.getenv("SAAS_SECRETS_OP_VAULT_ID"),
    "SAAS_OP_SERVICE_ACCOUNT_TOKEN": os.getenv("SAAS_OP_SERVICE_ACCOUNT_TOKEN"),
}


_async_client = None
_title_to_id_mapping = {}
_mappings_initialized = False


async def _get_or_create_client():
    """Lazy initialization of 1Password client"""
    global _async_client
    if _async_client is None:
        if not params["SAAS_OP_SERVICE_ACCOUNT_TOKEN"]:
            logger.error("Missing SAAS_OP_SERVICE_ACCOUNT_TOKEN. ")
            return None

        _async_client = await Client.authenticate(
            auth=params["SAAS_OP_SERVICE_ACCOUNT_TOKEN"],
            integration_name="Fides Saas Secrets",
            integration_version="v1.0.0",
        )
    return _async_client


async def _initialize_mappings():
    """Initialize title-to-ID mappings for all vaults and items in memory"""
    global _title_to_id_mapping, _mappings_initialized

    if _mappings_initialized:
        return

    client = await _get_or_create_client()
    if client is None:
        logger.error("Failed to initialize 1Password Mappings.")
        return

    logger.info("Initializing vault and item mappings...")

    # Get items in the SaaS Secrets vault
    items = await client.items.list(vault_id=params["SAAS_SECRETS_OP_VAULT_ID"])

    for item in items:
        logger.debug(f"Processing item: {item.title}")

        # Create id mappings (store metadata, not secrets)
        _title_to_id_mapping[item.title] = {
            "item_id": item.id,
            "category": item.category,
        }

    _mappings_initialized = True
    logger.info(f"Initialized mappings for {len(_title_to_id_mapping)} items")


async def get_item_by_title(title: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a 1Password item by its title

    Args:
        title: The title of the item to retrieve

    Returns:
        Dict containing item information and fields, or None if not found
    """
    await _initialize_mappings()

    if title not in _title_to_id_mapping:
        logger.warning(f"Item '{title}' not found in mapping")
        return None

    info = _title_to_id_mapping[title]

    client = await _get_or_create_client()
    if client is None:
        logger.error("Failed to initialize 1Password client.")
        return None

    item = await client.items.get(
        item_id=info["item_id"], vault_id=params["SAAS_SECRETS_OP_VAULT_ID"]
    )

    # Convert to dictionary format
    item_dict = {
        "id": item.id,
        "title": item.title,
        "category": item.category,
        "fields": [],
    }

    # Add field information
    if hasattr(item, "fields") and item.fields:
        for field in item.fields:
            field_info = {
                "id": getattr(field, "id", ""),
                "title": getattr(field, "title", ""),
                "type": getattr(field, "field_type", ""),
                "value": getattr(field, "value", ""),
                "purpose": getattr(field, "purpose", ""),
            }
            item_dict["fields"].append(field_info)

    logger.info(f"Retrieved item '{title}' with {len(item_dict['fields'])} fields")
    return item_dict


async def list_available_items() -> List[str]:
    """
    List all available item titles across all vaults

    Returns:
        List of item titles
    """
    await _initialize_mappings()
    return list(_title_to_id_mapping.keys())


def get_secrets(connector: str) -> Dict[str, Any]:
    """
    Get secrets from 1Password with flexible field selection

    Args:
        connector: The connector name (used as default item name)
        fields: Specific fields to retrieve. If None, tries to get common fields

    Returns:
        Dict mapping field names to values
    """
    # Create an isolated event loop without affecting global state
    loop = asyncio.new_event_loop()
    try:
        # Don't set as global loop - just use it locally
        return loop.run_until_complete(get_secrets_by_title(connector))
    finally:
        loop.close()


async def get_secrets_by_title(title: str) -> Dict[str, Any]:
    """Async implementation of secret retrieval by title"""
    item_data = await get_item_by_title(title)

    if not item_data:
        logger.warning(f"No item found with title: {title}")
        return {}

    secrets_map = {}
    for field in item_data.get("fields", []):
        field_title = field.get("title", "")
        field_value = field.get("value", "")
        if field_title and field_value:
            secrets_map[field_title] = field_value

    logger.info(f'Loading secrets for {title}: {", ".join(secrets_map.keys())}')
    return secrets_map
