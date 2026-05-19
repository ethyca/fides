"""
System↔ConnectionConfig link change hook — TEMPORARY EVENT-FRAMEWORK SHIM.

Single-purpose callback registry that lets fidesplus react when the link
between a ``System`` and a ``ConnectionConfig`` (``system_integration_link``
row) is created or removed. Only known consumer today is fidesplus's
monitor-stewardship-inheritance propagation: a monitor inherits stewards from
the system its connection is linked to, so the inherited set must be
recomputed when that linkage changes.

Like ``system_steward_change_hooks``, this module exists ONLY because the
event framework in fides PR #8096 is not yet merged. When it lands:

  - Call sites of ``notify_system_connection_config_link_changed`` (in the
    ``SystemIntegrationLinkService`` mutators) are replaced with
    ``publish_after_commit(session, SystemConnectionConfigLinkChanged(...))``.
  - Fidesplus's registered callback is replaced with a
    ``@subscribes_to(SystemConnectionConfigLinkChanged)`` handler.
  - This file is deleted.

Caveat: FK ``ondelete='CASCADE'`` on both ``system_id`` and
``connection_config_id`` means deleting a ``System`` or ``ConnectionConfig``
silently removes its links at the DB level with no Python callback. Hooks
will not fire for cascade-driven deletions; consumers must rely on a
periodic reconciler as the convergence safety net for those.

DO NOT use this as a precedent for adding more cross-repo hooks. If you need
a similar shim before the framework lands, create a separate single-purpose
module — do not generalize this into a ``hooks`` package.
"""

from typing import Callable, List

from fastapi import BackgroundTasks
from loguru import logger

SystemConnectionConfigLinkChangeHook = Callable[[BackgroundTasks, str], None]

_HOOKS: List[SystemConnectionConfigLinkChangeHook] = []


def register_system_connection_config_link_change_hook(
    hook: SystemConnectionConfigLinkChangeHook,
) -> None:
    """Register a callback invoked when a system↔connection-config link changes.

    Idempotent: registering the same hook twice is a no-op.
    """
    if hook not in _HOOKS:
        _HOOKS.append(hook)


def notify_system_connection_config_link_changed(
    background_tasks: BackgroundTasks, connection_config_id: str
) -> None:
    """Invoke every registered hook with the given ``connection_config_id``.

    Each hook is wrapped in try/except so one failure doesn't suppress the rest;
    failures are logged and swallowed. Hooks are responsible for scheduling
    their own background work via ``background_tasks``.
    """
    for hook in _HOOKS:
        try:
            hook(background_tasks, connection_config_id)
        except Exception:
            logger.exception(
                "System-connection-config-link-change hook {} raised for "
                "connection_config_id={}",
                hook,
                connection_config_id,
            )
