"""Unit tests for DSR-queue Celery ignore_result gating (execution.ignore_dsr_celery_task_results)."""

from types import SimpleNamespace
from unittest import mock

from fides.api.schemas.policy import ActionType
from fides.api.task.execute_request_tasks import queue_request_task, run_access_node
from fides.config import CONFIG
from fides.service.privacy_request.privacy_request_service import queue_privacy_request


def test_queue_privacy_request_omit_ignore_result_when_flag_off() -> None:
    original = CONFIG.execution.ignore_dsr_celery_task_results
    CONFIG.execution.ignore_dsr_celery_task_results = False
    try:
        with (
            mock.patch(
                "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
            ) as mock_apply,
            mock.patch(
                "fides.service.privacy_request.privacy_request_service.cache_task_tracking_key"
            ),
        ):
            mock_apply.return_value = SimpleNamespace(task_id="task-id-off")
            queue_privacy_request("pr-1", from_webhook_id=None, from_step=None)
            mock_apply.assert_called_once()
            _, call_kwargs = mock_apply.call_args
            assert "ignore_result" not in call_kwargs
    finally:
        CONFIG.execution.ignore_dsr_celery_task_results = original


def test_queue_privacy_request_passes_ignore_result_when_flag_on() -> None:
    original = CONFIG.execution.ignore_dsr_celery_task_results
    CONFIG.execution.ignore_dsr_celery_task_results = True
    try:
        with (
            mock.patch(
                "fides.api.service.privacy_request.request_runner_service.run_privacy_request.apply_async"
            ) as mock_apply,
            mock.patch(
                "fides.service.privacy_request.privacy_request_service.cache_task_tracking_key"
            ),
        ):
            mock_apply.return_value = SimpleNamespace(task_id="task-id-on")
            queue_privacy_request("pr-2", from_webhook_id=None, from_step=None)
            mock_apply.assert_called_once()
            _, call_kwargs = mock_apply.call_args
            assert call_kwargs.get("ignore_result") is True
    finally:
        CONFIG.execution.ignore_dsr_celery_task_results = original


def test_queue_request_task_omit_ignore_result_when_flag_off() -> None:
    original = CONFIG.execution.ignore_dsr_celery_task_results
    CONFIG.execution.ignore_dsr_celery_task_results = False
    try:
        request_task = SimpleNamespace(
            action_type=ActionType.access.value,
            privacy_request_id="pr-3",
            id="rt-1",
        )
        with (
            mock.patch.object(run_access_node, "apply_async") as mock_apply,
            mock.patch("fides.api.task.execute_request_tasks.cache_task_tracking_key"),
        ):
            mock_apply.return_value = SimpleNamespace(task_id="subtask-off")
            queue_request_task(request_task)  # type: ignore[arg-type]
            mock_apply.assert_called_once()
            _, call_kwargs = mock_apply.call_args
            assert "ignore_result" not in call_kwargs
    finally:
        CONFIG.execution.ignore_dsr_celery_task_results = original


def test_queue_request_task_passes_ignore_result_when_flag_on() -> None:
    original = CONFIG.execution.ignore_dsr_celery_task_results
    CONFIG.execution.ignore_dsr_celery_task_results = True
    try:
        request_task = SimpleNamespace(
            action_type=ActionType.access.value,
            privacy_request_id="pr-4",
            id="rt-2",
        )
        with (
            mock.patch.object(run_access_node, "apply_async") as mock_apply,
            mock.patch("fides.api.task.execute_request_tasks.cache_task_tracking_key"),
        ):
            mock_apply.return_value = SimpleNamespace(task_id="subtask-on")
            queue_request_task(request_task)  # type: ignore[arg-type]
            mock_apply.assert_called_once()
            _, call_kwargs = mock_apply.call_args
            assert call_kwargs.get("ignore_result") is True
    finally:
        CONFIG.execution.ignore_dsr_celery_task_results = original
