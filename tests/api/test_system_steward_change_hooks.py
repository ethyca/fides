"""Tests for the system-stewards change hook registry."""

from unittest.mock import MagicMock

import pytest
from fastapi import BackgroundTasks

from fides.api import system_steward_change_hooks as system_stewards


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch):
    """Each test starts with an empty registry."""
    monkeypatch.setattr(system_stewards, "_HOOKS", [])
    yield


def test_register_appends_hook():
    hook = MagicMock()
    system_stewards.register_system_steward_change_hook(hook)
    assert system_stewards._HOOKS == [hook]


def test_register_is_idempotent():
    hook = MagicMock()
    system_stewards.register_system_steward_change_hook(hook)
    system_stewards.register_system_steward_change_hook(hook)
    assert system_stewards._HOOKS == [hook]


def test_notify_calls_each_registered_hook():
    hook_a = MagicMock()
    hook_b = MagicMock()
    system_stewards.register_system_steward_change_hook(hook_a)
    system_stewards.register_system_steward_change_hook(hook_b)

    bg = BackgroundTasks()
    system_stewards.notify_system_stewards_changed(bg, "sys-1")

    hook_a.assert_called_once_with(bg, "sys-1")
    hook_b.assert_called_once_with(bg, "sys-1")


def test_notify_isolates_hook_failures():
    """One hook raising must not prevent the rest from firing."""
    raising = MagicMock(side_effect=RuntimeError("boom"))
    survivor = MagicMock()
    system_stewards.register_system_steward_change_hook(raising)
    system_stewards.register_system_steward_change_hook(survivor)

    bg = BackgroundTasks()
    system_stewards.notify_system_stewards_changed(bg, "sys-2")

    raising.assert_called_once()
    survivor.assert_called_once_with(bg, "sys-2")


def test_notify_with_no_hooks_is_noop():
    bg = BackgroundTasks()
    # Should not raise even if registry empty
    system_stewards.notify_system_stewards_changed(bg, "sys-3")
