"""
Instance-based 1Password client for retrieving secrets and items.

Provides lazy client initialization and vault item lookup by title.
Each instance is parameterized by its own service account token and vault ID,
so multiple consumers (e.g. SaaS test secrets, seed profile resolution)
can coexist with different credentials.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from loguru import logger
from onepassword.client import Client  # type: ignore[import-untyped]


class OnePasswordClient:
    """1Password SDK client with lazy initialization and title-based lookup."""

    def __init__(
        self,
        service_account_token: str,
        vault_id: str,
        integration_name: str = "Fides",
        integration_version: str = "v1.0.0",
    ):
        self._token = service_account_token
        self._vault_id = vault_id
        self._integration_name = integration_name
        self._integration_version = integration_version
        self._client: Optional[Client] = None
        self._title_to_id: Dict[str, Dict[str, str]] = {}
        self._mappings_initialized = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_client(self) -> Client:
        """Lazily authenticate and return the 1Password SDK client."""
        if self._client is None:
            self._client = await Client.authenticate(
                auth=self._token,
                integration_name=self._integration_name,
                integration_version=self._integration_version,
            )
        return self._client

    async def _ensure_mappings(self) -> None:
        """Build the title→ID index for items in the configured vault."""
        if self._mappings_initialized:
            return

        client = await self._get_client()
        items = await client.items.list(vault_id=self._vault_id)

        for item in items:
            logger.debug(f"1PW: indexed item '{item.title}'")
            self._title_to_id[item.title] = {
                "item_id": item.id,
                "category": item.category,
            }

        self._mappings_initialized = True
        logger.info(
            f"1PW: initialized mappings for {len(self._title_to_id)} items "
            f"in vault {self._vault_id}"
        )

    @staticmethod
    def _item_to_dict(item: Any) -> Dict[str, Any]:
        """Convert a 1Password SDK item object to a plain dict."""
        item_dict: Dict[str, Any] = {
            "id": item.id,
            "title": item.title,
            "category": item.category,
            "fields": [],
        }

        if hasattr(item, "fields") and item.fields:
            for field in item.fields:
                item_dict["fields"].append(
                    {
                        "id": getattr(field, "id", ""),
                        "title": getattr(field, "title", ""),
                        "type": getattr(field, "field_type", ""),
                        "value": getattr(field, "value", ""),
                        "purpose": getattr(field, "purpose", ""),
                    }
                )

        return item_dict

    # ------------------------------------------------------------------
    # Public API — async
    # ------------------------------------------------------------------

    async def get_item(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a 1Password item by its title.

        Returns a dict with keys: id, title, category, fields (list of
        dicts with id, title, type, value, purpose).  Returns None if
        the item is not found.
        """
        await self._ensure_mappings()

        if title not in self._title_to_id:
            logger.warning(f"1PW: item '{title}' not found in vault {self._vault_id}")
            return None

        info = self._title_to_id[title]
        client = await self._get_client()
        item = await client.items.get(
            item_id=info["item_id"],
            vault_id=self._vault_id,
        )

        item_dict = self._item_to_dict(item)
        logger.info(
            f"1PW: retrieved item '{title}' with {len(item_dict['fields'])} fields"
        )
        return item_dict

    async def get_secrets(self, title: str) -> Dict[str, str]:
        """
        Get field name → value pairs from a 1Password item.

        Filters out fields with empty titles or values.
        """
        item = await self.get_item(title)
        if not item:
            return {}

        return {
            field["title"]: field["value"]
            for field in item.get("fields", [])
            if field.get("title") and field.get("value")
        }

    async def get_item_notes(self, title: str) -> Optional[str]:
        """
        Get the notes (notesPlain) content from a 1Password item.

        Returns the string content of the NOTES field, or None if the
        item is not found or has no notes.
        """
        item = await self.get_item(title)
        if not item:
            return None

        for field in item.get("fields", []):
            if field.get("purpose") == "NOTES" or field.get("id") == "notesPlain":
                return field.get("value")

        return None

    async def get_item_notes_json(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Get the notes content from a 1Password item, parsed as JSON.

        Returns the parsed dict, or None if the item is not found,
        has no notes, or the notes are not valid JSON.
        """
        notes = await self.get_item_notes(title)
        if notes is None:
            return None

        try:
            return json.loads(notes)
        except json.JSONDecodeError:
            logger.error(f"1PW: notes for item '{title}' are not valid JSON")
            return None

    async def list_items(self) -> List[str]:
        """List all item titles in the configured vault."""
        await self._ensure_mappings()
        return list(self._title_to_id.keys())

    # ------------------------------------------------------------------
    # Public API — sync wrappers
    # ------------------------------------------------------------------

    def get_secrets_sync(self, title: str) -> Dict[str, str]:
        """Synchronous wrapper around :meth:`get_secrets`."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.get_secrets(title))
        finally:
            loop.close()

    def get_item_notes_json_sync(self, title: str) -> Optional[Dict[str, Any]]:
        """Synchronous wrapper around :meth:`get_item_notes_json`."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.get_item_notes_json(title))
        finally:
            loop.close()
