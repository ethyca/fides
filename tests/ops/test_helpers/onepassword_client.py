"""
Thin wrappers around :class:`fides.common.onepassword.OnePasswordClient`
for SaaS connector test secrets.

Preserves the existing module-level API so callers don't need to change.
"""

import os
from typing import Any, Dict, List, Optional

from loguru import logger

from fides.common.onepassword import OnePasswordClient

_client: Optional[OnePasswordClient] = None


def _get_client() -> Optional[OnePasswordClient]:
    """Lazily create a shared client for SaaS test secrets."""
    global _client
    if _client is not None:
        return _client

    token = os.getenv("SAAS_OP_SERVICE_ACCOUNT_TOKEN")
    vault_id = os.getenv("SAAS_SECRETS_OP_VAULT_ID")

    if not token:
        logger.error("Missing SAAS_OP_SERVICE_ACCOUNT_TOKEN.")
        return None
    if not vault_id:
        logger.error("Missing SAAS_SECRETS_OP_VAULT_ID.")
        return None

    _client = OnePasswordClient(
        service_account_token=token,
        vault_id=vault_id,
        integration_name="Fides Saas Secrets",
    )
    return _client


async def get_item_by_title(title: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a 1Password item by its title.

    Returns a dict with id, title, category, and fields, or None if not found.
    """
    client = _get_client()
    if client is None:
        return None
    return await client.get_item(title)


async def list_available_items() -> List[str]:
    """List all available item titles in the SaaS secrets vault."""
    client = _get_client()
    if client is None:
        return []
    return await client.list_items()


def get_secrets(connector: str) -> Dict[str, Any]:
    """
    Get secrets from 1Password by connector name (synchronous).

    Args:
        connector: The connector name (used as the 1PW item title)

    Returns:
        Dict mapping field names to values
    """
    client = _get_client()
    if client is None:
        return {}
    return client.get_secrets_sync(connector)


async def get_secrets_by_title(title: str) -> Dict[str, Any]:
    """Async implementation of secret retrieval by title."""
    client = _get_client()
    if client is None:
        return {}
    return await client.get_secrets(title)
