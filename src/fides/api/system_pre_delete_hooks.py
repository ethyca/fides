"""
System pre-delete hook — TEMPORARY EVENT-FRAMEWORK SHIM.

Fires synchronously immediately BEFORE a ``System`` is deleted, while the
system row and its dependent rows (``system_manager``,
``system_connection_config_link``, ``monitorsteward.source_system_id`` refs)
still exist. Registered callbacks may snapshot whatever state they need
before FK cascade wipes the joins they depend on.

Distinct from ``system_steward_change_hooks``: that fires on add/remove
against the ``system_manager`` join, where the BG-task model works because
the post-commit state is still queryable. Deletion is different — by the
time a BG task would run, FK cascades have erased the rows consumers need.
Hooks here therefore execute their snapshot synchronously and defer only
follow-up work via ``background_tasks``.

Like the adjacent change-hook shims, this module exists ONLY because the
event framework is not yet merged. When it lands:

  - Call sites of ``notify_system_about_to_be_deleted`` (in the two v1
    system-delete routes) are replaced with
    ``publish_before_commit(session, SystemDeleted(...))``.
  - Fidesplus's registered callback is replaced with a
    ``@subscribes_to(SystemDeleted)`` handler (with the snapshot moved
    into a pre-commit listener).
  - This file is deleted.

DO NOT use this as a precedent for adding more cross-repo hooks. If you need
a similar shim before the framework lands, create a separate single-purpose
module — do not generalize this into a ``hooks`` package.
"""

from typing import Callable, List

from fastapi import BackgroundTasks
from loguru import logger

SystemPreDeleteHook = Callable[[BackgroundTasks, str], None]

_HOOKS: List[SystemPreDeleteHook] = []


def register_system_pre_delete_hook(hook: SystemPreDeleteHook) -> None:
    """Register a callback invoked synchronously before a system is deleted.

    Idempotent: registering the same hook twice is a no-op.
    """
    if hook not in _HOOKS:
        _HOOKS.append(hook)


def notify_system_about_to_be_deleted(
    background_tasks: BackgroundTasks, system_id: str
) -> None:
    """Invoke every registered hook BEFORE the system row is deleted.

    Each hook runs synchronously in the request thread and must complete
    its snapshot quickly; heavy work should be deferred via
    ``background_tasks``. Failures are logged and swallowed — a misbehaving
    consumer must not block the delete.
    """
    for hook in _HOOKS:
        try:
            hook(background_tasks, system_id)
        except Exception:
            logger.exception(
                "System pre-delete hook {} raised for system_id={}",
                hook,
                system_id,
            )
