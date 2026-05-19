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


def test_register_is_idempotent():
    hook = MagicMock()
    system_stewards.register_system_steward_change_hook(hook)
    system_stewards.register_system_steward_change_hook(hook)
    assert system_stewards._HOOKS == [hook]


def test_notify_isolates_hook_failures():
    """A raising hook must not prevent later hooks from firing."""
    raising = MagicMock(side_effect=RuntimeError("boom"))
    survivor = MagicMock()
    system_stewards.register_system_steward_change_hook(raising)
    system_stewards.register_system_steward_change_hook(survivor)

    bg = BackgroundTasks()
    system_stewards.notify_system_stewards_changed(bg, "sys-1")

    raising.assert_called_once_with(bg, "sys-1")
    survivor.assert_called_once_with(bg, "sys-1")
