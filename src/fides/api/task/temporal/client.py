"""Temporal client singleton.

Provides a shared Temporal client instance, lazily connected on first use.
"""

from __future__ import annotations

from typing import Optional

from temporalio.client import Client

from fides.config import CONFIG

_client: Optional[Client] = None


async def get_temporal_client() -> Client:
    """Return a connected Temporal client, creating one if needed."""
    global _client
    if _client is None:
        _client = await Client.connect(
            CONFIG.temporal.server_url,
            namespace=CONFIG.temporal.namespace,
        )
    return _client
