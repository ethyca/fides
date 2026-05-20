"""
System data-steward change hook — TEMPORARY EVENT-FRAMEWORK SHIM.

A single-purpose callback registry that lets fidesplus react when a user is
added/removed as a data steward (system manager) of a system. The only known
consumer today is fidesplus's monitor-stewardship-inheritance propagation.

This module exists ONLY because the event framework in fides PR #8096 is
not yet merged. When it lands:

  - Call sites of ``notify_system_stewards_changed`` (in the three v1
    system-manager routes) are replaced with
    ``publish_after_commit(session, SystemDataStewardsChanged(...))``.
  - Fidesplus's registered callback is replaced with a
    ``@subscribes_to(SystemDataStewardsChanged)`` handler.
  - This file is deleted.

DO NOT use this as a precedent for adding more cross-repo hooks. If you need
a similar shim before the framework lands, create a separate single-purpose
module — do not generalize this into a ``hooks`` package.
"""

from typing import Callable, List

from fastapi import BackgroundTasks
from loguru import logger

SystemStewardChangeHook = Callable[[BackgroundTasks, str], None]

_HOOKS: List[SystemStewardChangeHook] = []


def register_system_steward_change_hook(hook: SystemStewardChangeHook) -> None:
    """Register a callback invoked when a system's data stewards change.

    Idempotent: registering the same hook twice is a no-op.
    """
    if hook not in _HOOKS:
        _HOOKS.append(hook)


def notify_system_stewards_changed(
    background_tasks: BackgroundTasks, system_id: str
) -> None:
    """Invoke every registered hook with the given ``system_id``.

    Each hook is wrapped in try/except so one failure doesn't suppress the rest;
    failures are logged and swallowed. Hooks are responsible for scheduling
    their own background work via ``background_tasks``.
    """
    for hook in _HOOKS:
        try:
            hook(background_tasks, system_id)
        except Exception:
            logger.exception(
                "System-stewards-change hook {} raised for system_id={}",
                hook,
                system_id,
            )
