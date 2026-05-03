"""Subscriber autodiscovery hook.

Subscriber modules must be imported in both webserver and worker processes
so that ``@subscribes_to`` decorators run and populate the registry. This
module maintains the list of subscriber module paths and provides an
``import_subscriber_modules()`` hook that triggers the imports.

Empty in v1: no production subscribers exist yet. Phase 2 + 3 add entries.
fidesplus calls ``register_subscriber_module`` at boot to register its own
subscriber modules alongside fides's.
"""

import importlib
from typing import List

from loguru import logger

# Fully-qualified module paths for subscriber modules.
event_subscriber_modules: List[str] = []


def register_subscriber_module(module_path: str) -> None:
    """Register a subscriber module to be imported at framework boot.

    Idempotent — registering the same module twice is a no-op.
    """
    if module_path not in event_subscriber_modules:
        event_subscriber_modules.append(module_path)


def import_subscriber_modules() -> None:
    """Import every registered subscriber module so its ``@subscribes_to``
    decorators run and populate the registry.

    Failure to import any single module logs an error but does not abort
    the boot — a misbehaving subscriber should not take down the entire
    process. Subscribers whose modules failed to import are simply absent
    from the registry; their event types will be treated as having no
    subscribers, and dispatch will be a no-op for those events.
    """
    for module_path in event_subscriber_modules:
        try:
            importlib.import_module(module_path)
        except Exception:
            logger.exception(
                "Failed to import event subscriber module: {}", module_path
            )
