"""Tests for the system pre-delete hook registry."""

from unittest.mock import MagicMock

import pytest
from fastapi import BackgroundTasks

from fides.api import system_pre_delete_hooks as pre_delete


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch):
    """Each test starts with an empty registry."""
    monkeypatch.setattr(pre_delete, "_HOOKS", [])
    yield


def test_register_is_idempotent():
    hook = MagicMock()
    pre_delete.register_system_pre_delete_hook(hook)
    pre_delete.register_system_pre_delete_hook(hook)
    assert pre_delete._HOOKS == [hook]


def test_notify_dispatches_to_all_hooks():
    first = MagicMock()
    second = MagicMock()
    pre_delete.register_system_pre_delete_hook(first)
    pre_delete.register_system_pre_delete_hook(second)

    bg = BackgroundTasks()
    pre_delete.notify_system_about_to_be_deleted(bg, "sys-1")

    first.assert_called_once_with(bg, "sys-1")
    second.assert_called_once_with(bg, "sys-1")


def test_notify_isolates_hook_failures():
    """A raising hook must not prevent later hooks from firing."""
    raising = MagicMock(side_effect=RuntimeError("boom"))
    survivor = MagicMock()
    pre_delete.register_system_pre_delete_hook(raising)
    pre_delete.register_system_pre_delete_hook(survivor)

    bg = BackgroundTasks()
    pre_delete.notify_system_about_to_be_deleted(bg, "sys-1")

    raising.assert_called_once_with(bg, "sys-1")
    survivor.assert_called_once_with(bg, "sys-1")


def test_notify_empty_registry_is_noop():
    """No hooks registered → no error, no side effects."""
    bg = BackgroundTasks()
    pre_delete.notify_system_about_to_be_deleted(bg, "sys-1")
