"""Tests for the system↔connection-config link change hook registry."""

from unittest.mock import MagicMock

import pytest
from fastapi import BackgroundTasks

from fides.api import system_connection_config_link_change_hooks as link_hooks


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch):
    """Each test starts with an empty registry."""
    monkeypatch.setattr(link_hooks, "_HOOKS", [])
    yield


def test_register_appends_hook():
    hook = MagicMock()
    link_hooks.register_system_connection_config_link_change_hook(hook)
    assert link_hooks._HOOKS == [hook]


def test_register_is_idempotent():
    hook = MagicMock()
    link_hooks.register_system_connection_config_link_change_hook(hook)
    link_hooks.register_system_connection_config_link_change_hook(hook)
    assert link_hooks._HOOKS == [hook]


def test_notify_calls_each_registered_hook():
    hook_a = MagicMock()
    hook_b = MagicMock()
    link_hooks.register_system_connection_config_link_change_hook(hook_a)
    link_hooks.register_system_connection_config_link_change_hook(hook_b)

    bg = BackgroundTasks()
    link_hooks.notify_system_connection_config_link_changed(bg, "cc-1")

    hook_a.assert_called_once_with(bg, "cc-1")
    hook_b.assert_called_once_with(bg, "cc-1")


def test_notify_isolates_hook_failures():
    """One hook raising must not prevent the rest from firing."""
    raising = MagicMock(side_effect=RuntimeError("boom"))
    survivor = MagicMock()
    link_hooks.register_system_connection_config_link_change_hook(raising)
    link_hooks.register_system_connection_config_link_change_hook(survivor)

    bg = BackgroundTasks()
    link_hooks.notify_system_connection_config_link_changed(bg, "cc-2")

    raising.assert_called_once()
    survivor.assert_called_once_with(bg, "cc-2")


def test_notify_with_no_hooks_is_noop():
    bg = BackgroundTasks()
    link_hooks.notify_system_connection_config_link_changed(bg, "cc-3")
